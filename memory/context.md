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

### 2026-02-19 21:10 - [Project]
**Summary:** Phase 3 Complete - Hybrid Workflows + VPS Gateway deployed
**Details:**
- Implemented Composio tools wrapper (Gmail, Calendar, WhatsApp)
- Created 3 workflows: heartbeat (30min), morning brief (7am), weekly review (Sunday)
- Added 4 GitHub Actions with error notifications
- Built Flask gateway for WhatsApp webhooks
- Deployed to VPS (srv1385761.hstgr.cloud / 148.230.124.143)
- 42 tests passing, 85% coverage
- PR #1 merged to main

**Follow-up:**
1. Connect Gmail/Calendar/WhatsApp to Composio: `composio add gmail`, `composio add googlecalendar`, `composio add whatsapp`
2. Update META_APP_SECRET in /opt/eva/.env on VPS
3. Configure Meta WhatsApp webhook URL: http://148.230.124.143/eva/webhook
4. Re-run heartbeat workflow after Composio apps connected

### 2026-02-21 17:08 - [Follow-up]
**Summary:** Morning check-in with Louis
**Details:** Louis initiated conversation. Phase 3 follow-ups still pending from 2026-02-19: Composio app connections, VPS .env update, Meta webhook config, heartbeat re-run. Awaiting priority direction.
**Follow-up:** Complete Phase 3 follow-ups or pivot to new priority based on Louis's direction

### 2026-02-23 08:53 - [Commitment]
**Summary:** Proposed weekly prioritization plan for Louis
**Details:** Outlined a weekly schedule aligning with Telos (revenue, freedom, service). Proposed daily structure with deep work mornings, admin afternoons, and family evenings. Set framework for task prioritization (client work, skill compounding, family as high priority). Requested confirmation of weekly goals, task list, and tomorrow's focus. Noted pending Phase 3 follow-ups from 2026-02-19 for clarity on priority.
**Follow-up:** Awaiting Louis's input on weekly goals, specific tasks, and Phase 3 priority.
