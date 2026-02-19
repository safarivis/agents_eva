# Eva Phase 3: Hybrid Workflows + VPS Gateway Design

**Date:** 2026-02-19
**Status:** Approved
**Approach:** Hybrid (GitHub Actions for scheduled, VPS for interactive)

---

## Overview

Phase 3 implements Eva's proactive capabilities:
- **Scheduled tasks** run on GitHub Actions (heartbeat, morning brief, weekly review)
- **Interactive WhatsApp** runs on VPS for fast response (~2-5s)
- **Composio** handles all external integrations (Gmail, Calendar, WhatsApp)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    HYBRID EVA SYSTEM                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  SCHEDULED TASKS (GitHub Actions)                            │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ heartbeat.yml      │ */30 * * * * │ Check emails/cal    │ │
│  │ morning-brief.yml  │ 0 5 * * *    │ Daily 7am summary   │ │
│  │ weekly-review.yml  │ 0 18 * * 0   │ Sunday recap        │ │
│  │ error-notify.yml   │ on:failure   │ Alert on errors     │ │
│  └─────────────────────────────────────────────────────────┘ │
│                          │                                   │
│                          ▼                                   │
│                   [Composio Tools]                           │
│                          │                                   │
│                          ▼                                   │
│                    WhatsApp → Louis                          │
│                                                              │
│  INTERACTIVE (VPS - srv1385761.hstgr.cloud)                  │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  WhatsApp ──► Nginx ──► Flask ──► Eva Agent ──► Reply   │ │
│  │   (Meta)      :443     :18790     (local)      (Composio)│ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Memory System

Git as source of truth, both runtimes sync before/after.

```
GitHub Repo (source of truth)
└── memory/
    ├── soul.md      (static - Eva identity)
    ├── user.md      (static - your preferences)
    ├── telos.md     (static - purpose)
    ├── harness.md   (static - architecture)
    └── context.md   (dynamic - rolling log)
```

**Rules:**
1. Both runtimes `git pull` before reading memory
2. Both runtimes `git commit && git push` after updating context.md
3. context.md entries are append-only (no conflicts)
4. Static files (soul, user, telos, harness) only edited manually

---

## GitHub Actions Workflows

### heartbeat.yml (Every 30 min)
```yaml
trigger: cron */30 * * * *
purpose: Check for urgent items that need attention
actions:
  1. Load memory
  2. Check Gmail for urgent/VIP emails (via Composio)
  3. Check Calendar for upcoming meetings (next 2 hours)
  4. If anything urgent → Send WhatsApp alert
  5. Update context.md with findings
```

### morning-brief.yml (Daily 7am SAST)
```yaml
trigger: cron 0 5 * * * (UTC, = 7am SAST)
purpose: Daily summary to start your day
actions:
  1. Load memory
  2. Fetch today's calendar events
  3. Fetch unread/important emails
  4. Check context.md for pending follow-ups
  5. Generate brief via LLM
  6. Send WhatsApp message with summary
  7. Update context.md
```

### weekly-review.yml (Sunday 8pm SAST)
```yaml
trigger: cron 0 18 * * 0 (UTC, = 8pm SAST)
purpose: Week recap and next week prep
actions:
  1. Load memory
  2. Summarize context.md entries from past week
  3. Identify incomplete commitments
  4. Preview next week's calendar
  5. Send WhatsApp weekly digest
  6. Archive old context entries (optional)
```

### error-notify.yml (On failure)
```yaml
trigger: workflow_run (on failure of any workflow)
purpose: Alert you when Eva breaks
actions:
  1. Extract error from failed workflow
  2. Send WhatsApp alert: "Eva error in {workflow}: {error}"
```

---

## VPS Gateway

### Infrastructure
- **Server:** srv1385761.hstgr.cloud (Hostinger VPS)
- **Port:** 18790 (Flask)
- **Proxy:** Nginx :443 → /eva/webhook → :18790
- **Service:** systemd eva-gateway.service

### Flask Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/webhook` | POST | Receive WhatsApp messages from Meta |
| `/health` | GET | Health check |

### Webhook Flow
```
1. Verify Meta signature
2. Extract message text + sender
3. git pull (sync memory)
4. Run Eva agent with message
5. Send response via Composio WhatsApp
6. git commit+push (update context)
```

### Security
- Meta webhook signature verification
- Only Louis's WhatsApp number can trigger Eva
- API keys in `.env`, not in code
- HTTPS via Nginx/Let's Encrypt

### Installation Path
```
/opt/eva/
├── .venv/
├── src/
├── memory/
└── .env
```

---

## Tools

| Tool | Source | Used By |
|------|--------|---------|
| `read_memory` | Built-in | Both |
| `update_context` | Built-in | Both |
| `GMAIL_FETCH_EMAILS` | Composio | Heartbeat, Morning Brief |
| `GMAIL_SEND_EMAIL` | Composio | When needed |
| `GOOGLECALENDAR_LIST_EVENTS` | Composio | Heartbeat, Morning Brief |
| `WHATSAPP_SEND_MESSAGE` | Composio | All notifications |

---

## New Files Required

| File | Purpose |
|------|---------|
| `src/workflows/heartbeat.py` | Heartbeat check logic |
| `src/workflows/morning_brief.py` | Brief generation logic |
| `src/workflows/weekly_review.py` | Weekly summary logic |
| `src/gateway.py` | Flask webhook receiver |
| `.github/workflows/heartbeat.yml` | Heartbeat workflow |
| `.github/workflows/morning-brief.yml` | Morning brief workflow |
| `.github/workflows/weekly-review.yml` | Weekly review workflow |
| `.github/workflows/error-notify.yml` | Error notification workflow |

---

## Testing Strategy

| Component | Test Approach |
|-----------|---------------|
| Workflow logic | Unit tests with mocked Composio |
| Gateway | Integration test with test webhook |
| End-to-end | Manual: send WhatsApp, verify response |

---

## Deployment Order

1. **Workflows first** - Test scheduled tasks work on GitHub
2. **VPS gateway second** - Add interactive capability
3. **Connect WhatsApp webhook** - Wire Meta to VPS

---

## Environment Variables

### GitHub Secrets
- `NVIDIA_API_KEY` - For Kimi K2.5
- `COMPOSIO_API_KEY` - For tool access

### VPS .env
- `NVIDIA_API_KEY`
- `COMPOSIO_API_KEY`
- `META_VERIFY_TOKEN` - WhatsApp webhook verification
- `META_APP_SECRET` - Signature verification
- `ALLOWED_PHONE` - Louis's phone number

---

## Success Criteria

1. Heartbeat runs every 30 min, alerts on urgent items
2. Morning brief arrives at 7am SAST daily
3. Weekly review arrives Sunday 8pm SAST
4. WhatsApp messages get response within 10 seconds
5. Errors trigger WhatsApp notification
6. context.md stays in sync across both runtimes
