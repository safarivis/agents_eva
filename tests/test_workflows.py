"""Tests for workflow modules."""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.workflows.heartbeat import run_heartbeat, check_urgent_emails, check_upcoming_meetings
from src.workflows.morning_brief import run_morning_brief, generate_brief
from src.workflows.weekly_review import run_weekly_review


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


class TestGenerateBrief:
    """Tests for generate_brief function."""

    def test_generates_formatted_brief(self):
        """generate_brief returns formatted markdown."""
        emails = [{"subject": "Test email", "from": "test@example.com"}]
        events = [{"summary": "Meeting", "start": {"dateTime": "2026-02-19T10:00:00Z"}}]
        context = "Previous context entries"

        result = generate_brief(emails, events, context)

        assert "Good morning" in result
        assert "Test email" in result
        assert "Meeting" in result


class TestRunMorningBrief:
    """Tests for run_morning_brief function."""

    def test_sends_brief_via_whatsapp(self, tmp_path: Path):
        """run_morning_brief sends formatted brief."""
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        (memory_dir / "context.md").write_text("# Context\n")

        with patch("src.workflows.morning_brief.fetch_emails") as mock_emails, \
             patch("src.workflows.morning_brief.fetch_calendar_events") as mock_events, \
             patch("src.workflows.morning_brief.send_whatsapp") as mock_wa, \
             patch("src.workflows.morning_brief.sync_memory"), \
             patch("src.workflows.morning_brief.push_memory"), \
             patch("src.workflows.morning_brief.load_memory_file") as mock_load:

            mock_emails.return_value = [{"subject": "Test", "from": "test@example.com"}]
            mock_events.return_value = [{"summary": "Standup", "start": {"dateTime": "2026-02-19T09:00:00Z"}}]
            mock_load.return_value = "# Context\nPrevious entries"

            run_morning_brief(tmp_path, "+27123456789")

            mock_wa.assert_called_once()
            message = mock_wa.call_args[0][1]
            assert "Good morning" in message


class TestRunWeeklyReview:
    """Tests for run_weekly_review function."""

    def test_sends_weekly_summary(self, tmp_path: Path):
        """run_weekly_review sends weekly digest."""
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        (memory_dir / "context.md").write_text("# Context\n## 2026-02-15\nEntry 1\n## 2026-02-16\nEntry 2")

        with patch("src.workflows.weekly_review.fetch_calendar_events") as mock_events, \
             patch("src.workflows.weekly_review.send_whatsapp") as mock_wa, \
             patch("src.workflows.weekly_review.sync_memory"), \
             patch("src.workflows.weekly_review.push_memory"), \
             patch("src.workflows.weekly_review.load_memory_file") as mock_load:

            mock_events.return_value = []
            mock_load.return_value = "# Context\nEntry from this week"

            run_weekly_review(tmp_path, "+27123456789")

            mock_wa.assert_called_once()
            message = mock_wa.call_args[0][1]
            assert "Week" in message
