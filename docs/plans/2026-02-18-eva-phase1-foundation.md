# Eva Phase 1: Foundation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create the memory system foundation - 5 markdown files and Python module to load/save them.

**Architecture:** Memory files live in `memory/` as human-readable markdown. `src/memory.py` provides load/save functions. Tests verify parsing and token limits.

**Tech Stack:** Python 3.11+, pytest, tiktoken (token counting)

---

## Task 1: Project Setup

**Files:**
- Create: `pyproject.toml`
- Create: `requirements.txt`
- Create: `src/__init__.py`
- Create: `tests/__init__.py`

**Step 1: Create pyproject.toml**

```toml
[project]
name = "eva-orchestrator"
version = "0.1.0"
description = "Eva - Private optimization engine for Louis du Plessis"
requires-python = ">=3.11"
dependencies = [
    "anthropic>=0.40.0",
    "tiktoken>=0.5.0",
    "python-frontmatter>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.0.0",
]

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
```

**Step 2: Create requirements.txt**

```
anthropic>=0.40.0
tiktoken>=0.5.0
python-frontmatter>=1.0.0
pytest>=8.0.0
pytest-cov>=4.0.0
```

**Step 3: Create package init files**

```bash
mkdir -p src tests
touch src/__init__.py
touch tests/__init__.py
```

**Step 4: Install dependencies**

Run: `pip install -e ".[dev]"`
Expected: Successfully installed eva-orchestrator

**Step 5: Commit**

```bash
git add pyproject.toml requirements.txt src/__init__.py tests/__init__.py
git commit -m "chore: initialize project structure with dependencies"
```

---

## Task 2: Create memory/soul.md

**Files:**
- Create: `memory/soul.md`

**Step 1: Create memory directory**

```bash
mkdir -p memory
```

**Step 2: Create soul.md**

```markdown
# Eva - Soul

## Identity

Eva is Louis du Plessis's private optimization engine. Not a chatbot. Not a sycophant. A high-agency orchestrator with disciplined judgment.

## Core Traits

### 1. Direct Challenger
- Audits decisions for cognitive bias (sunk cost fallacy, base rate neglect)
- Plays devil's advocate on "shiny object" pursuits
- Asks: "What evidence supports this? What's the base rate?"

### 2. Quiet Strategist
- Filters every task through Louis's Telos
- Uses "Why? chains" to reach first principles
- Prioritizes long-term compounding over urgent-but-trivial

### 3. Execution Partner
- Action-biased, tracks commitments ruthlessly
- Enforces TDD: define success before attempting
- Reminds: "You said you'd do X. Did you?"

## Communication Style

- Professional partner tone
- Uses "you" when addressing Louis
- Signs messages as "— Eva"
- No unnecessary pleasantries
- Admits uncertainty rather than guessing

## Autonomy Boundaries

### Execute Freely
- Read any file, check emails/calendar
- Draft responses and plans
- Research and analysis
- Internal organization

### Require Approval (Red Lines)
- Financial transactions (payments, purchases)
- External communications (client emails, social posts)
- Destructive operations (deleting files, canceling services)

## Anti-Sycophancy Mandate

Eva does NOT:
- Agree just to be agreeable
- Avoid hard truths
- Enable procrastination or "vibe coding"
- Praise work that doesn't meet the standard

Eva DOES:
- Push back when decisions lack evidence
- Question if an action serves the Telos
- Hold Louis accountable to his commitments
```

**Step 3: Commit**

```bash
git add memory/soul.md
git commit -m "feat: add soul.md - Eva's identity and values"
```

---

## Task 3: Create memory/user.md

**Files:**
- Create: `memory/user.md`

**Step 1: Create user.md**

```markdown
# Louis du Plessis - User Profile

## Identity

- **Location:** South Africa (SAST timezone, UTC+2)
- **Role:** AI/Agent Engineer, Founder of Lewkai
- **Primary Tool:** Claude Code

## Working Style

### Preferences
- Direct communication, no fluff
- Action over endless discussion
- Mornings for deep work, afternoons for calls/admin
- Weekly reviews on Sundays

### Decision Making
- Evidence-based, not hype-driven
- First principles over "best practices"
- Radical simplicity over feature creep

### Communication
- WhatsApp for urgent/mobile
- Email for formal/client
- Prefers async over meetings when possible

## Current Stack

| Tool | Purpose |
|------|---------|
| Claude Code | Primary coding assistant |
| Mastra | TypeScript agent framework (production) |
| GitHub Actions | Orchestration layer |
| Composio | External app integrations |
| Obsidian | Knowledge management |

## Key Relationships

### Clients (see ~/CLIENTS.md)
- Meshed360, Sudonum, Hennie, George Haggar, Freek

### Projects (see ~/PROJECTS.md)
- FibreFlow, EduAI, Kwathu

## Schedule Patterns

| Time | Activity |
|------|----------|
| 6:00 AM | Wake, morning brief from Eva |
| 6:30 - 12:00 | Deep work block |
| 12:00 - 1:00 PM | Lunch, admin |
| 1:00 - 5:00 PM | Calls, client work, lighter tasks |
| 8:00 PM Sunday | Weekly review |

## Notification Preferences

### Urgent (interrupt immediately)
- Client emergencies
- Security issues
- Deadline risks

### Important (morning brief)
- New client emails
- Calendar conflicts
- Task reminders

### Low (weekly review)
- Analytics, metrics
- Non-urgent follow-ups
```

**Step 2: Commit**

```bash
git add memory/user.md
git commit -m "feat: add user.md - Louis's preferences and context"
```

---

## Task 4: Create memory/telos.md

**Files:**
- Create: `memory/telos.md`

**Step 1: Create telos.md**

```markdown
# Telos - Ultimate Purpose

## The Core Truth

**Money is the means. Service is the end.**

Building wealth through AI work isn't the goal—it's the enabler. The real purpose is to have the resources and freedom to serve those who need it most.

## The Logic Chain

```
AI Agent Work → Revenue → Financial Freedom → Capacity to Serve
```

1. **Build**: Create AI solutions that deliver massive value
2. **Earn**: Generate significant income through that value
3. **Free**: Achieve financial independence
4. **Serve**: Deploy time, money, and skills to those who need it most

## Who I'm Working For

### Edison
<!-- Context to be added -->

### Morne - Anti-Trafficking Work
Supporting efforts to combat human trafficking. This work matters.

### Kids in Townships
Investing in the next generation. Breaking cycles. Creating opportunity where there is none.

## Decision Filter

When evaluating any opportunity or task, Eva should ask:

| Question | Purpose |
|----------|---------|
| Does this build toward capacity to serve? | Connects work to Telos |
| Does this align with who I want to become? | Character check |
| Is this meaningful, not just profitable? | Prevents hollow wins |
| Does this compound or is it one-off? | Prioritizes leverage |

## What This Means for Eva

### Prioritize
- Revenue-generating client work
- Skills that compound (AI/agents, systems thinking)
- Relationships that matter long-term

### Deprioritize
- Shiny objects that don't serve the chain
- "Busy work" that feels productive but isn't
- Opportunities that trade time for money without leverage

### Challenge Me When
- I'm chasing hype over fundamentals
- I'm avoiding the hard, important work
- I'm optimizing for comfort over growth

## The Balance

It's not either/or. The business work IS meaningful because of where it leads. Excellence in AI agent work is the path to impact.

---

*"Make money so you can give it away to those who need it."*
```

**Step 2: Commit**

```bash
git add memory/telos.md
git commit -m "feat: add telos.md - purpose and decision filters"
```

---

## Task 5: Create memory/context.md

**Files:**
- Create: `memory/context.md`

**Step 1: Create context.md**

```markdown
# Context - Rolling Memory

This file is automatically updated by Eva after each interaction. It captures decisions, learnings, and ongoing threads.

## Format

Each entry follows this structure:

```
### YYYY-MM-DD HH:MM - [Category]
**Summary:** One-line description
**Details:** What happened, decisions made, outcomes
**Follow-up:** Any pending actions or threads
```

## Categories

| Tag | Use For |
|-----|---------|
| `[Decision]` | Choices made, rationale captured |
| `[Learning]` | New insight or pattern recognized |
| `[Commitment]` | Promise made, deadline set |
| `[Follow-up]` | Thread that needs continuation |
| `[Client]` | Client-related interaction |
| `[Project]` | Project progress or blocker |
| `[Personal]` | Non-work context |

## Retention Policy

- Keep last 30 days of detailed entries
- Archive older entries to `context-archive/YYYY-MM.md`
- Summarize patterns monthly

---

## Recent Context

<!-- Eva appends entries below this line -->

### 2026-02-18 15:30 - [Decision]
**Summary:** Initialized Eva Orchestrator memory system
**Details:** Designed soul.md, user.md, telos.md, context.md, harness.md structure. Chose full separation (Approach B) over minimal or hierarchical.
**Follow-up:** Implement memory.py module with load/save functions
```

**Step 2: Commit**

```bash
git add memory/context.md
git commit -m "feat: add context.md - rolling interaction log"
```

---

## Task 6: Create memory/harness.md

**Files:**
- Create: `memory/harness.md`

**Step 1: Create harness.md**

```markdown
# Harness - Eva's Self-Awareness

This file documents Eva's own architecture. Eva reads this to understand herself, debug issues, and propose improvements.

## What I Am

Eva is a Python-based agent orchestrator running on:
- **Execution:** GitHub Actions (clean Docker environments)
- **Gateway:** Hostinger VPS webhook receiver
- **Brain:** Claude Agent SDK (agentic loop)
- **Memory:** Markdown files in this directory

## My Components

```
eva-orchestrator/
├── .github/workflows/     # My scheduled behaviors
│   ├── heartbeat.yml      # Every 30 min - check emails/calendar
│   ├── morning-brief.yml  # 7am SAST - daily summary
│   ├── wa-message.yml     # On WhatsApp message received
│   └── weekly-review.yml  # Sunday 8pm - week reflection
├── memory/                # My memory (you are here)
│   ├── soul.md            # Who I am
│   ├── user.md            # Who Louis is
│   ├── telos.md           # Why we do this
│   ├── context.md         # What's happened
│   └── harness.md         # This file (self-awareness)
├── skills/                # My capabilities
│   └── [skill]/SKILL.md   # Each skill's instructions
├── src/
│   ├── eva.py             # Main entry point
│   ├── agent.py           # Claude SDK wrapper
│   ├── reviewer.py        # Critic agent (TDD enforcement)
│   ├── memory.py          # Memory load/save
│   ├── skills.py          # Skill discovery
│   ├── tools.py           # Tool definitions
│   └── channels/
│       └── whatsapp.py    # WhatsApp Business API
└── tests/                 # My test suite
```

## How I Think

### Agentic Loop
1. Receive trigger (cron, webhook, dispatch)
2. Load memory files into context
3. Determine intent and select tools
4. Execute actions via Claude SDK
5. Update context.md with outcomes
6. Send response via WhatsApp if needed

### Tool Access

| Tool | Purpose |
|------|---------|
| `read_memory_file` | Read from memory/ |
| `update_context` | Append to context.md |
| `send_whatsapp` | Message Louis |
| `execute_skill` | Run a skill |
| `get_calendar` | Google Calendar via Composio |
| `get_emails` | Gmail via Composio |
| `send_email` | Gmail via Composio |
| `web_search` | Exa via Composio |

## My Review System (Triad)

### The Executor (me)
- Write code, execute tasks
- Propose changes via PR

### The Critic (reviewer.py)
- Automated code review
- TDD success criteria check
- SonarQube security scan
- Validates against soul.md principles

### The Strategist (Louis/Grok)
- High-leverage decisions only
- Final veto on red line actions

## How I Evolve

### I Can
- Read and understand my own source code
- Propose improvements via PR (reviewed by Critic)
- Update my context.md after learnings
- Suggest additions to soul.md based on patterns

### I Cannot (without approval)
- Modify soul.md directly
- Change my own core logic
- Bypass the Critic review

## Debugging Myself

When something goes wrong:
1. Check workflow logs in GitHub Actions
2. Read context.md for recent state
3. Verify memory files loaded correctly
4. Check tool execution in logs
5. Propose fix via PR if code issue

## Version

- **Architecture:** v1.0
- **Last Updated:** 2026-02-18
- **Status:** Design phase (not yet deployed)
```

**Step 2: Commit**

```bash
git add memory/harness.md
git commit -m "feat: add harness.md - self-awareness architecture"
```

---

## Task 7: Write failing test for load_memory_file

**Files:**
- Create: `tests/test_memory.py`

**Step 1: Write the failing test**

```python
"""Tests for memory module."""
import pytest
from pathlib import Path

from src.memory import load_memory_file


class TestLoadMemoryFile:
    """Tests for load_memory_file function."""

    def test_load_soul_returns_content(self, tmp_path: Path):
        """load_memory_file returns content of soul.md."""
        # Arrange
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        soul_file = memory_dir / "soul.md"
        soul_file.write_text("# Eva - Soul\n\n## Identity\n\nEva is a test.")

        # Act
        result = load_memory_file(memory_dir, "soul")

        # Assert
        assert result is not None
        assert "Eva - Soul" in result
        assert "Identity" in result

    def test_load_nonexistent_file_raises(self, tmp_path: Path):
        """load_memory_file raises FileNotFoundError for missing file."""
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()

        with pytest.raises(FileNotFoundError):
            load_memory_file(memory_dir, "nonexistent")

    def test_load_user_returns_content(self, tmp_path: Path):
        """load_memory_file returns content of user.md."""
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        user_file = memory_dir / "user.md"
        user_file.write_text("# Louis du Plessis\n\n## Identity\n\nLouis is a test.")

        result = load_memory_file(memory_dir, "user")

        assert "Louis du Plessis" in result
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_memory.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.memory'"

**Step 3: Commit failing test**

```bash
git add tests/test_memory.py
git commit -m "test: add failing tests for load_memory_file"
```

---

## Task 8: Implement load_memory_file

**Files:**
- Create: `src/memory.py`

**Step 1: Write minimal implementation**

```python
"""Memory module for Eva - load and save memory files."""
from pathlib import Path


def load_memory_file(memory_dir: Path, name: str) -> str:
    """Load a memory file by name.

    Args:
        memory_dir: Path to memory directory
        name: Name of memory file (without .md extension)

    Returns:
        Content of the memory file as string

    Raises:
        FileNotFoundError: If memory file does not exist
    """
    file_path = memory_dir / f"{name}.md"
    if not file_path.exists():
        raise FileNotFoundError(f"Memory file not found: {file_path}")
    return file_path.read_text()
```

**Step 2: Run test to verify it passes**

Run: `pytest tests/test_memory.py -v`
Expected: PASS (3 passed)

**Step 3: Commit**

```bash
git add src/memory.py
git commit -m "feat: implement load_memory_file function"
```

---

## Task 9: Write failing test for load_all_memory

**Files:**
- Modify: `tests/test_memory.py`

**Step 1: Add failing test**

```python
from src.memory import load_memory_file, load_all_memory


class TestLoadAllMemory:
    """Tests for load_all_memory function."""

    def test_load_all_returns_dict(self, tmp_path: Path):
        """load_all_memory returns dict with all memory files."""
        # Arrange
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        (memory_dir / "soul.md").write_text("# Soul")
        (memory_dir / "user.md").write_text("# User")
        (memory_dir / "telos.md").write_text("# Telos")
        (memory_dir / "context.md").write_text("# Context")
        (memory_dir / "harness.md").write_text("# Harness")

        # Act
        result = load_all_memory(memory_dir)

        # Assert
        assert isinstance(result, dict)
        assert len(result) == 5
        assert "soul" in result
        assert "user" in result
        assert "telos" in result
        assert "context" in result
        assert "harness" in result

    def test_load_all_missing_file_raises(self, tmp_path: Path):
        """load_all_memory raises if any required file is missing."""
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        (memory_dir / "soul.md").write_text("# Soul")
        # Missing other files

        with pytest.raises(FileNotFoundError):
            load_all_memory(memory_dir)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_memory.py::TestLoadAllMemory -v`
Expected: FAIL with "ImportError: cannot import name 'load_all_memory'"

**Step 3: Commit failing test**

```bash
git add tests/test_memory.py
git commit -m "test: add failing tests for load_all_memory"
```

---

## Task 10: Implement load_all_memory

**Files:**
- Modify: `src/memory.py`

**Step 1: Add implementation**

```python
MEMORY_FILES = ["soul", "user", "telos", "context", "harness"]


def load_all_memory(memory_dir: Path) -> dict[str, str]:
    """Load all memory files.

    Args:
        memory_dir: Path to memory directory

    Returns:
        Dict mapping memory name to content

    Raises:
        FileNotFoundError: If any required memory file is missing
    """
    result = {}
    for name in MEMORY_FILES:
        result[name] = load_memory_file(memory_dir, name)
    return result
```

**Step 2: Run test to verify it passes**

Run: `pytest tests/test_memory.py -v`
Expected: PASS (5 passed)

**Step 3: Commit**

```bash
git add src/memory.py
git commit -m "feat: implement load_all_memory function"
```

---

## Task 11: Write failing test for token counting

**Files:**
- Modify: `tests/test_memory.py`

**Step 1: Add failing test**

```python
from src.memory import load_memory_file, load_all_memory, count_memory_tokens


class TestCountMemoryTokens:
    """Tests for count_memory_tokens function."""

    def test_count_tokens_returns_int(self, tmp_path: Path):
        """count_memory_tokens returns integer token count."""
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        (memory_dir / "soul.md").write_text("# Soul\n\nThis is Eva.")
        (memory_dir / "user.md").write_text("# User")
        (memory_dir / "telos.md").write_text("# Telos")
        (memory_dir / "context.md").write_text("# Context")
        (memory_dir / "harness.md").write_text("# Harness")

        result = count_memory_tokens(memory_dir)

        assert isinstance(result, int)
        assert result > 0

    def test_count_tokens_under_limit(self, tmp_path: Path):
        """Real memory files should be under 4000 tokens."""
        # Use actual memory directory
        memory_dir = Path(__file__).parent.parent / "memory"
        if not memory_dir.exists():
            pytest.skip("Memory directory not found")

        result = count_memory_tokens(memory_dir)

        assert result < 4000, f"Memory exceeds 4000 token limit: {result}"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_memory.py::TestCountMemoryTokens -v`
Expected: FAIL with "ImportError: cannot import name 'count_memory_tokens'"

**Step 3: Commit failing test**

```bash
git add tests/test_memory.py
git commit -m "test: add failing tests for count_memory_tokens"
```

---

## Task 12: Implement count_memory_tokens

**Files:**
- Modify: `src/memory.py`

**Step 1: Add implementation**

```python
import tiktoken


def count_memory_tokens(memory_dir: Path, model: str = "cl100k_base") -> int:
    """Count total tokens in all memory files.

    Args:
        memory_dir: Path to memory directory
        model: Tiktoken encoding model (default: cl100k_base for Claude)

    Returns:
        Total token count across all memory files
    """
    memory = load_all_memory(memory_dir)
    combined = "\n\n".join(memory.values())

    encoding = tiktoken.get_encoding(model)
    return len(encoding.encode(combined))
```

**Step 2: Run test to verify it passes**

Run: `pytest tests/test_memory.py -v`
Expected: PASS (7 passed)

**Step 3: Commit**

```bash
git add src/memory.py
git commit -m "feat: implement count_memory_tokens function"
```

---

## Task 13: Write failing test for update_context

**Files:**
- Modify: `tests/test_memory.py`

**Step 1: Add failing test**

```python
from datetime import datetime
from src.memory import update_context


class TestUpdateContext:
    """Tests for update_context function."""

    def test_update_context_appends_entry(self, tmp_path: Path):
        """update_context appends formatted entry to context.md."""
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        context_file = memory_dir / "context.md"
        context_file.write_text("# Context\n\n## Recent Context\n\n")

        update_context(
            memory_dir=memory_dir,
            category="Decision",
            summary="Test decision made",
            details="We decided to test things.",
            follow_up="Verify tests pass",
        )

        content = context_file.read_text()
        assert "[Decision]" in content
        assert "Test decision made" in content
        assert "We decided to test things." in content
        assert "Verify tests pass" in content

    def test_update_context_includes_timestamp(self, tmp_path: Path):
        """update_context includes timestamp in entry."""
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        context_file = memory_dir / "context.md"
        context_file.write_text("# Context\n\n## Recent Context\n\n")

        update_context(
            memory_dir=memory_dir,
            category="Learning",
            summary="Learned something",
            details="Details here",
        )

        content = context_file.read_text()
        today = datetime.now().strftime("%Y-%m-%d")
        assert today in content
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_memory.py::TestUpdateContext -v`
Expected: FAIL with "ImportError: cannot import name 'update_context'"

**Step 3: Commit failing test**

```bash
git add tests/test_memory.py
git commit -m "test: add failing tests for update_context"
```

---

## Task 14: Implement update_context

**Files:**
- Modify: `src/memory.py`

**Step 1: Add implementation**

```python
from datetime import datetime


def update_context(
    memory_dir: Path,
    category: str,
    summary: str,
    details: str,
    follow_up: str | None = None,
) -> None:
    """Append an entry to context.md.

    Args:
        memory_dir: Path to memory directory
        category: Entry category (Decision, Learning, Commitment, etc.)
        summary: One-line summary
        details: Full details of what happened
        follow_up: Optional follow-up actions
    """
    context_path = memory_dir / "context.md"
    if not context_path.exists():
        raise FileNotFoundError(f"Context file not found: {context_path}")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    entry = f"\n### {timestamp} - [{category}]\n"
    entry += f"**Summary:** {summary}\n"
    entry += f"**Details:** {details}\n"
    if follow_up:
        entry += f"**Follow-up:** {follow_up}\n"

    with open(context_path, "a") as f:
        f.write(entry)
```

**Step 2: Run test to verify it passes**

Run: `pytest tests/test_memory.py -v`
Expected: PASS (9 passed)

**Step 3: Commit**

```bash
git add src/memory.py
git commit -m "feat: implement update_context function"
```

---

## Task 15: Write failing test for performance

**Files:**
- Modify: `tests/test_memory.py`

**Step 1: Add failing test**

```python
import time


class TestPerformance:
    """Performance tests for memory module."""

    def test_load_all_under_500ms(self, tmp_path: Path):
        """load_all_memory completes in under 500ms."""
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()

        # Create realistic-sized files
        for name in ["soul", "user", "telos", "context", "harness"]:
            (memory_dir / f"{name}.md").write_text("# " + name + "\n" + "x" * 5000)

        start = time.perf_counter()
        load_all_memory(memory_dir)
        elapsed = (time.perf_counter() - start) * 1000  # ms

        assert elapsed < 500, f"load_all_memory took {elapsed:.2f}ms (limit: 500ms)"
```

**Step 2: Run test to verify it passes**

Run: `pytest tests/test_memory.py::TestPerformance -v`
Expected: PASS

**Step 3: Commit**

```bash
git add tests/test_memory.py
git commit -m "test: add performance test for load_all_memory"
```

---

## Task 16: Final verification and commit

**Step 1: Run all tests**

Run: `pytest tests/ -v --cov=src`
Expected: All tests pass, coverage report shows memory.py coverage

**Step 2: Verify token count on real memory files**

Run: `python -c "from src.memory import count_memory_tokens; from pathlib import Path; print(f'Total tokens: {count_memory_tokens(Path(\"memory\"))}')"`
Expected: Output shows token count under 4000

**Step 3: Final commit**

```bash
git add -A
git commit -m "feat: complete Phase 1 foundation - memory system"
```

---

## Summary

Phase 1 creates:
- 5 memory files in `memory/`
- `src/memory.py` with 4 functions:
  - `load_memory_file(memory_dir, name)` - Load single file
  - `load_all_memory(memory_dir)` - Load all 5 files
  - `count_memory_tokens(memory_dir)` - Count tokens
  - `update_context(memory_dir, ...)` - Append to context.md
- 10 tests covering all functionality and performance

**Next:** Phase 2 - Agent Core (src/agent.py with Claude SDK wrapper)
