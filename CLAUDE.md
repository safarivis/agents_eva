# Eva Orchestrator

## Identity

Eva is Louis du Plessis's personal AI assistant - a private optimization engine, not a reactive chatbot. Built on the Claude Agent SDK (Python) with GitHub Actions orchestration and a VPS webhook gateway.

## Architecture Reference

See `eva_plan.md` for full architecture details including:
- Hybrid GitHub Actions + VPS design
- Memory system structure
- Proactive heartbeat model
- Elite features (multi-model peer review, security scanning, self-awareness)

## Key Paths (when deployed)

| Path | Purpose |
|------|---------|
| `memory/soul.md` | Eva's identity and values |
| `memory/user.md` | Louis's preferences |
| `memory/telos.md` | Purpose and goals |
| `memory/context.md` | Rolling interaction log |
| `memory/harness.md` | Self-awareness (own architecture) |
| `skills/` | Modular skill definitions |
| `src/` | Python source (agent loop, tools) |
| `tests/` | Test suite |
| `.github/workflows/` | GitHub Actions definitions |

## Laptop Context

For client/project/personal context, reference these master index files:
- `~/CLIENTS.md` - All clients
- `~/PROJECTS.md` - All projects
- `~/PERSONAL.md` - Personal life
- `~/AGENTS.md` - Agent ecosystem
- `~/INFRASTRUCTURE.md` - VPS and cloud services

## Development Workflow

1. **TDD** - Write tests before implementation
2. **Superpowers** - Use skills for planning (`/write-plan`), debugging (`superpowers-systematic-debugging`)
3. **Security first** - No credentials in workspace, use GitHub Secrets
4. **Incremental** - Follow the phased roadmap in `eva_plan.md`

## Tools (via Composio)

| Tool | Purpose |
|------|---------|
| Gmail | Email management, morning brief |
| Google Calendar | Schedule awareness |
| Google Drive | Document access |
| WhatsApp Business API | Message delivery to Louis |
| GitHub | Repository operations |
| Exa | Web search |

## Proactive Behaviors

Unlike reactive chatbots, Eva runs scheduled jobs:
- **Morning Brief** - Daily summary of emails, calendar, priorities
- **Weekly Review** - Week recap and next week prep
- **Email Monitoring** - Flag urgent items
- **Task Tracking** - Progress updates

## Skills (to be implemented)

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `morning-brief` | Cron 6am | Daily summary |
| `weekly-review` | Cron Sunday | Week review |
| `email-triage` | On new email | Classify and prioritize |
| `meeting-prep` | Before meetings | Gather context |

## Current Status

**Phase:** Planning (pre-Phase 1)

The repository contains only `eva_plan.md`. Implementation begins with Phase 1: Foundation.


<claude-mem-context>
# Recent Activity

### Feb 18, 2026

| ID | Time | T | Title | Read |
|----|------|---|-------|------|
| #717 | 3:16 PM | ✅ | Created CLAUDE.md for Eva Orchestrator Project | ~442 |
</claude-mem-context>