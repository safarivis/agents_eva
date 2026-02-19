"""Tests for workflow modules."""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.workflows.heartbeat import run_heartbeat, check_urgent_emails, check_upcoming_meetings


class TestCheckUrgentEmails:
    """Tests for check_urgent_emails function."""

    def test_returns_urgent_emails(self):
        """check_urgent_emails filters for urgent emails."""
        emails = [
            {"subject": "URGENT: Server down", "from": "alerts@company.com"},
            {"subject": "Newsletter", "from": "news@spam.com"},
            {"subject": "Action required: Invoice", "from": "finance@company.com"},
        ]

        result = check_urgent_emails(emails)

        assert len(result) == 2
        assert any("URGENT" in e["subject"] for e in result)


class TestCheckUpcomingMeetings:
    """Tests for check_upcoming_meetings function."""

    def test_returns_meetings_within_window(self):
        """check_upcoming_meetings returns meetings in next 2 hours."""
        from datetime import datetime, timedelta, timezone

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        events = [
            {"summary": "Team standup", "start": {"dateTime": (now + timedelta(hours=1)).isoformat() + "Z"}},
            {"summary": "Tomorrow meeting", "start": {"dateTime": (now + timedelta(hours=25)).isoformat() + "Z"}},
        ]

        result = check_upcoming_meetings(events, hours=2)

        assert len(result) == 1
        assert result[0]["summary"] == "Team standup"


class TestRunHeartbeat:
    """Tests for run_heartbeat function."""

    def test_sends_alert_when_urgent_items(self, tmp_path: Path):
        """run_heartbeat sends WhatsApp when urgent items found."""
        # Setup memory
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        (memory_dir / "context.md").write_text("# Context\n")

        with patch("src.workflows.heartbeat.fetch_emails") as mock_emails, \
             patch("src.workflows.heartbeat.fetch_calendar_events") as mock_events, \
             patch("src.workflows.heartbeat.send_whatsapp") as mock_wa, \
             patch("src.workflows.heartbeat.sync_memory"), \
             patch("src.workflows.heartbeat.push_memory"):

            mock_emails.return_value = [{"subject": "URGENT: Check this", "from": "boss@company.com"}]
            mock_events.return_value = []

            run_heartbeat(tmp_path, "+27123456789")

            mock_wa.assert_called_once()
            assert "URGENT" in mock_wa.call_args[0][1]
