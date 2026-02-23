# Eva Tool Calling 2.0 Design

**Date:** 2026-02-23
**Status:** Approved
**Author:** Claude (with Louis du Plessis)

## Overview

This design upgrades Eva to use Anthropic's Programmatic Tool Calling (PTC) and Dynamic Filtering features, while maintaining multi-provider support for NVIDIA/Kimi and Grok backends. It also adds a multi-model peer review system for automated code review.

### Goals

1. **Token Efficiency** - Reduce token consumption by 50-60% through PTC batching
2. **Latency Reduction** - Minimize API round trips for multi-tool workflows
3. **Dynamic Filtering** - Filter web content before it reaches context window
4. **Automated Review** - Multi-model peer review on all PRs

### Non-Goals

- Replacing non-Anthropic providers (they remain for flexibility)
- Adding new external integrations (focus on core PTC upgrade)
- Changing memory system or workflow structure

## Architecture

### Provider Strategy Pattern

The agent loop is abstracted behind a `ProviderStrategy` interface. Each provider implements its own tool calling style.

```
┌─────────────────────────────────────────────────────────────────────┐
│                          src/agent.py                                │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                      run_agent(prompt)                          │ │
│  │  1. Load memory -> build system prompt                          │ │
│  │  2. Get strategy = get_provider_strategy(PROVIDER)              │ │
│  │  3. Return strategy.run(prompt, system, tools)                  │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      src/providers/__init__.py                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │              ProviderStrategy (Protocol/ABC)                    │ │
│  │  - run(prompt, system, tools, memory_dir) -> str                │ │
│  │  - supports_ptc: bool                                           │ │
│  │  - supports_code_execution: bool                                │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                   │
           ┌───────────────────────┼───────────────────────┐
           ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   anthropic.py  │    │    nvidia.py    │    │     grok.py     │
│                 │    │                 │    │                 │
│ - PTC enabled   │    │ - Classic loop  │    │ - Classic loop  │
│ - Code exec     │    │ - OpenAI format │    │ - OpenAI format │
│ - Dynamic filter│    │                 │    │                 │
│ - Container mgmt│    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

**Key Design Decisions:**

- `agent.py` becomes a thin orchestrator - loads memory and delegates to strategy
- Each provider file owns its complete tool-calling loop
- Tools defined once in `tools.py` with optional `allowed_callers` field
- Non-Anthropic providers ignore `allowed_callers` and use direct calling

## Tool Definitions

Tools are organized by calling strategy in `src/tools.py`:

### Core Tools (Direct Only)

Memory operations stay direct - they're fast and simple.

```python
CORE_TOOLS = [
    {
        "name": "read_memory",
        "description": "Read a memory file (soul, user, telos, context, harness)",
        "input_schema": {...},
        # No allowed_callers = direct only
    },
    {
        "name": "update_context",
        "description": "Add entry to context.md rolling log",
        "input_schema": {...},
    },
]
```

### Composio Tools (PTC-Enabled)

External API calls get `allowed_callers` for batching.

```python
COMPOSIO_TOOLS = [
    {
        "name": "fetch_emails",
        "description": "Fetch emails from Gmail. Returns list of {id, subject, from, snippet, date}.",
        "input_schema": {
            "type": "object",
            "properties": {
                "max_results": {"type": "integer", "default": 10},
                "query": {"type": "string", "default": "is:unread"},
            },
        },
        "allowed_callers": ["code_execution_20260120"],
    },
    {
        "name": "fetch_calendar_events",
        "description": "Fetch upcoming calendar events. Returns list of {id, summary, start, end}.",
        "input_schema": {...},
        "allowed_callers": ["code_execution_20260120"],
    },
    {
        "name": "send_email",
        "description": "Send an email via Gmail.",
        "input_schema": {...},
        "allowed_callers": ["code_execution_20260120"],
    },
]
```

### Web Tools (Dynamic Filtering)

```python
WEB_TOOLS = [
    {
        "type": "web_fetch_20260209",  # Dynamic filtering version
        "name": "web_fetch",
        "max_uses": 10,
        "max_content_tokens": 50000,
    },
]

CODE_EXECUTION_TOOL = {
    "type": "code_execution_20260120",  # PTC version
    "name": "code_execution",
}
```

### Provider-Specific Tool Loading

```python
def get_tools_for_provider(provider: str) -> list:
    """Return tools formatted for the given provider."""
    if provider == "anthropic":
        return CORE_TOOLS + COMPOSIO_TOOLS + WEB_TOOLS + [CODE_EXECUTION_TOOL]
    else:
        # Strip allowed_callers for non-PTC providers
        tools = []
        for tool in CORE_TOOLS + COMPOSIO_TOOLS:
            clean_tool = {k: v for k, v in tool.items() if k != "allowed_callers"}
            tools.append(clean_tool)
        return tools
```

## Programmatic Tool Calling Flow

When using Anthropic provider with PTC:

```
User: "Check my emails and calendar, summarize what's urgent"

     ┌─────────────┐
     │  Eva Agent  │
     └──────┬──────┘
            │ 1. Send request with code_execution + tools
            ▼
     ┌─────────────┐
     │  Claude API │
     └──────┬──────┘
            │ 2. Claude writes Python code:
            │    emails = await fetch_emails(query="is:unread")
            │    events = await fetch_calendar_events(hours_ahead=4)
            │    urgent = [e for e in emails if "URGENT" in e["subject"]]
            │    print(f"Found {len(urgent)} urgent emails")
            │
            │ 3. API returns tool_use blocks with caller.type = "code_execution"
            ▼
     ┌─────────────┐
     │  Eva Agent  │  4. Execute each tool, return results
     └──────┬──────┘
            ▼
     ┌─────────────┐
     │  Claude API │  5. Code continues, filters data, returns summary
     └──────┬──────┘
            ▼
     ┌─────────────┐
     │  Eva Agent  │  6. Receive final text response (filtered, not raw data)
     └─────────────┘
```

### Anthropic Provider Implementation

```python
# src/providers/anthropic.py

@dataclass
class ContainerState:
    id: Optional[str] = None
    expires_at: Optional[str] = None

class AnthropicStrategy:
    """Anthropic provider with PTC and code execution support."""

    supports_ptc = True
    supports_code_execution = True

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.container = ContainerState()
        self.model = "claude-sonnet-4-20250514"

    def run(self, prompt: str, system: str, tools: list, memory_dir) -> str:
        messages = [{"role": "user", "content": prompt}]

        while True:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system,
                tools=tools,
                messages=messages,
                container=self.container.id,
            )

            # Track container for reuse
            if hasattr(response, "container"):
                self.container.id = response.container.id
                self.container.expires_at = response.container.expires_at

            if response.stop_reason == "end_turn":
                return self._extract_text(response)

            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})
                tool_results = self._execute_tools(response.content, memory_dir)
                messages.append({"role": "user", "content": tool_results})
                continue

            if response.stop_reason == "pause_turn":
                messages.append({"role": "assistant", "content": response.content})
                continue
```

## Peer Review System

Multi-model peer review using GPT-4o and Gemini for code review consensus.

```
                    ┌─────────────────┐
                    │   Eva (Claude)  │
                    │   Primary Dev   │
                    └────────┬────────┘
                             │ Creates PR
                             ▼
                    ┌─────────────────┐
                    │   GitHub PR     │
                    └────────┬────────┘
                             │ Triggers peer-review.yml
         ┌───────────────────┴───────────────────┐
         ▼                                       ▼
┌─────────────────┐                   ┌─────────────────┐
│  Reviewer A     │                   │  Reviewer B     │
│  GPT-4o         │                   │  Gemini 2.0     │
└────────┬────────┘                   └────────┬────────┘
         │         ┌─────────────────┐         │
         └────────►│  Consensus Bot  │◄────────┘
                   │  2/3 = merge    │
                   └─────────────────┘
```

### Review Criteria

Each reviewer evaluates:
1. **Code Quality** - Readability, maintainability, best practices
2. **Security** - Injection risks, credential exposure, OWASP Top 10
3. **Edge Cases** - Error handling, null checks, boundary conditions
4. **Performance** - Obvious inefficiencies, N+1 queries, memory leaks

### Consensus Rules

- 2/3 approval = auto-merge eligible
- Any security concern = hard block regardless of approvals
- Results posted as PR comment with actionable feedback

## File Structure

```
eva-orchestrator/
├── src/
│   ├── agent.py                  # MODIFIED - thin orchestrator
│   ├── tools.py                  # MODIFIED - add allowed_callers
│   ├── composio_tools.py         # MODIFIED - called by execute_tool()
│   │
│   ├── providers/                # NEW
│   │   ├── __init__.py           # ProviderStrategy protocol + factory
│   │   ├── anthropic.py          # PTC + code execution + containers
│   │   ├── nvidia.py             # Classic loop (Kimi K2.5)
│   │   └── grok.py               # Classic loop (Grok 3)
│   │
│   ├── review/                   # NEW
│   │   ├── __init__.py
│   │   ├── peer_review.py        # Multi-model review logic
│   │   └── run_review.py         # CLI for GitHub Action
│   │
│   └── workflows/                # Unchanged
│
├── .github/workflows/
│   └── peer-review.yml           # NEW
│
├── tests/
│   ├── test_providers/           # NEW
│   │   ├── test_anthropic.py
│   │   ├── test_nvidia.py
│   │   └── test_grok.py
│   └── test_review/              # NEW
│       └── test_peer_review.py
│
└── requirements.txt              # MODIFIED - add google-generativeai
```

## Error Handling

### Error Types

| Type | Handling |
|------|----------|
| Rate Limit | Retry with exponential backoff (max 3 retries) |
| Container Expired | Reset container ID, create new on next request |
| Tool Execution | Return error to Claude as `is_error: true` |
| Provider Unavailable | Raise `AgentError`, let caller handle |

### Container Lifecycle

- Containers created automatically on first PTC request
- Container ID persisted and reused across calls
- Containers expire after ~4.5 minutes of inactivity
- On expiry, automatically reset and create new container

## Testing Strategy

### Test Pyramid

```
         ┌─────────────┐
         │   E2E Test  │  Manual, real APIs
         └──────┬──────┘
         ┌──────┴──────┐
         │ Integration │  ~5 tests, mocked external APIs
         └──────┬──────┘
    ┌──────────┴──────────┐
    │      Unit Tests     │  ~25 tests
    └─────────────────────┘
```

### Key Test Cases

**Providers:**
- Simple response without tools
- PTC tool call flow (code execution -> tool -> continue)
- Container reuse across calls
- Container expiry recovery

**Peer Review:**
- 2/3 approval passes
- 1/3 approval fails
- Security concern blocks even with approvals

## Migration Path

### Phase 1: Add Provider Infrastructure
- Create `src/providers/` directory
- Extract existing code into strategy classes
- `agent.py` becomes thin orchestrator
- All tests pass, behavior identical

### Phase 2: Enable PTC for Anthropic
- Add `code_execution` tool
- Add `allowed_callers` to Composio tools
- Container management added

### Phase 3: Add Dynamic Filtering
- Upgrade `web_fetch` to `20260209` version
- Benefits automatic

### Phase 4: Add Peer Review
- Create `src/review/` module
- Add `peer-review.yml` GitHub Action
- Configure secrets

## Expected Benefits

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Token usage (multi-tool) | ~2000 tokens | ~800 tokens | 60% reduction |
| API round trips (5 tools) | 5 | 1 | 80% reduction |
| Web fetch context | Full HTML | Filtered data | 50-80% reduction |
| Code review coverage | Manual | Automated | 100% PRs reviewed |

## Dependencies

### New Dependencies

```txt
google-generativeai>=0.5.0   # For Gemini peer review
```

### Required Secrets

| Secret | Purpose |
|--------|---------|
| `ANTHROPIC_API_KEY` | Existing |
| `OPENAI_API_KEY` | GPT-4o peer review |
| `GOOGLE_AI_API_KEY` | Gemini peer review |

## References

- [Anthropic Code Execution Tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/code-execution-tool)
- [Anthropic Programmatic Tool Calling](https://platform.claude.com/docs/en/agents-and-tools/tool-use/programmatic-tool-calling)
- [Anthropic Web Fetch with Dynamic Filtering](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/web-fetch-tool)
- [Claude Blog: Improved Web Search with Dynamic Filtering](https://claude.com/blog/improved-web-search-with-dynamic-filtering)
