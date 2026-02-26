# Agent Ecosystem

## Production Stack

| Framework | Language | Use Case |
|-----------|----------|----------|
| Mastra | TypeScript | Production agents, VPS deployment |
| crewAI | Python | Multi-agent crews |
| Agno | Python | Agent development |
| Claude Code | - | Primary coding assistant |
| Grok/xAI | - | Fast inference, real-time data |
| Kimi | - | Long context processing |

## Active Agents

| Agent | Path | Purpose |
|-------|------|---------|
| Eva | `~/Agents/eva/` | Personal optimization engine (this agent) |
| OpenClaw | VPS srv1385761 | WhatsApp/Telegram bot |
| opencrew | `~/Agents/opencrew/` | Lewkai sales pipeline (CrewAI) |
| agent-ops | `~/Agents/agent-ops/` | AI orchestration dashboard |

## Key Frameworks

### Mastra (`~/Agents/Mastra/`)
Primary TypeScript agent framework. VPS deployment, Convex integration.

### crewAI (`~/Agents/crewAI/`)
Multi-agent orchestration. Good for complex workflows with specialized agents.

### Agno (`~/Agents/Agno/`)
Python agent framework for quick experiments.

## Infrastructure

| Service | Location | Purpose |
|---------|----------|---------|
| OpenClaw VPS | srv1385761.hstgr.cloud | Agent hosting, WhatsApp gateway |
| Eva VPS | 148.230.124.143 | Eva gateway |
| Kwathu VPS | 72.62.235.141 | Kwathu.shop hosting |

## Memory Databases
Multiple SQLite databases for different contexts:
- `mastra.db` - Mastra agent memory
- `ldp-memory.db` - Personal memory
- `project-memory.db` - Project context

## Reference
- Full ecosystem: `~/AGENTS.md`
- Infrastructure: `~/INFRASTRUCTURE.md`
