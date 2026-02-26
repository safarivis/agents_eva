# Security Auditor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement parallel Security Auditor using native GitHub Actions + Claude API and GitHub Agentic Workflows (`gh aw`) for side-by-side comparison.

**Architecture:** Two parallel workflows triggered on PR/push/schedule. Native approach uses Python module with Claude API for analysis. Agentic approach uses markdown-defined agent compiled via `gh aw`. Both post separate labeled outputs. Critical findings block merge and trigger immediate Gmail notification.

**Tech Stack:** Python 3.11, Anthropic SDK, Composio (Gmail), GitHub Actions, `gh aw` extension, pytest

---

## Task 1: Create Severity Enum and Data Models

**Files:**
- Create: `src/security/__init__.py`
- Create: `src/security/severity.py`
- Test: `tests/test_security/test_severity.py`

**Step 1: Create test directory and init files**

```bash
mkdir -p src/security tests/test_security
touch src/security/__init__.py tests/test_security/__init__.py
```

**Step 2: Write failing test for severity module**

Create `tests/test_security/test_severity.py`:

```python
"""Tests for security severity module."""
import pytest
from src.security.severity import Severity, Finding


class TestSeverity:
    def test_severity_ordering(self):
        """Severities should be orderable by priority."""
        assert Severity.CRITICAL > Severity.HIGH
        assert Severity.HIGH > Severity.MEDIUM
        assert Severity.MEDIUM > Severity.LOW

    def test_severity_blocks_merge(self):
        """Critical and High should block merge."""
        assert Severity.CRITICAL.blocks_merge is True
        assert Severity.HIGH.blocks_merge is True
        assert Severity.MEDIUM.blocks_merge is False
        assert Severity.LOW.blocks_merge is False

    def test_severity_immediate_notify(self):
        """Only Critical should trigger immediate notification."""
        assert Severity.CRITICAL.immediate_notify is True
        assert Severity.HIGH.immediate_notify is False
        assert Severity.MEDIUM.immediate_notify is False
        assert Severity.LOW.immediate_notify is False


class TestFinding:
    def test_finding_creation(self):
        """Finding should store all required fields."""
        finding = Finding(
            severity=Severity.HIGH,
            file="src/agent.py",
            line=42,
            check="input_validation",
            message="Unvalidated user input",
            recommendation="Add input validation",
        )
        assert finding.severity == Severity.HIGH
        assert finding.file == "src/agent.py"
        assert finding.line == 42
        assert finding.check == "input_validation"

    def test_finding_to_dict(self):
        """Finding should serialize to dict for JSON storage."""
        finding = Finding(
            severity=Severity.CRITICAL,
            file="src/tools.py",
            line=10,
            check="secrets",
            message="Hardcoded API key",
            recommendation="Use environment variable",
        )
        d = finding.to_dict()
        assert d["severity"] == "critical"
        assert d["file"] == "src/tools.py"
        assert d["line"] == 10

    def test_finding_from_dict(self):
        """Finding should deserialize from dict."""
        d = {
            "severity": "high",
            "file": "src/memory.py",
            "line": 23,
            "check": "path_traversal",
            "message": "Path traversal risk",
            "recommendation": "Sanitize path input",
        }
        finding = Finding.from_dict(d)
        assert finding.severity == Severity.HIGH
        assert finding.file == "src/memory.py"
```

**Step 3: Run test to verify it fails**

```bash
pytest tests/test_security/test_severity.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'src.security.severity'`

**Step 4: Write minimal implementation**

Create `src/security/severity.py`:

```python
"""Severity levels and finding data model for security auditor."""
from dataclasses import dataclass
from enum import IntEnum
from typing import Optional


class Severity(IntEnum):
    """Security finding severity levels, ordered by priority."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    @property
    def blocks_merge(self) -> bool:
        """Whether this severity should block PR merge."""
        return self >= Severity.HIGH

    @property
    def immediate_notify(self) -> bool:
        """Whether this severity triggers immediate notification."""
        return self == Severity.CRITICAL


@dataclass
class Finding:
    """A security finding from an audit."""

    severity: Severity
    file: str
    line: int
    check: str
    message: str
    recommendation: str
    snippet: Optional[str] = None

    def to_dict(self) -> dict:
        """Serialize to dict for JSON storage."""
        return {
            "severity": self.severity.name.lower(),
            "file": self.file,
            "line": self.line,
            "check": self.check,
            "message": self.message,
            "recommendation": self.recommendation,
            "snippet": self.snippet,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Finding":
        """Deserialize from dict."""
        return cls(
            severity=Severity[d["severity"].upper()],
            file=d["file"],
            line=d["line"],
            check=d["check"],
            message=d["message"],
            recommendation=d["recommendation"],
            snippet=d.get("snippet"),
        )
```

**Step 5: Update `src/security/__init__.py`**

```python
"""Security auditor module for Eva."""
from .severity import Severity, Finding

__all__ = ["Severity", "Finding"]
```

**Step 6: Run test to verify it passes**

```bash
pytest tests/test_security/test_severity.py -v
```

Expected: All tests PASS

**Step 7: Commit**

```bash
git add src/security/ tests/test_security/
git commit -m "feat(security): add severity enum and finding data model"
```

---

## Task 2: Implement Security Checks Module

**Files:**
- Create: `src/security/checks.py`
- Create: `tests/test_security/fixtures/` (vulnerable code samples)
- Test: `tests/test_security/test_checks.py`

**Step 1: Create test fixtures directory with vulnerable samples**

```bash
mkdir -p tests/test_security/fixtures
```

Create `tests/test_security/fixtures/vulnerable_secrets.py`:

```python
# Sample file with hardcoded secrets for testing
API_KEY = "sk-ant-api03-xxxxxxxxxxxx"
PASSWORD = "super_secret_password_123"
TOKEN = "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
SAFE_CONSTANT = "not-a-secret"
```

Create `tests/test_security/fixtures/vulnerable_injection.py`:

```python
# Sample file with injection vulnerabilities
import subprocess
import os

def run_command(user_input):
    # Command injection vulnerability
    os.system(f"echo {user_input}")
    subprocess.call(user_input, shell=True)

def execute_code(code_string):
    # Code execution vulnerability
    eval(code_string)
    exec(code_string)
```

Create `tests/test_security/fixtures/vulnerable_path.py`:

```python
# Sample file with path traversal vulnerability
from pathlib import Path

def read_file(user_path):
    # Path traversal - no validation
    with open(f"/data/{user_path}") as f:
        return f.read()

def load_memory(name):
    # Safe - uses enum
    valid = ["soul", "user", "telos"]
    if name in valid:
        return Path(f"memory/{name}.md").read_text()
```

Create `tests/test_security/fixtures/clean_code.py`:

```python
# Sample file with no vulnerabilities
import os
from pathlib import Path

API_KEY = os.environ.get("API_KEY")

def process_data(data: str) -> str:
    """Process data safely."""
    if not isinstance(data, str):
        raise TypeError("data must be string")
    return data.strip().lower()
```

**Step 2: Write failing test for checks module**

Create `tests/test_security/test_checks.py`:

```python
"""Tests for security checks module."""
import pytest
from pathlib import Path
from src.security.checks import (
    check_secrets,
    check_injection,
    check_path_traversal,
    run_all_checks,
)
from src.security.severity import Severity

FIXTURES = Path(__file__).parent / "fixtures"


class TestSecretChecks:
    def test_detects_api_key(self):
        """Should detect hardcoded API keys."""
        code = FIXTURES / "vulnerable_secrets.py"
        findings = check_secrets(code)
        assert len(findings) >= 1
        assert any(f.check == "hardcoded_secret" for f in findings)
        assert any(f.severity == Severity.CRITICAL for f in findings)

    def test_clean_code_no_secrets(self):
        """Should not flag environment variable usage."""
        code = FIXTURES / "clean_code.py"
        findings = check_secrets(code)
        assert len(findings) == 0


class TestInjectionChecks:
    def test_detects_command_injection(self):
        """Should detect os.system and subprocess.call with shell=True."""
        code = FIXTURES / "vulnerable_injection.py"
        findings = check_injection(code)
        assert len(findings) >= 2
        assert any("os.system" in f.message or "subprocess" in f.message for f in findings)

    def test_detects_eval_exec(self):
        """Should detect eval() and exec() calls."""
        code = FIXTURES / "vulnerable_injection.py"
        findings = check_injection(code)
        assert any("eval" in f.message or "exec" in f.message for f in findings)

    def test_clean_code_no_injection(self):
        """Should not flag safe code."""
        code = FIXTURES / "clean_code.py"
        findings = check_injection(code)
        assert len(findings) == 0


class TestPathTraversalChecks:
    def test_detects_unsanitized_path(self):
        """Should detect user input in file paths."""
        code = FIXTURES / "vulnerable_path.py"
        findings = check_path_traversal(code)
        assert len(findings) >= 1
        assert any(f.check == "path_traversal" for f in findings)

    def test_clean_code_no_path_issues(self):
        """Should not flag validated paths."""
        code = FIXTURES / "clean_code.py"
        findings = check_path_traversal(code)
        assert len(findings) == 0


class TestRunAllChecks:
    def test_aggregates_all_findings(self):
        """Should run all checks and aggregate findings."""
        files = [
            FIXTURES / "vulnerable_secrets.py",
            FIXTURES / "vulnerable_injection.py",
        ]
        findings = run_all_checks(files)
        # Should have findings from both files
        assert len(findings) >= 3
        checks = {f.check for f in findings}
        assert "hardcoded_secret" in checks

    def test_returns_empty_for_clean_code(self):
        """Should return empty list for clean code."""
        files = [FIXTURES / "clean_code.py"]
        findings = run_all_checks(files)
        assert len(findings) == 0
```

**Step 3: Run test to verify it fails**

```bash
pytest tests/test_security/test_checks.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'src.security.checks'`

**Step 4: Write implementation**

Create `src/security/checks.py`:

```python
"""Security check implementations for the auditor."""
import re
from pathlib import Path
from typing import Callable

from .severity import Severity, Finding

# Patterns for secret detection
SECRET_PATTERNS = [
    (r'["\']sk-ant-[a-zA-Z0-9-]+["\']', "Anthropic API key"),
    (r'["\']sk-[a-zA-Z0-9]{48,}["\']', "OpenAI API key"),
    (r'["\']ghp_[a-zA-Z0-9]{36,}["\']', "GitHub personal access token"),
    (r'["\']gho_[a-zA-Z0-9]{36,}["\']', "GitHub OAuth token"),
    (r'(?i)(password|passwd|pwd)\s*=\s*["\'][^"\']+["\']', "Hardcoded password"),
    (r'(?i)(api_key|apikey|api-key)\s*=\s*["\'][^"\']{10,}["\']', "Hardcoded API key"),
    (r'(?i)(secret|token)\s*=\s*["\'][^"\']{10,}["\']', "Hardcoded secret/token"),
]

# Patterns for injection vulnerabilities
INJECTION_PATTERNS = [
    (r'os\.system\s*\(', "os.system() call - potential command injection"),
    (r'subprocess\.call\s*\([^)]*shell\s*=\s*True', "subprocess with shell=True"),
    (r'subprocess\.run\s*\([^)]*shell\s*=\s*True', "subprocess.run with shell=True"),
    (r'(?<![a-zA-Z_])eval\s*\(', "eval() call - code execution risk"),
    (r'(?<![a-zA-Z_])exec\s*\(', "exec() call - code execution risk"),
]

# Patterns for path traversal
PATH_PATTERNS = [
    (r'open\s*\(\s*f["\'][^"\']*\{[^}]+\}', "f-string in file path - potential traversal"),
    (r'Path\s*\(\s*f["\'][^"\']*\{[^}]+\}', "f-string in Path() - potential traversal"),
]


def _scan_file_for_patterns(
    file_path: Path,
    patterns: list[tuple[str, str]],
    severity: Severity,
    check_name: str,
) -> list[Finding]:
    """Scan a file for regex patterns and return findings."""
    findings = []
    try:
        content = file_path.read_text()
        lines = content.split("\n")

        for line_num, line in enumerate(lines, start=1):
            # Skip comments
            stripped = line.strip()
            if stripped.startswith("#"):
                continue

            for pattern, description in patterns:
                if re.search(pattern, line):
                    findings.append(
                        Finding(
                            severity=severity,
                            file=str(file_path),
                            line=line_num,
                            check=check_name,
                            message=description,
                            recommendation=f"Review and fix: {description}",
                            snippet=line.strip()[:100],
                        )
                    )
    except Exception:
        pass  # Skip files that can't be read

    return findings


def check_secrets(file_path: Path) -> list[Finding]:
    """Check for hardcoded secrets in a file."""
    return _scan_file_for_patterns(
        file_path,
        SECRET_PATTERNS,
        Severity.CRITICAL,
        "hardcoded_secret",
    )


def check_injection(file_path: Path) -> list[Finding]:
    """Check for injection vulnerabilities in a file."""
    return _scan_file_for_patterns(
        file_path,
        INJECTION_PATTERNS,
        Severity.CRITICAL,
        "injection",
    )


def check_path_traversal(file_path: Path) -> list[Finding]:
    """Check for path traversal vulnerabilities in a file."""
    return _scan_file_for_patterns(
        file_path,
        PATH_PATTERNS,
        Severity.HIGH,
        "path_traversal",
    )


# Registry of all checks
ALL_CHECKS: list[Callable[[Path], list[Finding]]] = [
    check_secrets,
    check_injection,
    check_path_traversal,
]


def run_all_checks(files: list[Path]) -> list[Finding]:
    """Run all security checks on a list of files."""
    findings = []
    for file_path in files:
        if not file_path.suffix == ".py":
            continue
        for check in ALL_CHECKS:
            findings.extend(check(file_path))
    return findings
```

**Step 5: Update `src/security/__init__.py`**

```python
"""Security auditor module for Eva."""
from .severity import Severity, Finding
from .checks import (
    check_secrets,
    check_injection,
    check_path_traversal,
    run_all_checks,
)

__all__ = [
    "Severity",
    "Finding",
    "check_secrets",
    "check_injection",
    "check_path_traversal",
    "run_all_checks",
]
```

**Step 6: Run test to verify it passes**

```bash
pytest tests/test_security/test_checks.py -v
```

Expected: All tests PASS

**Step 7: Commit**

```bash
git add src/security/ tests/test_security/
git commit -m "feat(security): add pattern-based security checks"
```

---

## Task 3: Implement Auditor Core with Claude API

**Files:**
- Create: `src/security/auditor.py`
- Test: `tests/test_security/test_auditor.py`

**Step 1: Write failing test**

Create `tests/test_security/test_auditor.py`:

```python
"""Tests for security auditor core module."""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.security.auditor import SecurityAuditor, AuditResult
from src.security.severity import Severity, Finding

FIXTURES = Path(__file__).parent / "fixtures"


class TestAuditResult:
    def test_has_critical(self):
        """Should detect if any finding is critical."""
        findings = [
            Finding(Severity.HIGH, "a.py", 1, "test", "msg", "rec"),
            Finding(Severity.CRITICAL, "b.py", 2, "test", "msg", "rec"),
        ]
        result = AuditResult(findings=findings, files_scanned=2, approach="native")
        assert result.has_critical is True
        assert result.should_block is True

    def test_no_critical(self):
        """Should return False when no critical findings."""
        findings = [
            Finding(Severity.MEDIUM, "a.py", 1, "test", "msg", "rec"),
        ]
        result = AuditResult(findings=findings, files_scanned=1, approach="native")
        assert result.has_critical is False
        assert result.should_block is False

    def test_to_json(self):
        """Should serialize to JSON-compatible dict."""
        result = AuditResult(findings=[], files_scanned=5, approach="native")
        d = result.to_json()
        assert d["files_scanned"] == 5
        assert d["approach"] == "native"
        assert "timestamp" in d


class TestSecurityAuditor:
    def test_scan_files_pattern_based(self):
        """Should find issues using pattern-based checks."""
        auditor = SecurityAuditor(use_llm=False)
        files = [FIXTURES / "vulnerable_secrets.py"]
        result = auditor.scan_files(files)
        assert result.files_scanned == 1
        assert len(result.findings) >= 1

    @patch("src.security.auditor.anthropic")
    def test_scan_files_with_llm(self, mock_anthropic):
        """Should call Claude API when use_llm=True."""
        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text='{"findings": []}')]
        )

        auditor = SecurityAuditor(use_llm=True)
        files = [FIXTURES / "clean_code.py"]
        result = auditor.scan_files(files)
        assert result.files_scanned == 1
        mock_client.messages.create.assert_called_once()

    def test_scan_directory(self):
        """Should scan all Python files in a directory."""
        auditor = SecurityAuditor(use_llm=False)
        result = auditor.scan_directory(FIXTURES)
        assert result.files_scanned >= 4  # All fixture files
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_security/test_auditor.py -v
```

Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write implementation**

Create `src/security/auditor.py`:

```python
"""Core security auditor with optional LLM enhancement."""
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import anthropic

from .severity import Severity, Finding
from .checks import run_all_checks


AUDIT_SYSTEM_PROMPT = """You are a security auditor for Python code. Analyze the provided code for security vulnerabilities.

Focus on:
1. Hardcoded secrets (API keys, passwords, tokens)
2. Injection vulnerabilities (command, SQL, prompt injection)
3. Path traversal risks
4. Unsafe code execution (eval, exec)
5. Missing input validation
6. AI/LLM-specific risks (prompt injection, output trust)

Return your findings as JSON:
{
  "findings": [
    {
      "severity": "critical|high|medium|low",
      "file": "path/to/file.py",
      "line": 42,
      "check": "check_name",
      "message": "Description of the issue",
      "recommendation": "How to fix it"
    }
  ]
}

If no issues found, return: {"findings": []}
"""


@dataclass
class AuditResult:
    """Result of a security audit."""

    findings: list[Finding]
    files_scanned: int
    approach: str  # "native" or "agentic"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def has_critical(self) -> bool:
        """Check if any finding is critical severity."""
        return any(f.severity == Severity.CRITICAL for f in self.findings)

    @property
    def has_high(self) -> bool:
        """Check if any finding is high severity."""
        return any(f.severity == Severity.HIGH for f in self.findings)

    @property
    def should_block(self) -> bool:
        """Check if findings should block PR merge."""
        return any(f.severity.blocks_merge for f in self.findings)

    @property
    def needs_immediate_notify(self) -> bool:
        """Check if any finding needs immediate notification."""
        return any(f.severity.immediate_notify for f in self.findings)

    def to_json(self) -> dict:
        """Serialize to JSON-compatible dict."""
        return {
            "findings": [f.to_dict() for f in self.findings],
            "files_scanned": self.files_scanned,
            "approach": self.approach,
            "timestamp": self.timestamp.isoformat(),
            "summary": {
                "critical": sum(1 for f in self.findings if f.severity == Severity.CRITICAL),
                "high": sum(1 for f in self.findings if f.severity == Severity.HIGH),
                "medium": sum(1 for f in self.findings if f.severity == Severity.MEDIUM),
                "low": sum(1 for f in self.findings if f.severity == Severity.LOW),
            },
        }


class SecurityAuditor:
    """Security auditor with pattern-based and optional LLM analysis."""

    def __init__(self, use_llm: bool = True):
        """Initialize auditor.

        Args:
            use_llm: Whether to use Claude API for enhanced analysis.
        """
        self.use_llm = use_llm
        self._client: Optional[anthropic.Anthropic] = None

    @property
    def client(self) -> anthropic.Anthropic:
        """Lazy-load Anthropic client."""
        if self._client is None:
            self._client = anthropic.Anthropic()
        return self._client

    def scan_files(self, files: list[Path]) -> AuditResult:
        """Scan a list of files for security issues.

        Args:
            files: List of file paths to scan.

        Returns:
            AuditResult with findings.
        """
        # Always run pattern-based checks
        findings = run_all_checks(files)

        # Optionally enhance with LLM analysis
        if self.use_llm and files:
            llm_findings = self._llm_scan(files)
            findings = self._merge_findings(findings, llm_findings)

        return AuditResult(
            findings=findings,
            files_scanned=len(files),
            approach="native",
        )

    def scan_directory(self, directory: Path) -> AuditResult:
        """Scan all Python files in a directory.

        Args:
            directory: Directory to scan.

        Returns:
            AuditResult with findings.
        """
        files = list(directory.rglob("*.py"))
        return self.scan_files(files)

    def _llm_scan(self, files: list[Path]) -> list[Finding]:
        """Use Claude to analyze files for security issues."""
        # Prepare code content
        code_parts = []
        for f in files[:10]:  # Limit to 10 files per call
            try:
                content = f.read_text()
                code_parts.append(f"# File: {f}\n{content}")
            except Exception:
                continue

        if not code_parts:
            return []

        code_content = "\n\n---\n\n".join(code_parts)

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=AUDIT_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": code_content}],
            )

            # Parse response
            text = response.content[0].text
            data = json.loads(text)
            return [Finding.from_dict(f) for f in data.get("findings", [])]

        except Exception:
            return []  # Fallback to pattern-only on error

    def _merge_findings(
        self, pattern_findings: list[Finding], llm_findings: list[Finding]
    ) -> list[Finding]:
        """Merge findings from pattern and LLM, deduplicating."""
        # Use (file, line, check) as dedup key
        seen = set()
        merged = []

        for f in pattern_findings:
            key = (f.file, f.line, f.check)
            if key not in seen:
                seen.add(key)
                merged.append(f)

        for f in llm_findings:
            key = (f.file, f.line, f.check)
            if key not in seen:
                seen.add(key)
                merged.append(f)

        return merged
```

**Step 4: Update `src/security/__init__.py`**

```python
"""Security auditor module for Eva."""
from .severity import Severity, Finding
from .checks import (
    check_secrets,
    check_injection,
    check_path_traversal,
    run_all_checks,
)
from .auditor import SecurityAuditor, AuditResult

__all__ = [
    "Severity",
    "Finding",
    "check_secrets",
    "check_injection",
    "check_path_traversal",
    "run_all_checks",
    "SecurityAuditor",
    "AuditResult",
]
```

**Step 5: Run test to verify it passes**

```bash
pytest tests/test_security/test_auditor.py -v
```

Expected: All tests PASS

**Step 6: Commit**

```bash
git add src/security/ tests/test_security/
git commit -m "feat(security): add core auditor with Claude API integration"
```

---

## Task 4: Implement Reporter for PR Comments and Issues

**Files:**
- Create: `src/security/reporter.py`
- Test: `tests/test_security/test_reporter.py`

**Step 1: Write failing test**

Create `tests/test_security/test_reporter.py`:

```python
"""Tests for security reporter module."""
import pytest
from src.security.reporter import format_pr_comment, format_issue_body, format_email
from src.security.severity import Severity, Finding
from src.security.auditor import AuditResult


@pytest.fixture
def sample_findings():
    return [
        Finding(Severity.CRITICAL, "src/agent.py", 42, "hardcoded_secret", "API key found", "Use env var"),
        Finding(Severity.HIGH, "src/tools.py", 10, "injection", "eval() detected", "Remove eval"),
        Finding(Severity.MEDIUM, "src/memory.py", 5, "code_quality", "Broad exception", "Catch specific"),
    ]


@pytest.fixture
def sample_result(sample_findings):
    return AuditResult(findings=sample_findings, files_scanned=3, approach="native")


class TestFormatPRComment:
    def test_includes_header(self, sample_result):
        """Should include labeled header."""
        comment = format_pr_comment(sample_result)
        assert "Security Audit [Native]" in comment

    def test_includes_findings_table(self, sample_result):
        """Should format findings as markdown table."""
        comment = format_pr_comment(sample_result)
        assert "| Severity |" in comment
        assert "CRITICAL" in comment
        assert "src/agent.py:42" in comment

    def test_includes_summary(self, sample_result):
        """Should include severity summary."""
        comment = format_pr_comment(sample_result)
        assert "1 critical" in comment.lower()
        assert "1 high" in comment.lower()

    def test_block_recommendation(self, sample_result):
        """Should recommend BLOCK when critical/high found."""
        comment = format_pr_comment(sample_result)
        assert "BLOCK" in comment

    def test_approve_for_clean(self):
        """Should recommend APPROVE when no blocking issues."""
        result = AuditResult(findings=[], files_scanned=5, approach="native")
        comment = format_pr_comment(result)
        assert "No security issues detected" in comment


class TestFormatIssueBody:
    def test_includes_scan_metadata(self, sample_result):
        """Should include scan type and date."""
        body = format_issue_body(sample_result, scan_type="scheduled")
        assert "Scheduled" in body
        assert "Files analyzed: 3" in body

    def test_formats_all_findings(self, sample_result):
        """Should list all findings."""
        body = format_issue_body(sample_result, scan_type="scheduled")
        assert "src/agent.py" in body
        assert "src/tools.py" in body


class TestFormatEmail:
    def test_critical_email_subject(self, sample_findings):
        """Should format critical finding for immediate email."""
        finding = sample_findings[0]  # Critical
        subject, body = format_email(finding, pr_number=42, pr_url="https://example.com")
        assert "Critical" in subject
        assert "hardcoded_secret" in subject
        assert "PR #42" in body

    def test_email_includes_action(self, sample_findings):
        """Should include action required."""
        finding = sample_findings[0]
        subject, body = format_email(finding, pr_number=42, pr_url="https://example.com")
        assert "blocked" in body.lower()
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_security/test_reporter.py -v
```

Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write implementation**

Create `src/security/reporter.py`:

```python
"""Formatters for security audit output."""
from datetime import datetime
from typing import Optional

from .severity import Severity, Finding
from .auditor import AuditResult


def format_pr_comment(result: AuditResult) -> str:
    """Format audit result as PR comment markdown.

    Args:
        result: The audit result.

    Returns:
        Markdown-formatted PR comment.
    """
    label = "Native" if result.approach == "native" else "Agentic"

    if not result.findings:
        return f"### ✅ Security Audit [{label}]\n\nNo security issues detected.\n\n**Files analyzed:** {result.files_scanned}"

    lines = [
        f"### 🔒 Security Audit [{label}]",
        "",
        f"**Scan type:** PR",
        f"**Files analyzed:** {result.files_scanned}",
        "",
        "#### Findings",
        "",
        "| Severity | File:Line | Issue | Recommendation |",
        "|----------|-----------|-------|----------------|",
    ]

    for f in sorted(result.findings, key=lambda x: -x.severity):
        severity = f.severity.name
        file_line = f"{f.file}:{f.line}"
        lines.append(f"| {severity} | {file_line} | {f.message} | {f.recommendation} |")

    summary = result.to_json()["summary"]
    lines.extend([
        "",
        "#### Summary",
        "",
        f"- {summary['critical']} critical, {summary['high']} high, {summary['medium']} medium, {summary['low']} low findings",
        f"- **Merge recommendation:** {'BLOCK' if result.should_block else 'APPROVE'}",
    ])

    return "\n".join(lines)


def format_issue_body(result: AuditResult, scan_type: str = "scheduled") -> str:
    """Format audit result as GitHub issue body.

    Args:
        result: The audit result.
        scan_type: Type of scan (scheduled, push, etc.)

    Returns:
        Markdown-formatted issue body.
    """
    label = "Native" if result.approach == "native" else "Agentic"
    date = result.timestamp.strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        f"## Security Audit [{label}] - {scan_type.title()}",
        "",
        f"**Date:** {date}",
        f"**Files analyzed:** {result.files_scanned}",
        "",
    ]

    if not result.findings:
        lines.append("✅ No security issues detected.")
        return "\n".join(lines)

    summary = result.to_json()["summary"]
    lines.extend([
        "### Summary",
        "",
        f"- Critical: {summary['critical']}",
        f"- High: {summary['high']}",
        f"- Medium: {summary['medium']}",
        f"- Low: {summary['low']}",
        "",
        "### Findings",
        "",
        "| Severity | File:Line | Issue | Recommendation |",
        "|----------|-----------|-------|----------------|",
    ])

    for f in sorted(result.findings, key=lambda x: -x.severity):
        file_line = f"{f.file}:{f.line}"
        lines.append(f"| {f.severity.name} | {file_line} | {f.message} | {f.recommendation} |")

    return "\n".join(lines)


def format_email(
    finding: Finding,
    pr_number: Optional[int] = None,
    pr_url: Optional[str] = None,
) -> tuple[str, str]:
    """Format a critical finding as email subject and body.

    Args:
        finding: The critical finding.
        pr_number: PR number if applicable.
        pr_url: PR URL if applicable.

    Returns:
        Tuple of (subject, body).
    """
    subject = f"🚨 [Eva Security] Critical: {finding.check} in {finding.file}"

    lines = [
        f"**Severity:** {finding.severity.name}",
        f"**File:** {finding.file}:{finding.line}",
        f"**Check:** {finding.check}",
        "",
        "**Finding:**",
        f"> {finding.message}",
        "",
        f"**Recommendation:** {finding.recommendation}",
        "",
    ]

    if finding.snippet:
        lines.extend([
            "**Code snippet:**",
            f"```python",
            finding.snippet,
            "```",
            "",
        ])

    if pr_number:
        lines.extend([
            f"**Action Required:** PR #{pr_number} is blocked until resolved.",
        ])
        if pr_url:
            lines.append(f"**View PR:** {pr_url}")

    body = "\n".join(lines)
    return subject, body


def format_digest(
    native_result: Optional[AuditResult],
    agentic_result: Optional[AuditResult],
    date: datetime,
) -> tuple[str, str]:
    """Format daily digest email comparing both approaches.

    Args:
        native_result: Results from native approach (or None).
        agentic_result: Results from agentic approach (or None).
        date: Date of the digest.

    Returns:
        Tuple of (subject, body).
    """
    date_str = date.strftime("%b %d, %Y")
    subject = f"[Eva Security] Daily Digest - {date_str}"

    lines = [
        "## Security Audit Daily Digest",
        "",
        f"**Date:** {date_str}",
        "",
    ]

    if native_result:
        summary = native_result.to_json()["summary"]
        lines.extend([
            "### Native Approach",
            "",
            f"- Files scanned: {native_result.files_scanned}",
            f"- Findings: {summary['critical']} critical, {summary['high']} high, "
            f"{summary['medium']} medium, {summary['low']} low",
            "",
        ])

    if agentic_result:
        summary = agentic_result.to_json()["summary"]
        lines.extend([
            "### Agentic Approach",
            "",
            f"- Files scanned: {agentic_result.files_scanned}",
            f"- Findings: {summary['critical']} critical, {summary['high']} high, "
            f"{summary['medium']} medium, {summary['low']} low",
            "",
        ])

    body = "\n".join(lines)
    return subject, body
```

**Step 4: Update `src/security/__init__.py`**

```python
"""Security auditor module for Eva."""
from .severity import Severity, Finding
from .checks import (
    check_secrets,
    check_injection,
    check_path_traversal,
    run_all_checks,
)
from .auditor import SecurityAuditor, AuditResult
from .reporter import format_pr_comment, format_issue_body, format_email, format_digest

__all__ = [
    "Severity",
    "Finding",
    "check_secrets",
    "check_injection",
    "check_path_traversal",
    "run_all_checks",
    "SecurityAuditor",
    "AuditResult",
    "format_pr_comment",
    "format_issue_body",
    "format_email",
    "format_digest",
]
```

**Step 5: Run test to verify it passes**

```bash
pytest tests/test_security/test_reporter.py -v
```

Expected: All tests PASS

**Step 6: Commit**

```bash
git add src/security/ tests/test_security/
git commit -m "feat(security): add reporter for PR comments, issues, and emails"
```

---

## Task 5: Create Native GitHub Actions Workflow

**Files:**
- Create: `.github/workflows/security-native.yml`

**Step 1: Write the workflow file**

Create `.github/workflows/security-native.yml`:

```yaml
name: Security Audit (Native)

on:
  pull_request:
    types: [opened, synchronize]
  push:
    branches: [main]
  schedule:
    - cron: '0 0 * * *'  # 2am SAST (midnight UTC)
  workflow_dispatch:

concurrency:
  group: security-native-${{ github.ref }}
  cancel-in-progress: true

env:
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  COMPOSIO_API_KEY: ${{ secrets.COMPOSIO_API_KEY }}

jobs:
  audit:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
      issues: write
      statuses: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Need history for diff

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .

      - name: Get changed files (PR/push)
        id: changed
        if: github.event_name == 'pull_request' || github.event_name == 'push'
        run: |
          if [ "${{ github.event_name }}" == "pull_request" ]; then
            BASE=${{ github.event.pull_request.base.sha }}
            HEAD=${{ github.event.pull_request.head.sha }}
          else
            BASE=${{ github.event.before }}
            HEAD=${{ github.event.after }}
          fi
          FILES=$(git diff --name-only --diff-filter=ACMRT $BASE $HEAD | grep '\.py$' | tr '\n' ' ' || true)
          echo "files=$FILES" >> $GITHUB_OUTPUT

      - name: Run security audit
        id: audit
        run: |
          python -c "
          import json
          import os
          import sys
          from pathlib import Path
          from src.security import SecurityAuditor, format_pr_comment, format_issue_body

          event = os.environ.get('GITHUB_EVENT_NAME', 'workflow_dispatch')
          files_str = '${{ steps.changed.outputs.files }}'.strip()

          auditor = SecurityAuditor(use_llm=True)

          if event == 'schedule' or not files_str:
              # Full repo scan
              result = auditor.scan_directory(Path('src'))
              scan_type = 'scheduled'
          else:
              # Scan only changed files
              files = [Path(f) for f in files_str.split() if f]
              result = auditor.scan_files(files)
              scan_type = 'pr' if event == 'pull_request' else 'push'

          # Output for subsequent steps
          output = result.to_json()
          output['scan_type'] = scan_type
          output['pr_comment'] = format_pr_comment(result)
          output['issue_body'] = format_issue_body(result, scan_type)

          # Write to file for artifact
          Path('.github/security-findings').mkdir(parents=True, exist_ok=True)
          with open('.github/security-findings/native-latest.json', 'w') as f:
              json.dump(output, f, indent=2)

          # Set outputs
          with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
              f.write(f'should_block={str(result.should_block).lower()}\n')
              f.write(f'has_critical={str(result.has_critical).lower()}\n')
              f.write(f'finding_count={len(result.findings)}\n')

          print(output['pr_comment'])
          "

      - name: Post PR comment
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const data = JSON.parse(fs.readFileSync('.github/security-findings/native-latest.json', 'utf8'));

            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: data.pr_comment
            });

      - name: Set commit status
        if: github.event_name == 'pull_request' || github.event_name == 'push'
        uses: actions/github-script@v7
        with:
          script: |
            const shouldBlock = '${{ steps.audit.outputs.should_block }}' === 'true';
            await github.rest.repos.createCommitStatus({
              owner: context.repo.owner,
              repo: context.repo.repo,
              sha: context.sha,
              state: shouldBlock ? 'failure' : 'success',
              context: 'Security Audit (Native)',
              description: shouldBlock ? 'Security issues found - merge blocked' : 'No blocking security issues'
            });

      - name: Create issue for scheduled scan
        if: github.event_name == 'schedule' && steps.audit.outputs.finding_count != '0'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const data = JSON.parse(fs.readFileSync('.github/security-findings/native-latest.json', 'utf8'));
            const date = new Date().toISOString().split('T')[0];

            await github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: `Security Audit [Native] - ${date}`,
              body: data.issue_body,
              labels: ['security-audit', 'native']
            });

      - name: Send critical notification
        if: steps.audit.outputs.has_critical == 'true'
        run: |
          python -c "
          import json
          from pathlib import Path
          from src.security import Finding, format_email
          from src.composio_tools import send_email

          data = json.loads(Path('.github/security-findings/native-latest.json').read_text())
          critical = [f for f in data['findings'] if f['severity'] == 'critical']

          if critical:
              finding = Finding.from_dict(critical[0])
              pr_number = ${{ github.event.pull_request.number || 0 }}
              pr_url = '${{ github.event.pull_request.html_url }}' or None
              subject, body = format_email(finding, pr_number, pr_url)
              send_email('${{ secrets.NOTIFY_EMAIL }}', subject, body)
          "

      - name: Upload findings artifact
        uses: actions/upload-artifact@v4
        with:
          name: security-findings-native
          path: .github/security-findings/native-latest.json
          retention-days: 30
```

**Step 2: Verify YAML syntax**

```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/security-native.yml'))"
```

Expected: No output (valid YAML)

**Step 3: Commit**

```bash
git add .github/workflows/security-native.yml
git commit -m "feat(security): add native GitHub Actions workflow"
```

---

## Task 6: Create Agentic Workflow Definition

**Files:**
- Create: `.github/workflows/security-agent.md`

**Step 1: Write the agentic workflow definition**

Create `.github/workflows/security-agent.md`:

```markdown
---
name: Security Auditor (Agentic)
permissions:
  contents: read
  pull-requests: write
  issues: write
provider: copilot
triggers:
  pull_request:
    types: [opened, synchronize]
  push:
    branches: [main]
  schedule:
    - cron: '0 0 * * *'
  workflow_dispatch:
---

# Security Auditor

You are a security auditor for the Eva orchestrator codebase. Your job is to analyze code changes for security vulnerabilities with expert-level judgment.

## Your Expertise

You are an expert in:
- OWASP Top 10 vulnerabilities (injection, XSS, auth flaws, etc.)
- Python security best practices
- AI/LLM-specific risks (prompt injection, unsafe eval, output trust)
- Secret detection and credential hygiene
- Path traversal and file system security

## What to Analyze

**For pull requests:** Analyze only the changed files in the PR diff.
**For push to main:** Analyze only the changed files in the commit.
**For scheduled runs:** Analyze the entire `src/` directory.

## Security Checks

Evaluate each file for these issues, in order of severity:

### CRITICAL Severity
1. **Hardcoded Secrets**: API keys, passwords, tokens in source code
   - Look for: `sk-`, `ghp_`, `password=`, `token=`, `api_key=`
   - Exception: `os.environ.get()` is safe

2. **Injection Vulnerabilities**:
   - Command injection: `os.system()`, `subprocess.call(..., shell=True)`
   - Code execution: `eval()`, `exec()` with user input
   - SQL injection: String concatenation in queries

3. **Authentication/Authorization Flaws**:
   - Missing auth checks on sensitive operations
   - Hardcoded credentials

### HIGH Severity
4. **Input Validation**:
   - Unvalidated user/external input passed to file operations
   - Missing type checks on API inputs

5. **Path Traversal**:
   - User input in file paths without sanitization
   - f-strings or format strings with user data in `open()` or `Path()`

6. **Unsafe Execution**:
   - `eval()`, `exec()` even without direct user input
   - `subprocess` with shell=True

7. **Dependency Issues**:
   - Known vulnerable package versions in requirements.txt/pyproject.toml

### MEDIUM Severity
8. **Error Handling**:
   - Broad `except:` or `except Exception:` that swallows errors
   - Stack traces exposed to users
   - Sensitive data in error messages

9. **AI-Specific Risks**:
   - LLM output used directly without validation
   - Prompt templates with unsanitized user input

### LOW Severity
10. **Code Quality**:
    - Hardcoded values that should be configuration
    - Missing input validation on internal functions

## Output Format

Post a PR comment with this exact structure:

```
### 🔒 Security Audit [Agentic]

**Scan type:** PR #X / Push / Scheduled
**Files analyzed:** X

#### Findings

| Severity | File:Line | Issue | Recommendation |
|----------|-----------|-------|----------------|
| CRITICAL | path/file.py:42 | Hardcoded API key | Use os.environ.get() |

#### Summary

- X critical, Y high, Z medium, W low findings
- **Merge recommendation:** BLOCK / APPROVE
```

If no issues found, post:
```
### ✅ Security Audit [Agentic]

No security issues detected.

**Files analyzed:** X
```

## Important Guidelines

1. **Be thorough but avoid false positives** - Only flag real security issues
2. **Provide actionable recommendations** - Tell developers HOW to fix issues
3. **Consider context** - A pattern in test fixtures is different from production code
4. **Include code snippets** - Quote the problematic line when helpful
5. **BLOCK recommendation** - Use when ANY critical or high severity issues found
6. **APPROVE recommendation** - Use when only medium/low or no issues found

## For Scheduled Scans

Create a GitHub Issue instead of a PR comment with title:
`Security Audit [Agentic] - YYYY-MM-DD`

Add labels: `security-audit`, `agentic`
```

**Step 2: Commit the definition**

```bash
git add .github/workflows/security-agent.md
git commit -m "feat(security): add agentic workflow definition"
```

**Step 3: Install gh aw extension and compile**

```bash
gh extension install github/gh-agentic-workflows
gh aw compile
```

Expected: Creates `.github/workflows/security-agent.lo.yml`

**Step 4: Commit compiled workflow**

```bash
git add .github/workflows/security-agent.lo.yml .github/AW/
git commit -m "feat(security): compile agentic workflow to locked YAML"
```

---

## Task 7: Create Digest Workflow for Daily Email

**Files:**
- Create: `.github/workflows/security-digest.yml`

**Step 1: Write the digest workflow**

Create `.github/workflows/security-digest.yml`:

```yaml
name: Security Digest

on:
  schedule:
    - cron: '0 4 * * *'  # 6am SAST (4am UTC)
  workflow_dispatch:

env:
  COMPOSIO_API_KEY: ${{ secrets.COMPOSIO_API_KEY }}

jobs:
  digest:
    runs-on: ubuntu-latest

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

      - name: Download recent artifacts
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const path = require('path');

            // Get artifacts from last 24 hours
            const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();

            const artifacts = await github.rest.actions.listArtifactsForRepo({
              owner: context.repo.owner,
              repo: context.repo.repo,
              per_page: 100
            });

            const securityArtifacts = artifacts.data.artifacts.filter(a =>
              a.name.startsWith('security-findings-') &&
              new Date(a.created_at) > new Date(yesterday)
            );

            fs.mkdirSync('.github/security-findings', { recursive: true });

            for (const artifact of securityArtifacts) {
              const download = await github.rest.actions.downloadArtifact({
                owner: context.repo.owner,
                repo: context.repo.repo,
                artifact_id: artifact.id,
                archive_format: 'zip'
              });

              const fileName = `${artifact.name}.zip`;
              fs.writeFileSync(fileName, Buffer.from(download.data));

              // Extract (simplified - in practice use unzip)
              console.log(`Downloaded: ${artifact.name}`);
            }

      - name: Compile and send digest
        run: |
          python -c "
          import json
          from datetime import datetime
          from pathlib import Path
          from src.security import format_digest, AuditResult, Finding
          from src.composio_tools import send_email

          findings_dir = Path('.github/security-findings')
          native_findings = []
          agentic_findings = []

          # Load findings from artifacts
          for f in findings_dir.glob('*.json'):
              try:
                  data = json.loads(f.read_text())
                  if 'native' in f.name:
                      native_findings.append(data)
                  elif 'agentic' in f.name:
                      agentic_findings.append(data)
              except Exception:
                  continue

          # Aggregate findings
          def aggregate(findings_list):
              if not findings_list:
                  return None
              all_findings = []
              total_files = 0
              for data in findings_list:
                  all_findings.extend([Finding.from_dict(f) for f in data.get('findings', [])])
                  total_files += data.get('files_scanned', 0)
              return AuditResult(findings=all_findings, files_scanned=total_files, approach=findings_list[0].get('approach', 'unknown'))

          native_result = aggregate(native_findings)
          agentic_result = aggregate(agentic_findings)

          if native_result or agentic_result:
              subject, body = format_digest(native_result, agentic_result, datetime.now())
              send_email('${{ secrets.NOTIFY_EMAIL }}', subject, body)
              print(f'Sent digest: {subject}')
          else:
              print('No findings to report')
          "
```

**Step 2: Commit**

```bash
git add .github/workflows/security-digest.yml
git commit -m "feat(security): add daily digest workflow"
```

---

## Task 8: Create Comparison Tracking Document

**Files:**
- Create: `docs/security-audit-comparison.md`

**Step 1: Write initial tracking document**

Create `docs/security-audit-comparison.md`:

```markdown
# Security Auditor Comparison - Evaluation Log

**Comparison Period:** 2026-02-24 to 2026-03-10 (2 weeks)
**Status:** In Progress

## Approach Summary

| Approach | Implementation | AI Provider |
|----------|---------------|-------------|
| Native | Python + Claude API | Anthropic Claude Sonnet |
| Agentic | gh aw markdown | GitHub Copilot |

## Evaluation Metrics

| Metric | Native | Agentic | Notes |
|--------|--------|---------|-------|
| True Positives | - | - | Real issues found |
| False Positives | - | - | Non-issues flagged |
| Missed Issues | - | - | Found later |
| Avg Latency | - | - | Workflow duration |
| Avg Cost | - | - | API calls/tokens |

## Weekly Observations

### Week 1 (2026-02-24 - 2026-03-02)

_To be filled during evaluation_

**PRs Scanned:** -
**Agreements:** - (both found same issue)
**Native Only:** - (native found, agentic missed)
**Agentic Only:** - (agentic found, native missed)
**False Positives:** -

### Week 2 (2026-03-03 - 2026-03-10)

_To be filled during evaluation_

## Finding Log

| Date | PR/Commit | Native Finding | Agentic Finding | Actual Issue? |
|------|-----------|----------------|-----------------|---------------|
| | | | | |

## Comparison Notes

_Document interesting observations, disagreements between approaches, etc._

## Final Recommendation

_To be completed at end of comparison period_

**Recommended approach:**
**Rationale:**
```

**Step 2: Commit**

```bash
git add docs/security-audit-comparison.md
git commit -m "docs: add security audit comparison tracking template"
```

---

## Task 9: Run All Tests and Verify

**Step 1: Run full test suite**

```bash
pytest tests/ -v --cov=src/security --cov-report=term-missing
```

Expected: All tests PASS with good coverage

**Step 2: Test native workflow locally (dry run)**

```bash
python -c "
from pathlib import Path
from src.security import SecurityAuditor, format_pr_comment

auditor = SecurityAuditor(use_llm=False)  # Skip API call for local test
result = auditor.scan_directory(Path('src'))
print(format_pr_comment(result))
"
```

Expected: Outputs formatted PR comment (may find some issues in existing code)

**Step 3: Commit any fixes**

If tests reveal issues, fix and commit:

```bash
git add -A
git commit -m "fix(security): address issues found in testing"
```

---

## Task 10: Final Push and Enable Workflows

**Step 1: Push all changes**

```bash
git push origin main
```

**Step 2: Verify workflows appear in GitHub Actions tab**

Navigate to: `https://github.com/safarivis/eva/actions`

Expected: See `Security Audit (Native)`, `Security Auditor (Agentic)`, `Security Digest`

**Step 3: Manually trigger test run**

```bash
gh workflow run "Security Audit (Native)" --ref main
gh workflow run "Security Auditor (Agentic)" --ref main
```

**Step 4: Verify both workflows complete**

```bash
gh run list --workflow="Security Audit (Native)" --limit=1
gh run list --workflow="Security Auditor (Agentic)" --limit=1
```

Expected: Both show "completed" status

**Step 5: Create test PR to verify PR triggers**

```bash
git checkout -b test/security-audit-verification
echo "# Test" >> README.md
git add README.md
git commit -m "test: verify security audit workflows"
git push -u origin test/security-audit-verification
gh pr create --title "Test: Security Audit Verification" --body "Testing parallel security auditors"
```

Expected: Both workflows trigger and post separate PR comments

**Step 6: Clean up test PR**

```bash
gh pr close --delete-branch
git checkout main
```

---

## Success Criteria Checklist

- [ ] `src/security/` module with severity, checks, auditor, reporter
- [ ] Tests in `tests/test_security/` with fixtures
- [ ] `.github/workflows/security-native.yml` - native approach
- [ ] `.github/workflows/security-agent.md` - agentic definition
- [ ] `.github/workflows/security-agent.lo.yml` - compiled agentic
- [ ] `.github/workflows/security-digest.yml` - daily digest
- [ ] `docs/security-audit-comparison.md` - tracking template
- [ ] Both workflows trigger on PR, push, schedule
- [ ] Both post separate labeled outputs
- [ ] Critical findings block PR merge
- [ ] All tests pass

---

*Plan created 2026-02-23. Ready for implementation.*
