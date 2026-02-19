# Eva Phase 3: Hybrid Workflows + VPS Gateway Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement proactive workflows (heartbeat, morning brief, weekly review) on GitHub Actions and interactive WhatsApp gateway on VPS.

**Architecture:** Hybrid approach - scheduled tasks run on GitHub Actions with full logging, interactive WhatsApp messages run on VPS for fast response. Both use Composio for external integrations (Gmail, Calendar, WhatsApp).

**Tech Stack:** Python 3.11+, Flask, GitHub Actions, Composio SDK, Nginx, systemd

---

## Task 1: Add Composio SDK dependency

**Files:**
- Modify: `requirements.txt`
- Modify: `pyproject.toml`

**Step 1: Update requirements.txt**

Add to `requirements.txt`:
```
composio-core>=0.5.0
flask>=3.0.0
gunicorn>=21.0.0
```

**Step 2: Update pyproject.toml**

Update dependencies in `pyproject.toml`:
```toml
dependencies = [
    "anthropic>=0.40.0",
    "openai>=1.0.0",
    "tiktoken>=0.5.0",
    "python-frontmatter>=1.0.0",
    "composio-core>=0.5.0",
    "flask>=3.0.0",
    "gunicorn>=21.0.0",
]
```

**Step 3: Install dependencies**

Run: `pip install -e ".[dev]"`
Expected: Successfully installed composio-core, flask, gunicorn

**Step 4: Commit**

```bash
git add requirements.txt pyproject.toml
git commit -m "chore: add Composio, Flask, gunicorn dependencies"
```

---

## Task 2: Create Composio tools wrapper

**Files:**
- Create: `src/composio_tools.py`
- Create: `tests/test_composio_tools.py`

**Step 1: Write failing tests**

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_composio_tools.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.composio_tools'"

**Step 3: Commit failing tests**

```bash
git add tests/test_composio_tools.py
git commit -m "test: add failing tests for Composio tools wrapper"
```

---

## Task 3: Implement Composio tools wrapper

**Files:**
- Create: `src/composio_tools.py`

**Step 1: Write implementation**

```python
"""Composio tools wrapper for Eva."""
import os
from datetime import datetime, timedelta
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
    now = datetime.utcnow()
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


def send_whatsapp(
    phone_number: str,
    message: str,
) -> bool:
    """Send WhatsApp message via Composio.

    Args:
        phone_number: Recipient phone number (with country code)
        message: Message text to send

    Returns:
        True if sent successfully
    """
    toolset = _get_toolset()
    result = toolset.execute_action(
        action=Action.WHATSAPP_SEND_MESSAGE,
        params={
            "to": phone_number,
            "body": message,
        },
    )
    return result.get("data", {}).get("success", False)
```

**Step 2: Run tests to verify they pass**

Run: `pytest tests/test_composio_tools.py -v`
Expected: PASS (3 passed)

**Step 3: Commit**

```bash
git add src/composio_tools.py
git commit -m "feat: implement Composio tools wrapper"
```

---

## Task 4: Create workflows package structure

**Files:**
- Create: `src/workflows/__init__.py`
- Create: `src/workflows/base.py`

**Step 1: Create package init**

```python
"""Eva workflow modules."""
from .heartbeat import run_heartbeat
from .morning_brief import run_morning_brief
from .weekly_review import run_weekly_review

__all__ = ["run_heartbeat", "run_morning_brief", "run_weekly_review"]
```

**Step 2: Create base workflow utilities**

```python
"""Base utilities for Eva workflows."""
import subprocess
from pathlib import Path


def sync_memory(repo_dir: Path) -> None:
    """Pull latest memory from git.

    Args:
        repo_dir: Path to repository root
    """
    subprocess.run(
        ["git", "pull", "--rebase"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )


def push_memory(repo_dir: Path, message: str) -> None:
    """Commit and push memory changes.

    Args:
        repo_dir: Path to repository root
        message: Commit message
    """
    subprocess.run(
        ["git", "add", "memory/context.md"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )
    # Check if there are changes to commit
    result = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=repo_dir,
        capture_output=True,
    )
    if result.returncode != 0:  # Changes exist
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "push"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )
```

**Step 3: Commit**

```bash
git add src/workflows/
git commit -m "feat: create workflows package structure"
```

---

## Task 5: Write failing tests for heartbeat workflow

**Files:**
- Create: `tests/test_workflows.py`

**Step 1: Write failing tests**

```python
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
        from datetime import datetime, timedelta

        now = datetime.utcnow()
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
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_workflows.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.workflows.heartbeat'"

**Step 3: Commit failing tests**

```bash
git add tests/test_workflows.py
git commit -m "test: add failing tests for heartbeat workflow"
```

---

## Task 6: Implement heartbeat workflow

**Files:**
- Create: `src/workflows/heartbeat.py`

**Step 1: Write implementation**

```python
"""Heartbeat workflow - checks for urgent items every 30 minutes."""
from datetime import datetime, timedelta
from pathlib import Path

from ..composio_tools import fetch_emails, fetch_calendar_events, send_whatsapp
from ..memory import update_context
from .base import sync_memory, push_memory


# Keywords that indicate urgency
URGENT_KEYWORDS = ["urgent", "asap", "emergency", "critical", "action required", "immediately"]

# VIP senders (always alert)
VIP_SENDERS = ["louis", "lewkai"]


def check_urgent_emails(emails: list[dict]) -> list[dict]:
    """Filter emails for urgent ones.

    Args:
        emails: List of email dicts

    Returns:
        List of urgent emails
    """
    urgent = []
    for email in emails:
        subject = email.get("subject", "").lower()
        sender = email.get("from", "").lower()

        # Check for urgent keywords
        is_urgent = any(kw in subject for kw in URGENT_KEYWORDS)

        # Check for VIP senders
        is_vip = any(vip in sender for vip in VIP_SENDERS)

        if is_urgent or is_vip:
            urgent.append(email)

    return urgent


def check_upcoming_meetings(events: list[dict], hours: int = 2) -> list[dict]:
    """Filter calendar events for upcoming ones.

    Args:
        events: List of calendar event dicts
        hours: Look ahead window in hours

    Returns:
        List of events within window
    """
    now = datetime.utcnow()
    cutoff = now + timedelta(hours=hours)
    upcoming = []

    for event in events:
        start_str = event.get("start", {}).get("dateTime", "")
        if not start_str:
            continue

        # Parse ISO format
        start = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
        start_naive = start.replace(tzinfo=None)

        if now <= start_naive <= cutoff:
            upcoming.append(event)

    return upcoming


def run_heartbeat(repo_dir: Path, phone_number: str) -> None:
    """Run heartbeat check.

    Args:
        repo_dir: Path to Eva repository
        phone_number: WhatsApp number to alert
    """
    memory_dir = repo_dir / "memory"

    # Sync memory from git
    sync_memory(repo_dir)

    # Fetch data
    emails = fetch_emails(max_results=20, query="is:unread")
    events = fetch_calendar_events(hours_ahead=2)

    # Check for urgent items
    urgent_emails = check_urgent_emails(emails)
    upcoming_meetings = check_upcoming_meetings(events, hours=2)

    # Build alert message if needed
    alerts = []
    if urgent_emails:
        alerts.append(f"📧 {len(urgent_emails)} urgent email(s):")
        for email in urgent_emails[:3]:  # Top 3
            alerts.append(f"  • {email.get('subject', 'No subject')[:50]}")

    if upcoming_meetings:
        alerts.append(f"📅 {len(upcoming_meetings)} meeting(s) in next 2 hours:")
        for event in upcoming_meetings[:3]:
            alerts.append(f"  • {event.get('summary', 'No title')[:50]}")

    # Send alert if anything urgent
    if alerts:
        message = "⚡ Eva Heartbeat Alert\n\n" + "\n".join(alerts)
        send_whatsapp(phone_number, message)

        # Log to context
        update_context(
            memory_dir,
            category="Heartbeat",
            summary=f"Sent alert: {len(urgent_emails)} emails, {len(upcoming_meetings)} meetings",
            details=message,
        )
        push_memory(repo_dir, "eva: heartbeat alert sent")
```

**Step 2: Run tests to verify they pass**

Run: `pytest tests/test_workflows.py -v`
Expected: PASS (3 passed)

**Step 3: Commit**

```bash
git add src/workflows/heartbeat.py
git commit -m "feat: implement heartbeat workflow"
```

---

## Task 7: Write failing tests for morning brief workflow

**Files:**
- Modify: `tests/test_workflows.py`

**Step 1: Add failing tests**

```python
from src.workflows.morning_brief import run_morning_brief, generate_brief


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
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_workflows.py::TestGenerateBrief -v`
Expected: FAIL with "ImportError: cannot import name 'generate_brief'"

**Step 3: Commit failing tests**

```bash
git add tests/test_workflows.py
git commit -m "test: add failing tests for morning brief workflow"
```

---

## Task 8: Implement morning brief workflow

**Files:**
- Create: `src/workflows/morning_brief.py`

**Step 1: Write implementation**

```python
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
```

**Step 2: Run tests to verify they pass**

Run: `pytest tests/test_workflows.py -v`
Expected: PASS (5 passed)

**Step 3: Commit**

```bash
git add src/workflows/morning_brief.py
git commit -m "feat: implement morning brief workflow"
```

---

## Task 9: Implement weekly review workflow

**Files:**
- Create: `src/workflows/weekly_review.py`
- Modify: `tests/test_workflows.py`

**Step 1: Write test**

```python
from src.workflows.weekly_review import run_weekly_review


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
```

**Step 2: Write implementation**

```python
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
```

**Step 3: Run tests**

Run: `pytest tests/test_workflows.py -v`
Expected: PASS (6 passed)

**Step 4: Commit**

```bash
git add src/workflows/weekly_review.py tests/test_workflows.py
git commit -m "feat: implement weekly review workflow"
```

---

## Task 10: Update workflows __init__.py

**Files:**
- Modify: `src/workflows/__init__.py`

**Step 1: Update exports**

```python
"""Eva workflow modules."""
from .heartbeat import run_heartbeat
from .morning_brief import run_morning_brief
from .weekly_review import run_weekly_review

__all__ = ["run_heartbeat", "run_morning_brief", "run_weekly_review"]
```

**Step 2: Commit**

```bash
git add src/workflows/__init__.py
git commit -m "chore: update workflows package exports"
```

---

## Task 11: Create heartbeat GitHub Action

**Files:**
- Create: `.github/workflows/heartbeat.yml`

**Step 1: Create workflow file**

```yaml
name: Eva Heartbeat

on:
  schedule:
    - cron: '*/30 * * * *'  # Every 30 minutes
  workflow_dispatch:  # Manual trigger for testing

env:
  EVA_PROVIDER: nvidia
  NVIDIA_API_KEY: ${{ secrets.NVIDIA_API_KEY }}
  COMPOSIO_API_KEY: ${{ secrets.COMPOSIO_API_KEY }}
  LOUIS_PHONE: ${{ secrets.LOUIS_PHONE }}

jobs:
  heartbeat:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .

      - name: Configure git
        run: |
          git config user.name "Eva"
          git config user.email "eva@lewkai.com"

      - name: Run heartbeat
        run: |
          python -c "
          from pathlib import Path
          import os
          from src.workflows import run_heartbeat
          run_heartbeat(Path('.'), os.environ['LOUIS_PHONE'])
          "

      - name: Push context updates
        run: |
          git add memory/context.md || true
          git diff --cached --quiet || git commit -m 'eva: heartbeat check'
          git push || true
```

**Step 2: Create workflows directory**

```bash
mkdir -p .github/workflows
```

**Step 3: Commit**

```bash
git add .github/workflows/heartbeat.yml
git commit -m "feat: add heartbeat GitHub Action"
```

---

## Task 12: Create morning brief GitHub Action

**Files:**
- Create: `.github/workflows/morning-brief.yml`

**Step 1: Create workflow file**

```yaml
name: Eva Morning Brief

on:
  schedule:
    - cron: '0 5 * * *'  # 5am UTC = 7am SAST
  workflow_dispatch:

env:
  EVA_PROVIDER: nvidia
  NVIDIA_API_KEY: ${{ secrets.NVIDIA_API_KEY }}
  COMPOSIO_API_KEY: ${{ secrets.COMPOSIO_API_KEY }}
  LOUIS_PHONE: ${{ secrets.LOUIS_PHONE }}

jobs:
  morning-brief:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .

      - name: Configure git
        run: |
          git config user.name "Eva"
          git config user.email "eva@lewkai.com"

      - name: Run morning brief
        run: |
          python -c "
          from pathlib import Path
          import os
          from src.workflows import run_morning_brief
          run_morning_brief(Path('.'), os.environ['LOUIS_PHONE'])
          "

      - name: Push context updates
        run: |
          git add memory/context.md || true
          git diff --cached --quiet || git commit -m 'eva: morning brief sent'
          git push || true
```

**Step 2: Commit**

```bash
git add .github/workflows/morning-brief.yml
git commit -m "feat: add morning brief GitHub Action"
```

---

## Task 13: Create weekly review GitHub Action

**Files:**
- Create: `.github/workflows/weekly-review.yml`

**Step 1: Create workflow file**

```yaml
name: Eva Weekly Review

on:
  schedule:
    - cron: '0 18 * * 0'  # 6pm UTC Sunday = 8pm SAST
  workflow_dispatch:

env:
  EVA_PROVIDER: nvidia
  NVIDIA_API_KEY: ${{ secrets.NVIDIA_API_KEY }}
  COMPOSIO_API_KEY: ${{ secrets.COMPOSIO_API_KEY }}
  LOUIS_PHONE: ${{ secrets.LOUIS_PHONE }}

jobs:
  weekly-review:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .

      - name: Configure git
        run: |
          git config user.name "Eva"
          git config user.email "eva@lewkai.com"

      - name: Run weekly review
        run: |
          python -c "
          from pathlib import Path
          import os
          from src.workflows import run_weekly_review
          run_weekly_review(Path('.'), os.environ['LOUIS_PHONE'])
          "

      - name: Push context updates
        run: |
          git add memory/context.md || true
          git diff --cached --quiet || git commit -m 'eva: weekly review sent'
          git push || true
```

**Step 2: Commit**

```bash
git add .github/workflows/weekly-review.yml
git commit -m "feat: add weekly review GitHub Action"
```

---

## Task 14: Create error notify GitHub Action

**Files:**
- Create: `.github/workflows/error-notify.yml`

**Step 1: Create workflow file**

```yaml
name: Eva Error Notify

on:
  workflow_run:
    workflows:
      - "Eva Heartbeat"
      - "Eva Morning Brief"
      - "Eva Weekly Review"
    types:
      - completed

env:
  COMPOSIO_API_KEY: ${{ secrets.COMPOSIO_API_KEY }}
  LOUIS_PHONE: ${{ secrets.LOUIS_PHONE }}

jobs:
  notify-on-failure:
    runs-on: ubuntu-latest
    if: ${{ github.event.workflow_run.conclusion == 'failure' }}

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .

      - name: Send error notification
        run: |
          python -c "
          import os
          from src.composio_tools import send_whatsapp

          workflow = '${{ github.event.workflow_run.name }}'
          run_url = '${{ github.event.workflow_run.html_url }}'

          message = f'''⚠️ Eva Error Alert

          Workflow failed: {workflow}

          Check logs: {run_url}

          — Eva'''

          send_whatsapp(os.environ['LOUIS_PHONE'], message)
          "
```

**Step 2: Commit**

```bash
git add .github/workflows/error-notify.yml
git commit -m "feat: add error notify GitHub Action"
```

---

## Task 15: Write failing tests for Flask gateway

**Files:**
- Create: `tests/test_gateway.py`

**Step 1: Write failing tests**

```python
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
           patch("src.gateway.push_memory"):

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
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_gateway.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.gateway'"

**Step 3: Commit failing tests**

```bash
git add tests/test_gateway.py
git commit -m "test: add failing tests for Flask gateway"
```

---

## Task 16: Implement Flask gateway

**Files:**
- Create: `src/gateway.py`

**Step 1: Write implementation**

```python
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
```

**Step 2: Run tests to verify they pass**

Run: `pytest tests/test_gateway.py -v`
Expected: PASS (5 passed)

**Step 3: Commit**

```bash
git add src/gateway.py
git commit -m "feat: implement Flask gateway for WhatsApp"
```

---

## Task 17: Create VPS deployment files

**Files:**
- Create: `deploy/eva-gateway.service`
- Create: `deploy/nginx-eva.conf`
- Create: `deploy/setup.sh`

**Step 1: Create systemd service file**

```ini
# deploy/eva-gateway.service
[Unit]
Description=Eva Gateway
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/eva
Environment="PATH=/opt/eva/.venv/bin"
EnvironmentFile=/opt/eva/.env
ExecStart=/opt/eva/.venv/bin/gunicorn -w 2 -b 127.0.0.1:18790 src.gateway:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**Step 2: Create Nginx config**

```nginx
# deploy/nginx-eva.conf
# Add to existing server block or create new one

location /eva/webhook {
    proxy_pass http://127.0.0.1:18790/webhook;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Hub-Signature-256 $http_x_hub_signature_256;
}

location /eva/health {
    proxy_pass http://127.0.0.1:18790/health;
}
```

**Step 3: Create setup script**

```bash
#!/bin/bash
# deploy/setup.sh - Run on VPS to set up Eva gateway

set -e

echo "=== Eva Gateway Setup ==="

# Clone or update repo
if [ -d /opt/eva ]; then
    echo "Updating existing installation..."
    cd /opt/eva
    git pull
else
    echo "Fresh installation..."
    git clone https://github.com/safarivis/agents_eva.git /opt/eva
    cd /opt/eva
fi

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
pip install gunicorn

# Create .env if not exists
if [ ! -f .env ]; then
    echo "Creating .env template..."
    cat > .env << 'EOF'
EVA_PROVIDER=nvidia
NVIDIA_API_KEY=your_key_here
COMPOSIO_API_KEY=your_key_here
META_VERIFY_TOKEN=your_verify_token
META_APP_SECRET=your_app_secret
ALLOWED_PHONE=27123456789
EVA_REPO_DIR=/opt/eva
EOF
    echo ">>> EDIT /opt/eva/.env with your actual keys!"
fi

# Install systemd service
cp deploy/eva-gateway.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable eva-gateway
systemctl start eva-gateway

echo ""
echo "=== Setup Complete ==="
echo "1. Edit /opt/eva/.env with your keys"
echo "2. Add Nginx config from deploy/nginx-eva.conf"
echo "3. Reload nginx: systemctl reload nginx"
echo "4. Check status: systemctl status eva-gateway"
```

**Step 4: Make setup script executable and commit**

```bash
mkdir -p deploy
chmod +x deploy/setup.sh
git add deploy/
git commit -m "feat: add VPS deployment files"
```

---

## Task 18: Run full test suite with coverage

**Step 1: Run all tests**

Run: `pytest tests/ -v --cov=src --cov-report=term-missing`
Expected: All tests pass, good coverage

**Step 2: Verify test count**

Expected: ~20+ tests covering:
- Composio tools (3)
- Workflows (6)
- Gateway (5)
- Existing tests (28)

---

## Task 19: Push and configure GitHub secrets

**Step 1: Push all changes**

```bash
git push origin main
```

**Step 2: Configure GitHub secrets**

Go to: https://github.com/safarivis/agents_eva/settings/secrets/actions

Add these secrets:
- `NVIDIA_API_KEY` - Your NVIDIA API key
- `COMPOSIO_API_KEY` - Your Composio API key
- `LOUIS_PHONE` - Your WhatsApp number (with country code, no +)

**Step 3: Test heartbeat workflow manually**

Go to: Actions → Eva Heartbeat → Run workflow

---

## Task 20: Deploy to VPS

**Step 1: SSH to VPS**

```bash
ssh root@srv1385761.hstgr.cloud
```

**Step 2: Run setup script**

```bash
curl -fsSL https://raw.githubusercontent.com/safarivis/agents_eva/main/deploy/setup.sh | bash
```

**Step 3: Configure environment**

```bash
nano /opt/eva/.env
# Add your actual API keys
```

**Step 4: Configure Nginx**

```bash
nano /etc/nginx/sites-available/default
# Add the /eva/webhook location block
systemctl reload nginx
```

**Step 5: Configure Meta webhook**

Go to: Meta Developer Console → Your App → WhatsApp → Configuration
- Callback URL: `https://srv1385761.hstgr.cloud/eva/webhook`
- Verify Token: (same as META_VERIFY_TOKEN in .env)

**Step 6: Test end-to-end**

Send WhatsApp message to Eva, verify response.

---

## Summary

Phase 3 creates:
- `src/composio_tools.py` - Wrapper for Composio integrations
- `src/workflows/` - heartbeat, morning_brief, weekly_review
- `src/gateway.py` - Flask webhook receiver
- `.github/workflows/` - 4 workflow files
- `deploy/` - VPS deployment files
- `tests/` - ~15 new tests

**Environment variables needed:**
- GitHub: `NVIDIA_API_KEY`, `COMPOSIO_API_KEY`, `LOUIS_PHONE`
- VPS: Same + `META_VERIFY_TOKEN`, `META_APP_SECRET`, `ALLOWED_PHONE`

**Next:** Phase 4 - Skills registry and self-awareness features
