"""Flask gateway for WhatsApp webhooks."""
import hashlib
import hmac
import os
from pathlib import Path

from flask import Flask, request, jsonify

from .agent import run_agent
from .composio_tools import send_whatsapp
from .workflows.base import sync_memory, push_memory
from .memory import update_context

app = Flask(__name__)

# Configuration from environment
REPO_DIR = Path(os.environ.get("EVA_REPO_DIR", "/opt/eva"))
MEMORY_DIR = REPO_DIR / "memory"


def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify Meta webhook signature.

    Args:
        payload: Raw request body
        signature: X-Hub-Signature-256 header value
        secret: App secret for verification

    Returns:
        True if signature is valid
    """
    if not signature.startswith("sha256="):
        return False

    expected = "sha256=" + hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected)


@app.route("/webhook", methods=["GET"])
def webhook_verify():
    """Handle Meta webhook verification challenge."""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    verify_token = os.environ.get("META_VERIFY_TOKEN")

    if mode == "subscribe" and token == verify_token:
        return challenge, 200

    return "Forbidden", 403


@app.route("/webhook", methods=["POST"])
def webhook_receive():
    """Handle incoming WhatsApp messages."""
    # Verify signature
    signature = request.headers.get("X-Hub-Signature-256", "")
    secret = os.environ.get("META_APP_SECRET", "")

    if not verify_signature(request.data, signature, secret):
        return "Invalid signature", 403

    # Parse message
    data = request.json
    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]
        message = value["messages"][0]
        sender = message["from"]
        text = message["text"]["body"]
    except (KeyError, IndexError):
        return jsonify({"status": "no message"}), 200

    # Check if sender is allowed
    allowed_phone = os.environ.get("ALLOWED_PHONE", "")
    if sender != allowed_phone:
        return jsonify({"status": "unauthorized"}), 200

    # Sync memory from git
    try:
        sync_memory(REPO_DIR)
    except Exception as e:
        app.logger.error(f"Failed to sync memory: {e}")

    # Run Eva agent
    try:
        response = run_agent(text, MEMORY_DIR)
    except Exception as e:
        app.logger.error(f"Agent error: {e}")
        response = f"Sorry, I encountered an error: {str(e)[:100]}"

    # Send response via WhatsApp
    send_whatsapp(sender, response)

    # Log to context and push
    try:
        update_context(
            MEMORY_DIR,
            category="WhatsApp",
            summary=f"Replied to: {text[:50]}",
            details=f"Response: {response[:200]}",
        )
        push_memory(REPO_DIR, "eva: whatsapp reply")
    except Exception as e:
        app.logger.error(f"Failed to push memory: {e}")

    return jsonify({"status": "ok"}), 200


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "service": "eva-gateway"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=18790, debug=False)
