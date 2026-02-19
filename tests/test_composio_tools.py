"""Tests for Composio tools wrapper."""
import pytest
from unittest.mock import MagicMock, patch

from src.composio_tools import (
    fetch_emails,
    fetch_calendar_events,
    send_whatsapp,
)


class TestFetchEmails:
    """Tests for fetch_emails function."""

    def test_returns_list_of_emails(self):
        """fetch_emails returns list of email dicts."""
        with patch("src.composio_tools.ComposioToolSet") as mock_toolset:
            mock_instance = MagicMock()
            mock_toolset.return_value = mock_instance
            mock_instance.execute_action.return_value = {
                "data": {
                    "messages": [
                        {"id": "1", "subject": "Test", "from": "test@example.com"}
                    ]
                }
            }

            result = fetch_emails(max_results=5)

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["subject"] == "Test"


class TestFetchCalendarEvents:
    """Tests for fetch_calendar_events function."""

    def test_returns_list_of_events(self):
        """fetch_calendar_events returns list of event dicts."""
        with patch("src.composio_tools.ComposioToolSet") as mock_toolset:
            mock_instance = MagicMock()
            mock_toolset.return_value = mock_instance
            mock_instance.execute_action.return_value = {
                "data": {
                    "items": [
                        {"id": "1", "summary": "Meeting", "start": {"dateTime": "2026-02-19T10:00:00Z"}}
                    ]
                }
            }

            result = fetch_calendar_events(hours_ahead=2)

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["summary"] == "Meeting"


class TestSendWhatsapp:
    """Tests for send_whatsapp function."""

    def test_sends_message_successfully(self):
        """send_whatsapp returns success status."""
        with patch("src.composio_tools.ComposioToolSet") as mock_toolset:
            mock_instance = MagicMock()
            mock_toolset.return_value = mock_instance
            mock_instance.execute_action.return_value = {"data": {"success": True}}

            result = send_whatsapp("+27123456789", "Hello!")

            assert result is True
            mock_instance.execute_action.assert_called_once()
