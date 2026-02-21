"""Composio tools wrapper for Eva."""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from composio import ComposioToolSet, Action


def _get_toolset() -> ComposioToolSet:
    """Get configured Composio toolset."""
    return ComposioToolSet(api_key=os.environ.get("COMPOSIO_API_KEY"))


def fetch_emails(
    max_results: int = 10,
    query: str = "is:unread",
) -> list[dict]:
    """Fetch emails from Gmail via Composio.

    Args:
        max_results: Maximum number of emails to fetch
        query: Gmail search query

    Returns:
        List of email dicts with id, subject, from, snippet
    """
    toolset = _get_toolset()
    result = toolset.execute_action(
        action=Action.GMAIL_FETCH_EMAILS,
        params={
            "max_results": max_results,
            "q": query,
            "user_id": "me",
        },
    )
    messages = result.get("data", {}).get("messages", [])
    return messages


def fetch_calendar_events(
    hours_ahead: int = 24,
) -> list[dict]:
    """Fetch upcoming calendar events via Composio.

    Args:
        hours_ahead: How many hours ahead to look

    Returns:
        List of event dicts with id, summary, start, end
    """
    toolset = _get_toolset()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    time_max = now + timedelta(hours=hours_ahead)

    result = toolset.execute_action(
        action=Action.GOOGLECALENDAR_FIND_EVENT,
        params={
            "time_min": now.isoformat() + "Z",
            "time_max": time_max.isoformat() + "Z",
            "max_results": 10,
        },
    )
    events = result.get("data", {}).get("items", [])
    return events


def send_email(
    to_email: str,
    subject: str,
    body: str,
) -> bool:
    """Send email via Gmail/Composio.

    Args:
        to_email: Recipient email address
        subject: Email subject line
        body: Email body text

    Returns:
        True if sent successfully
    """
    toolset = _get_toolset()
    result = toolset.execute_action(
        action=Action.GMAIL_SEND_EMAIL,
        params={
            "recipient_email": to_email,
            "subject": subject,
            "body": body,
            "user_id": "me",
        },
    )
    return bool(result.get("data", {}).get("id"))
