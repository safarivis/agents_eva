"""Weekly review workflow - Sunday evening recap."""
from datetime import datetime
from pathlib import Path

from ..composio_tools import fetch_calendar_events, send_whatsapp
from ..memory import load_memory_file, update_context
from .base import sync_memory, push_memory


def run_weekly_review(repo_dir: Path, phone_number: str) -> None:
    """Run weekly review workflow.

    Args:
        repo_dir: Path to Eva repository
        phone_number: WhatsApp number to send review to
    """
    memory_dir = repo_dir / "memory"

    # Sync memory
    sync_memory(repo_dir)

    # Load context for analysis
    context = load_memory_file(memory_dir, "context")

    # Get next week's events
    next_week_events = fetch_calendar_events(hours_ahead=168)  # 7 days

    # Build weekly summary
    lines = [
        "📊 **Weekly Review**",
        f"Week ending {datetime.now().strftime('%B %d, %Y')}",
        "",
        "**This Week's Activity:**",
    ]

    # Count context entries (rough analysis)
    entry_count = context.count("## 202")
    lines.append(f"  • {entry_count} context entries logged")

    # Check for commitments/follow-ups
    commitments = context.count("Commitment")
    followups = context.count("Follow-up")
    if commitments or followups:
        lines.append(f"  • {commitments} commitments, {followups} follow-ups tracked")

    lines.append("")
    lines.append("**Next Week Preview:**")

    if next_week_events:
        lines.append(f"  • {len(next_week_events)} events scheduled")
        # Group by day (simplified)
        lines.append("  • Check calendar for details")
    else:
        lines.append("  • Calendar is clear")

    lines.append("")
    lines.append("Take time to reflect. What went well? What could improve?")
    lines.append("")
    lines.append("— Eva")

    message = "\n".join(lines)
    send_whatsapp(phone_number, message)

    # Log to context
    update_context(
        memory_dir,
        category="WeeklyReview",
        summary="Sent weekly review digest",
        details=f"Review sent at {datetime.now().strftime('%H:%M')}",
    )
    push_memory(repo_dir, "eva: weekly review sent")
