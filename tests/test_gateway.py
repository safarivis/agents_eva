"""Tests for Flask gateway."""
import pytest
import hashlib
import hmac
import json
from unittest.mock import patch, MagicMock

from src.gateway import app, verify_signature


class TestVerifySignature:
    """Tests for webhook signature verification."""

    def test_valid_signature_returns_true(self):
        """verify_signature returns True for valid signature."""
        payload = b'{"test": "data"}'
        secret = "test_secret"
        signature = "sha256=" + hmac.new(
            secret.encode(), payload, hashlib.sha256
        ).hexdigest()

        result = verify_signature(payload, signature, secret)

        assert result is True

    def test_invalid_signature_returns_false(self):
        """verify_signature returns False for invalid signature."""
        payload = b'{"test": "data"}'
        signature = "sha256=invalid"
        secret = "test_secret"

        result = verify_signature(payload, signature, secret)

        assert result is False


class TestWebhookEndpoint:
    """Tests for /webhook endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        app.config["TESTING"] = True
        with app.test_client() as client:
            yield client

    def test_get_verification_challenge(self, client):
        """GET /webhook returns challenge for Meta verification."""
        with patch.dict("os.environ", {"META_VERIFY_TOKEN": "test_token"}):
            response = client.get(
                "/webhook?hub.mode=subscribe&hub.verify_token=test_token&hub.challenge=abc123"
            )

        assert response.status_code == 200
        assert response.data == b"abc123"

    def test_post_returns_received(self, client):
        """POST /webhook acknowledges receipt."""
        payload = {"test": "data"}

        with patch.dict("os.environ", {"META_APP_SECRET": ""}):
            response = client.post(
                "/webhook",
                json=payload,
                content_type="application/json",
            )

        assert response.status_code == 200
        assert b"received" in response.data


class TestTriggerEndpoint:
    """Tests for /trigger endpoint."""

    @pytest.fixture
    def client(self):
        app.config["TESTING"] = True
        with app.test_client() as client:
            yield client

    def test_trigger_heartbeat(self, client, tmp_path):
        """POST /trigger with heartbeat workflow."""
        # Create memory directory for heartbeat
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        (memory_dir / "context.md").write_text("# Context\n")

        with patch("src.gateway.sync_memory"), \
             patch("src.gateway.REPO_DIR", tmp_path), \
             patch("src.gateway.MEMORY_DIR", memory_dir), \
             patch("src.workflows.heartbeat.fetch_emails") as mock_emails, \
             patch("src.workflows.heartbeat.fetch_calendar_events") as mock_events, \
             patch("src.workflows.heartbeat.send_email") as mock_email, \
             patch("src.workflows.heartbeat.sync_memory"), \
             patch("src.workflows.heartbeat.push_memory"), \
             patch.dict("os.environ", {"USER_EMAIL": "test@example.com"}):

            mock_emails.return_value = [{"subject": "URGENT: Test", "from": "test@example.com"}]
            mock_events.return_value = []

            response = client.post("/trigger", json={"workflow": "heartbeat"})

        assert response.status_code == 200
        assert b"heartbeat" in response.data


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    @pytest.fixture
    def client(self):
        app.config["TESTING"] = True
        with app.test_client() as client:
            yield client

    def test_health_returns_ok(self, client):
        """GET /health returns 200 OK."""
        response = client.get("/health")

        assert response.status_code == 200
        assert b"ok" in response.data.lower()
