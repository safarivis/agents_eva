"""Flask gateway for Eva webhooks and health checks."""
import hashlib
import hmac
import os
from pathlib import Path

from flask import Flask, request, jsonify

from .agent import run_agent
from .composio_tools import send_email
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
    """Handle incoming webhook requests (reserved for future use)."""
    # Verify signature if secret is configured
    signature = request.headers.get("X-Hub-Signature-256", "")
    secret = os.environ.get("META_APP_SECRET", "")

    if secret and signature and not verify_signature(request.data, signature, secret):
        return "Invalid signature", 403

    # Parse generic webhook payload
    data = request.json
    if not data:
        return jsonify({"status": "no data"}), 200

    # Future: handle different webhook types here
    # For now, just acknowledge receipt
    return jsonify({"status": "received"}), 200


@app.route("/trigger", methods=["POST"])
def trigger_workflow():
    """Manually trigger Eva workflows via HTTP.

    POST /trigger with JSON body: {"workflow": "heartbeat|morning_brief|weekly_review"}
    """
    data = request.json or {}
    workflow = data.get("workflow", "")
    user_email = os.environ.get("USER_EMAIL", "louisrdup@gmail.com")

    # Sync memory
    try:
        sync_memory(REPO_DIR)
    except Exception as e:
        app.logger.error(f"Failed to sync memory: {e}")

    if workflow == "heartbeat":
        from .workflows.heartbeat import run_heartbeat
        run_heartbeat(REPO_DIR, user_email)
        return jsonify({"status": "ok", "workflow": "heartbeat"}), 200
    elif workflow == "morning_brief":
        from .workflows.morning_brief import run_morning_brief
        run_morning_brief(REPO_DIR, user_email)
        return jsonify({"status": "ok", "workflow": "morning_brief"}), 200
    elif workflow == "weekly_review":
        from .workflows.weekly_review import run_weekly_review
        run_weekly_review(REPO_DIR, user_email)
        return jsonify({"status": "ok", "workflow": "weekly_review"}), 200
    else:
        return jsonify({"error": "Unknown workflow", "valid": ["heartbeat", "morning_brief", "weekly_review"]}), 400


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "service": "eva-gateway"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=18790, debug=False)
