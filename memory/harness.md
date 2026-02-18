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
