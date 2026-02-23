# Security Auditor Design - Comparison Build

**Date:** 2026-02-23
**Status:** Approved
**Purpose:** Implement parallel Security Auditor using both native GitHub Actions and GitHub Agentic Workflows (`gh aw`) to compare approaches

---

## 1. Overview

Eva will gain a Security Auditor capability that runs two parallel implementations:
- **Native:** Python script + Claude API with structured checks
- **Agentic:** Markdown-defined agent compiled via `gh aw` extension

Both run on the same triggers and post separate results for direct comparison over a 2-week evaluation period.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SECURITY AUDITOR COMPARISON                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Triggers:                                                           │
│  ├── PR opened/synchronized                                          │
│  ├── Push to main                                                    │
│  └── Scheduled (daily 2am SAST / 0:00 UTC)                          │
│                                                                      │
│  ┌──────────────────────┐    ┌──────────────────────┐               │
│  │  NATIVE APPROACH     │    │  AGENTIC APPROACH    │               │
│  │  security-native.yml │    │  security-agent.md   │               │
│  │                      │    │  → compiled to       │               │
│  │  • Python script     │    │    security-agent    │               │
│  │  • Claude API call   │    │    .lo.yml           │               │
│  │  • Structured checks │    │                      │               │
│  │  • JSON output       │    │  • Natural language  │               │
│  └──────────┬───────────┘    │    instructions      │               │
│             │                │  • GitHub Copilot    │               │
│             │                └──────────┬───────────┘               │
│             │                           │                            │
│             └───────────┬───────────────┘                            │
│                         ▼                                            │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                      OUTPUTS                                 │    │
│  │                                                              │    │
│  │  PRs:       Two separate comments ([Native] and [Agentic])  │    │
│  │  Push:      Two separate commit status checks               │    │
│  │  Scheduled: Two separate GitHub Issues (labeled)            │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                         │                                            │
│                         ▼                                            │
│              ┌─────────────────────┐                                 │
│              │   NOTIFICATION      │                                 │
│              │   (Gmail via        │                                 │
│              │    Composio)        │                                 │
│              │                     │                                 │
│              │   Critical → Block  │                                 │
│              │   + Immediate email │                                 │
│              │                     │                                 │
│              │   Med/Low → Daily   │                                 │
│              │   digest at 6am     │                                 │
│              └─────────────────────┘                                 │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Security Checks Scope

Both implementations check the same categories for fair comparison:

| Category | Checks | Severity |
|----------|--------|----------|
| **Secrets** | API keys, tokens, passwords in code or config | Critical |
| **Injection** | SQL, command, prompt injection patterns | Critical |
| **OWASP Top 10** | XSS, auth flaws, sensitive data exposure, SSRF | Critical/High |
| **Dependencies** | Known CVEs in requirements.txt/pyproject.toml | High/Medium |
| **AI-Specific** | Unsafe eval/exec, prompt template injection, LLM output trust | High |
| **Eva-Specific** | Memory file path traversal, tool input validation, Composio key handling | High |
| **Code Quality** | Hardcoded values, missing input validation | Medium/Low |

### Severity → Action Mapping

| Severity | PR Action | Notification |
|----------|-----------|--------------|
| Critical | Block merge | Immediate Gmail |
| High | Block merge | Daily digest |
| Medium | PR comment only | Daily digest |
| Low | PR comment only | Weekly digest (or omit) |

---

## 4. File Structure

```
eva-orchestrator/
├── .github/
│   ├── workflows/
│   │   ├── security-native.yml      # Native approach workflow
│   │   ├── security-agent.md        # Agentic approach definition
│   │   ├── security-agent.lo.yml    # Compiled (generated by gh aw)
│   │   ├── security-digest.yml      # Daily/weekly digest emailer
│   │   └── ... (existing workflows)
│   └── security-findings/           # JSON artifacts for digest
│       ├── 2026-02-23-native.json
│       └── 2026-02-23-agentic.json
├── src/
│   └── security/
│       ├── __init__.py
│       ├── auditor.py               # Core audit logic
│       ├── checks.py                # Individual check implementations
│       ├── severity.py              # Severity classification
│       └── reporter.py              # PR comment / Issue formatter
├── tests/
│   └── test_security/
│       ├── test_auditor.py
│       ├── test_checks.py
│       └── fixtures/                # Sample vulnerable code snippets
└── docs/
    └── security-audit-comparison.md # Results tracking
```

---

## 5. Triggers & Configuration

### Trigger Matrix

| Trigger | Native | Agentic | Action |
|---------|--------|---------|--------|
| `pull_request: [opened, synchronize]` | ✓ | ✓ | Audit changed files only |
| `push: branches: [main]` | ✓ | ✓ | Audit changed files only |
| `schedule: cron '0 0 * * *'` (2am SAST) | ✓ | ✓ | Full repo scan |
| `workflow_dispatch` | ✓ | ✓ | Manual trigger for testing |

### Environment & Secrets

| Secret | Used By | Purpose |
|--------|---------|---------|
| `ANTHROPIC_API_KEY` | Native | Claude API for analysis |
| `GITHUB_TOKEN` | Both | PR comments, issues, status checks |
| `COMPOSIO_API_KEY` | Digest | Gmail notifications via Composio |
| (GitHub Copilot) | Agentic | Built-in to `gh aw` - no extra key |

### Concurrency Control

```yaml
concurrency:
  group: security-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

### Blocking Logic

```python
if any_finding.severity == "critical":
    set_commit_status("failure")  # Blocks merge
    send_immediate_gmail()
elif any_finding.severity == "high":
    set_commit_status("failure")  # Blocks merge
    queue_for_digest()
else:
    set_commit_status("success")  # Advisory only
    queue_for_digest()
```

---

## 6. Notification System

### Immediate Notifications (Critical only)

```
Subject: 🚨 [Eva Security] Critical: {check_name} in {file}

Body:
Severity: CRITICAL
File: src/tools.py:42
Check: Hardcoded API key detected
Approach: Native (or Agentic)

Finding:
> ANTHROPIC_API_KEY = "sk-ant-..."

Action Required: PR #{number} is blocked until resolved.
View PR: {link}
```

### Daily Digest (6am SAST)

```
Subject: [Eva Security] Daily Digest - Feb 23, 2026

Body:
## Summary
- PRs scanned: 3
- Push scans: 2
- Findings: 4 high, 7 medium, 12 low

## Native Approach Findings
| Severity | File:Line | Check | PR |
|----------|-----------|-------|-----|
| High | agent.py:89 | Missing input validation | #42 |
| Medium | tools.py:15 | Broad exception catch | #42 |

## Agentic Approach Findings
| Severity | File:Line | Check | PR |
|----------|-----------|-------|-----|
| High | agent.py:89 | Unvalidated user input | #42 |
| Medium | memory.py:23 | Path traversal risk | #43 |

## Comparison Notes
- Both caught agent.py issue (agreement)
- Agentic found memory.py issue Native missed
- Native had 1 false positive (flagged safe pattern)
```

---

## 7. Agentic Workflow Definition

`security-agent.md`:

```markdown
---
name: Security Auditor (Agentic)
permissions:
  contents: read
  pull-requests: write
  issues: write
provider: copilot
---

# Security Auditor

You are a security auditor for the Eva orchestrator codebase. Your job is to analyze code changes for security vulnerabilities.

## Your Expertise

You are an expert in:
- OWASP Top 10 vulnerabilities
- Python security best practices
- AI/LLM-specific risks (prompt injection, unsafe eval)
- Secret detection and credential hygiene

## What to Analyze

For pull requests: Analyze only the changed files.
For scheduled runs: Analyze the entire `src/` directory.

## Security Checks

Evaluate each file for:

1. **Secrets** (CRITICAL): API keys, tokens, passwords hardcoded in source
2. **Injection** (CRITICAL): SQL, command, or prompt injection vulnerabilities
3. **Auth Flaws** (CRITICAL): Missing authentication, broken access control
4. **Input Validation** (HIGH): Unvalidated user/external input
5. **Path Traversal** (HIGH): File path manipulation risks
6. **Unsafe Execution** (HIGH): eval(), exec(), subprocess with user input
7. **Dependency Issues** (HIGH): Known vulnerable packages
8. **Error Handling** (MEDIUM): Information leakage in errors
9. **Code Quality** (LOW): Hardcoded values, broad exceptions

## Output Format

Post a PR comment with this structure:

### 🔒 Security Audit [Agentic]

**Scan type:** PR #X / Push / Scheduled
**Files analyzed:** X

#### Findings

| Severity | File:Line | Issue | Recommendation |
|----------|-----------|-------|----------------|
| CRITICAL | ... | ... | ... |

#### Summary

- X critical, Y high, Z medium findings
- Merge recommendation: BLOCK / APPROVE

If no issues found, post: "✅ No security issues detected [Agentic]"
```

**Compilation:**

```bash
cd eva-orchestrator
gh aw compile
# Generates .github/workflows/security-agent.lo.yml
```

---

## 8. Evaluation Framework

### Comparison Period

2 weeks of parallel operation

### Metrics to Track

| Metric | How to Measure | Winner Criteria |
|--------|----------------|-----------------|
| **Detection Rate** | True positives found | More real issues caught |
| **False Positive Rate** | Issues flagged that weren't real | Fewer false alarms |
| **Missed Issues** | Bugs found later neither caught | Fewer misses |
| **Latency** | Workflow run duration | Faster feedback |
| **Cost** | API tokens/calls per scan | Lower cost |
| **Maintainability** | Ease of adding new checks | Simpler to extend |
| **Judgment Quality** | Context-awareness of findings | Better explanations |

### Decision Matrix

| Outcome | Action |
|---------|--------|
| Native clearly better | Archive agentic, use native |
| Agentic clearly better | Archive native, use agentic |
| Both have strengths | Hybrid approach |
| Neither adequate | Revisit scope/implementation |

### Checkpoints

- **Week 1:** Quick review - is one approach obviously failing?
- **Week 2:** Final evaluation and decision

### Final Deliverable

`docs/security-audit-comparison.md` with:
- Raw data (findings from each approach)
- Analysis of disagreements
- Recommendation with rationale

---

## 9. Prerequisites

Before implementation:

1. **Install `gh aw` extension:**
   ```bash
   gh extension install github/gh-agentic-workflows
   ```

2. **Verify GitHub Copilot access** for the repository

3. **Ensure secrets are configured:**
   - `ANTHROPIC_API_KEY`
   - `COMPOSIO_API_KEY`

---

## 10. Success Criteria

Implementation is complete when:

- [ ] Both workflows trigger on PR, push, and schedule
- [ ] Both post separate, labeled outputs
- [ ] Critical findings block PR merge
- [ ] Immediate Gmail sent for critical issues
- [ ] Daily digest aggregates and compares findings
- [ ] Comparison tracking doc created
- [ ] Tests pass for native implementation

---

*Design approved 2026-02-23. Ready for implementation planning.*
