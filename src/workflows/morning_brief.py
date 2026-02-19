"""Morning brief workflow - daily summary at 7am."""
from datetime import datetime
from pathlib import Path

from ..composio_tools import fetch_emails, fetch_calendar_events, send_whatsapp
from ..memory import load_memory_file, update_context
from .base import sync_memory, push_memory


def generate_brief(
    emails: list[dict],
    events: list[dict],
    context: str,
) -> str:
    """Generate formatted morning brief.

    Args:
        emails: Unread emails
        events: Today's calendar events
        context: Recent context entries

    Returns:
        Formatted brief message
    """
    today = datetime.now().strftime("%A, %B %d")

    lines = [
        f"☀️ Good morning, Louis!",
        f"📅 {today}",
        "",
    ]

    # Calendar section
    if events:
        lines.append(f"**Today's Schedule** ({len(events)} events):")
        for event in events[:5]:
            time_str = event.get("start", {}).get("dateTime", "")
            if time_str:
                time = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
                time_fmt = time.strftime("%H:%M")
            else:
                time_fmt = "All day"
            lines.append(f"  • {time_fmt} - {event.get('summary', 'No title')[:40]}")
    else:
        lines.append("**Today's Schedule:** Clear day! 🎉")

    lines.append("")

    # Email section
    if emails:
        lines.append(f"**Inbox** ({len(emails)} unread):")
        for email in emails[:5]:
            sender = email.get("from", "Unknown")[:20]
            subject = email.get("subject", "No subject")[:35]
            lines.append(f"  • {sender}: {subject}")
    else:
        lines.append("**Inbox:** All caught up! ✅")

    lines.append("")

    # Context/followups section (parse recent commitments)
    if "Commitment" in context or "Follow-up" in context:
        lines.append("**Open Items:** Check context.md for pending follow-ups")
    else:
        lines.append("**Open Items:** None tracked")

    lines.append("")
    lines.append("— Eva")

    return "\n".join(lines)


def run_morning_brief(repo_dir: Path, phone_number: str) -> None:
    """Run morning brief workflow.

    Args:
        repo_dir: Path to Eva repository
        phone_number: WhatsApp number to send brief to
    """
    memory_dir = repo_dir / "memory"

    # Sync memory
    sync_memory(repo_dir)

    # Fetch today's data
    emails = fetch_emails(max_results=20, query="is:unread")
    events = fetch_calendar_events(hours_ahead=16)  # Full day ahead
    context = load_memory_file(memory_dir, "context")

    # Generate and send brief
    brief = generate_brief(emails, events, context)
    send_whatsapp(phone_number, brief)

    # Log to context
    update_context(
        memory_dir,
        category="MorningBrief",
        summary=f"Sent daily brief: {len(events)} events, {len(emails)} emails",
        details=f"Brief sent at {datetime.now().strftime('%H:%M')}",
    )
    push_memory(repo_dir, "eva: morning brief sent")
