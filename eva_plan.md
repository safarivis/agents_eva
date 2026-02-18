# Eva Orchestrator - Comprehensive Implementation Plan

**Date:** 2026-02-18
**Synthesized from:** Current system configuration, AI Velocity Framework, and expert-level "agentic engineering" principles

---

## 1. Core Philosophy: The "Rebuild" Approach

Following **Pillar 2 (First Principles)** and **Pillar 3 (Radical Simplicity)** of the AI Velocity Framework, Eva will be built from the ground up as a private, secure "Optimization Engine" rather than an overengineered "bolt-on" to existing complex frameworks.

### Security Mandate
By building from scratch using the Claude Agent SDK (Python), you eliminate the "security minefield" found in OpenClaw, such as remote code execution vulnerabilities and plain-text credential storage.

### Compliance
Direct use of the SDK ensures adherence to Anthropic's terms of service, avoiding the account bans associated with third-party wrappers.

### Engineering Discipline
Success is defined through **Test-Driven Development (TDD)**—writing success criteria before implementation to solve the "Articulation Problem" (capturing the 95% of unspoken context).

---

## 2. Technical Architecture

Eva utilizes a **Hybrid Orchestration Layer** that balances local control, cloud reliability, and mobile accessibility.

```
┌─────────────────────────────────────────────────────────────────┐
│                     EVA ORCHESTRATOR                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐    ┌──────────────────┐                  │
│  │   THE BRAIN      │    │    THE HEART     │                  │
│  │  GitHub Actions  │◄───│   VPS Gateway    │◄─── WhatsApp     │
│  │                  │    │                  │                  │
│  │ • Cron jobs      │    │ • Flask webhook  │                  │
│  │ • Clean Docker   │    │ • 24/7 listener  │                  │
│  │ • Full logging   │    │ • Nginx proxy    │                  │
│  └────────┬─────────┘    └──────────────────┘                  │
│           │                                                     │
│           ▼                                                     │
│  ┌──────────────────┐                                          │
│  │   THE DRIVER     │                                          │
│  │ Claude Agent SDK │                                          │
│  │                  │                                          │
│  │ • Agentic loop   │                                          │
│  │ • Tool execution │                                          │
│  │ • MCP servers    │                                          │
│  └──────────────────┘                                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### The Brain (GitHub Actions)
Core logic resides in a private `eva-orchestrator` repository. Every task runs in a clean, isolated Docker environment, providing total observability and logging.

### The Heart (VPS Webhook Gateway)
Your Hostinger VPS (`srv1385761.hstgr.cloud`) acts as the 24/7 listener. It runs a minimal Flask app to receive WhatsApp webhooks and triggers a `repository_dispatch` to GitHub to wake the agent.

### The Driver (Claude Agent SDK)
Eva uses the official SDK to manage the agentic loop—file editing, command execution, and tool selection—autonomously.

---

## 3. The Four Pillars of Implementation

### Pillar 1: Markdown-Driven Memory

Memory is elegant and human-readable, utilizing Obsidian for local syncing and editing.

| File | Purpose |
|------|---------|
| `soul.md` | Defines Eva's identity, values, and "flavor" to prevent AI sycophancy |
| `user.md` | Captures your specific preferences and context |
| `telos.md` | Outlines the agent's purpose and long-term goals |
| `context.md` | A rolling log of interactions, auto-updated by Eva after every session |

### Pillar 2: Proactive Heartbeat

Unlike reactive chatbots, Eva is "always thinking" via GitHub Action cron jobs.

| Schedule | Action |
|----------|--------|
| Every 30 min | Check emails, calendars, tasks (via Composio). Notify of urgent items |
| 7:00 AM SAST | Morning brief - daily priorities via WhatsApp |
| 8:00 PM Sunday | Weekly review and reflection |

### Pillar 3: WhatsApp Channel Adapter

A "thin" channel strategy that allows high-value, low-bandwidth communication from anywhere.

**Human-in-the-Loop:** Eva can draft emails or PRs but awaits your WhatsApp approval before final execution.

### Pillar 4: Skills Registry

A modular directory (`skills/[name]/SKILL.md`) where adding a new capability is as simple as adding an instruction file.

**Initial Skills:**
- Lead Management
- Project Status
- Follow-up Tracking
- A "skill to create more skills" for autonomous evolution

---

## 4. Strategic Stack Consolidation

To achieve **Innovation Velocity**, you must prune your current AGENTS.md configuration.

| Action | Frameworks | Reason |
|--------|------------|--------|
| **RETAIN** | Mastra, Claude Code | Production/B2B agents, Primary coding assistant |
| **ARCHIVE** | Agno, crewAI | Python framework sprawl creates "paralysis through options" |
| **REFERENCE** | OpenClaw | Blueprint to "one-shot" features into Eva, then decommission for security |

---

## 5. Repository Structure

```
eva-orchestrator/
├── .github/
│   └── workflows/
│       ├── heartbeat.yml          # Cron: */30 * * * *
│       ├── morning-brief.yml      # Cron: 0 5 * * * (7am SAST)
│       ├── wa-message.yml         # repository_dispatch
│       ├── weekly-review.yml      # Cron: 0 18 * * 0 (8pm Sun SAST)
│       ├── peer-review.yml        # Triangle agent review on PRs
│       ├── security-scan.yml      # SonarQube scan on push
│       └── error-notify.yml       # On workflow failure
├── memory/
│   ├── soul.md                    # Eva identity
│   ├── user.md                    # Louis preferences
│   ├── telos.md                   # Purpose
│   ├── context.md                 # Long-term memory (auto-updated)
│   └── harness.md                 # Self-awareness: Eva's own architecture
├── skills/
│   ├── README.md
│   ├── lead-management/SKILL.md
│   ├── project-status/SKILL.md
│   ├── follow-up/SKILL.md
│   └── skill-creator/SKILL.md     # Meta-skill for creating skills
├── src/
│   ├── eva.py                     # Main entry (agentic loop)
│   ├── agent.py                   # Claude Agent SDK wrapper
│   ├── tools.py                   # Tool definitions
│   ├── memory.py                  # Memory load/save
│   ├── skills.py                  # Skill discovery & execution
│   ├── introspection.py           # Self-awareness tools
│   └── channels/
│       ├── __init__.py
│       └── whatsapp.py            # WA Business API
├── tests/
│   ├── test_agent.py
│   ├── test_memory.py
│   ├── test_tools.py
│   └── test_skills.py
├── sonar-project.properties       # SonarQube configuration
├── Dockerfile
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## 6. Tools (Agentic Loop)

Eva will have these tools for autonomous operation:

| Tool | Purpose |
|------|---------|
| `read_memory_file` | Read from memory/ directory |
| `update_context` | Append to context.md |
| `send_whatsapp` | Send WA message |
| `execute_skill` | Run a skill |
| `get_calendar` | Via Composio GOOGLE_CALENDAR |
| `get_emails` | Via Composio GMAIL |
| `send_email` | Via Composio GMAIL |
| `web_search` | Via Composio EXA |
| `read_source_file` | Read own source code (self-awareness) |
| `read_harness` | Read harness.md (architecture awareness) |
| `propose_self_modification` | Suggest changes to own identity/code |

---

## 7. Elite Features

### Peer-Review Workflow (Triangle Pattern)

Three-agent review system for code changes:

```
┌─────────────┐
│   Eva       │ ← Primary agent (writes code)
│  (Claude)   │
└──────┬──────┘
       │ PR created
       ▼
┌─────────────┐     ┌─────────────┐
│  Reviewer A │ ←── │  Reviewer B │
│   (GPT-4o)  │     │   (Gemini)  │
└──────┬──────┘     └──────┬──────┘
       │                   │
       └───────┬───────────┘
               ▼
        Consensus check
        (2/3 approve = merge)
```

### Security Scanning (SonarQube)

Automated security scans on every push:
- OWASP Top 10 vulnerabilities
- Code smells
- Injection risks in AI-generated code
- Hardcoded secrets

### Agentic Self-Awareness

Eva is aware of her own source code and harness:
- Can read and understand her own implementation
- Can propose improvements via PR
- Can evolve her soul.md based on learnings
- Can debug her own errors

---

## 8. Implementation Roadmap

### Phase 1: Foundation (Days 1-2)
- [ ] Create private `eva-orchestrator` repo
- [ ] Configure GitHub Secrets (`ANTHROPIC_API_KEY`, WhatsApp tokens)
- [ ] Initialize memory files (soul.md, user.md, telos.md, context.md)
- [ ] Copy existing soul from `/home/louisdup/Agents/eva/soul.md`

### Phase 2: Core SDK Setup (Days 3-5)
- [ ] Implement `src/memory.py` - Memory load/save functions
- [ ] Implement `src/tools.py` - Tool definitions for Claude SDK
- [ ] Implement `src/agent.py` - ClaudeSDKClient with agentic loop
- [ ] Implement `src/eva.py` - Main entry point and mode handling

### Phase 3: Workflows (Days 6-8)
- [ ] Create `heartbeat.yml` - 30-minute proactive checks
- [ ] Create `morning-brief.yml` - Daily 7am briefing
- [ ] Create `wa-message.yml` - WhatsApp dispatch trigger
- [ ] Create `error-notify.yml` - Failure notifications

### Phase 4: VPS Gateway (Day 9)
- [ ] Create Flask webhook receiver
- [ ] Configure Nginx proxy
- [ ] Deploy to `srv1385761.hstgr.cloud`
- [ ] Test WhatsApp → GitHub flow

### Phase 5: TDD & Skills (Days 10-12)
- [ ] Write unit tests in `tests/`
- [ ] Implement `src/skills.py` - Skill discovery
- [ ] Create initial skills (LeadManagement, ProjectStatus, FollowUp)
- [ ] Define success criteria for each skill

### Phase 6: Elite Features (Days 13-15)
- [ ] Implement `src/introspection.py` - Self-awareness
- [ ] Create `memory/harness.md` - Architecture documentation
- [ ] Create `peer-review.yml` - Multi-model review
- [ ] Create `security-scan.yml` - SonarQube integration

### Phase 7: Integration (Day 16+)
- [ ] Test full flow end-to-end
- [ ] Enable cron schedules
- [ ] Monitor and iterate

---

## 9. Environment Variables / Secrets

| Secret | Source |
|--------|--------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `WA_ACCESS_TOKEN` | WA Business API access token |
| `WA_PHONE_NUMBER_ID` | Your WA phone number ID |
| `GITHUB_TOKEN` | Auto-provided by Actions |
| `OPENAI_API_KEY` | For GPT-4o peer reviewer |
| `GOOGLE_AI_API_KEY` | For Gemini peer reviewer |
| `SONAR_TOKEN` | SonarQube authentication |
| `SONAR_HOST_URL` | SonarQube server URL |

---

## 10. Expert Advice & Critique

### Critique on Sprawl
Your AGENTS.md list shows you are "collecting" tools (Flowise, Nemo, eko) rather than building an Optimization Engine. **Delete what you don't use today.**

### Advice on "Taste"
The value of Eva is your judgment layer. Focus 20% of engineering time on refining the `soul.md` and `user.md` files; this is your only durable moat against "vibe coding."

### Final Guardrail
**Never store credentials in your workspace directory.** Use environment variables/secrets exclusively, as highlighted by the OpenClaw security fallout.

---

## 11. Source Files to Copy

| From | To |
|------|-----|
| `/home/louisdup/Agents/external/eva/SYSTEM/prompts/CORE.md` | `memory/soul.md` |
| `/home/louisdup/Agents/external/eva/USER/preferences/identity.md` | `memory/user.md` |
| `/home/louisdup/Agents/external/eva/USER/TELOS/TELOS.md` | `memory/telos.md` |
| `/home/louisdup/Agents/external/eva/SYSTEM/skills/*` | `skills/` |
| `/home/louisdup/Agents/eva/soul.md` | Reference for Eva values |

---

## 12. Next Steps After MVP

1. Add SQLite for semantic search (embeddings)
2. Add LiveKit voice integration on VPS
3. Add more tools (Notion, GitHub issues, etc.)
4. Add learning loop (Eva improves based on feedback)
5. Add multi-channel support (Telegram, Slack)

---

*This plan moves you from Phase 2 (hosted agents) to Phase 12 (invisible infrastructure), turning Eva into a functional, always-on employee.*
