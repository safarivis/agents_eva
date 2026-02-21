"""Heartbeat workflow - checks for urgent items every 30 minutes."""
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ..composio_tools import fetch_emails, fetch_calendar_events, send_email
from ..memory import update_context
from .base import sync_memory, push_memory


# Keywords that indicate urgency
URGENT_KEYWORDS = ["urgent", "asap", "emergency", "critical", "action required", "immediately"]

# VIP senders (always alert)
VIP_SENDERS = ["louis", "lewkai"]


def check_urgent_emails(emails: list[dict]) -> list[dict]:
    """Filter emails for urgent ones.

    Args:
        emails: List of email dicts

    Returns:
        List of urgent emails
    """
    urgent = []
    for email in emails:
        subject = email.get("subject", "").lower()
        sender = email.get("from", "").lower()

        # Check for urgent keywords
        is_urgent = any(kw in subject for kw in URGENT_KEYWORDS)

        # Check for VIP senders
        is_vip = any(vip in sender for vip in VIP_SENDERS)

        if is_urgent or is_vip:
            urgent.append(email)

    return urgent


def check_upcoming_meetings(events: list[dict], hours: int = 2) -> list[dict]:
    """Filter calendar events for upcoming ones.

    Args:
        events: List of calendar event dicts
        hours: Look ahead window in hours

    Returns:
        List of events within window
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    cutoff = now + timedelta(hours=hours)
    upcoming = []

    for event in events:
        start_str = event.get("start", {}).get("dateTime", "")
        if not start_str:
            continue

        # Parse ISO format
        start = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
        start_naive = start.replace(tzinfo=None)

        if now <= start_naive <= cutoff:
            upcoming.append(event)

    return upcoming


def run_heartbeat(repo_dir: Path, user_email: str) -> None:
    """Run heartbeat check.

    Args:
        repo_dir: Path to Eva repository
        user_email: Email address to send alerts to
    """
    memory_dir = repo_dir / "memory"

    # Sync memory from git
    sync_memory(repo_dir)

    # Fetch data
    emails = fetch_emails(max_results=20, query="is:unread")
    events = fetch_calendar_events(hours_ahead=2)

    # Check for urgent items
    urgent_emails = check_urgent_emails(emails)
    upcoming_meetings = check_upcoming_meetings(events, hours=2)

    # Build alert message if needed
    alerts = []
    if urgent_emails:
        alerts.append(f"📧 {len(urgent_emails)} urgent email(s):")
        for email in urgent_emails[:3]:  # Top 3
            alerts.append(f"  • {email.get('subject', 'No subject')[:50]}")

    if upcoming_meetings:
        alerts.append(f"📅 {len(upcoming_meetings)} meeting(s) in next 2 hours:")
        for event in upcoming_meetings[:3]:
            alerts.append(f"  • {event.get('summary', 'No title')[:50]}")

    # Send alert if anything urgent
    if alerts:
        body = "\n".join(alerts)
        send_email(user_email, "⚡ Eva Heartbeat Alert", body)

        # Log to context
        update_context(
            memory_dir,
            category="Heartbeat",
            summary=f"Sent alert: {len(urgent_emails)} emails, {len(upcoming_meetings)} meetings",
            details=body,
        )
        push_memory(repo_dir, "eva: heartbeat alert sent")
