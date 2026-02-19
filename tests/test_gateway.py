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

    def test_post_processes_message(self, client):
        """POST /webhook processes incoming message."""
        payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "27123456789",
                            "text": {"body": "Hello Eva"}
                        }]
                    }
                }]
            }]
        }

        with patch.dict("os.environ", {
            "META_APP_SECRET": "secret",
            "ALLOWED_PHONE": "27123456789",
        }), patch("src.gateway.run_agent") as mock_agent, \
           patch("src.gateway.send_whatsapp") as mock_wa, \
           patch("src.gateway.sync_memory"), \
           patch("src.gateway.push_memory"), \
           patch("src.gateway.update_context"):

            mock_agent.return_value = "Hello!"

            # Generate valid signature
            body = json.dumps(payload).encode()
            sig = "sha256=" + hmac.new(b"secret", body, hashlib.sha256).hexdigest()

            response = client.post(
                "/webhook",
                data=body,
                content_type="application/json",
                headers={"X-Hub-Signature-256": sig}
            )

        assert response.status_code == 200
        mock_agent.assert_called_once()
        mock_wa.assert_called_once()


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
