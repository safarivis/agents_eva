# Codex-Only Tool Calling Implementation Plan

**Goal:** Simplify Eva to a single-provider OpenAI Codex stack with native OpenAI tool calling, removing Anthropic/NVIDIA/Grok complexity and Anthropic‑specific PTC concepts.

**Why a new plan:** The prior Tool Calling 2.0 plan is centered on Anthropic PTC + multi‑provider strategy. With only OpenAI Codex, that architecture is not required and adds complexity.

## Is the old plan still needed for Codex?
**Short answer:** No. Anthropic PTC and `allowed_callers` are Anthropic‑specific. If you only use OpenAI Codex, the provider strategy and PTC filtering are unnecessary.

**What can still benefit Codex:**
- Clear tool definitions and a single tool execution path.
- Better tests around tool calls and agent loop behavior.
- Optional peer review automation (can be OpenAI‑only).

## Scope
**In scope:**
- OpenAI Codex as the only provider
- OpenAI tool calling (function calling)
- Cleanup of provider branches and Anthropic SDK usage
- Tests updated to OpenAI‑only

**Out of scope (drop from prior plan):**
- Anthropic PTC and `allowed_callers`
- NVIDIA/Grok provider strategies
- Multi‑model peer review consensus (unless you explicitly want it)

---

## Phase 1: Simplify Provider to Codex‑Only

### Task 1: Remove multi‑provider branching
**Files:**
- Modify: `src/agent.py`
- Modify: `requirements.txt`

**Steps:**
1. Replace provider selection logic with a single OpenAI Codex path.
2. Remove Anthropic SDK usage and any NVIDIA/Grok configuration.
3. Use `OPENAI_MODEL` env var (no hardcoded model), default to a safe placeholder if needed (e.g., `codex` or leave empty and assert).
4. Remove `anthropic` dependency from `requirements.txt`.

**Expected outcome:** Single `run_agent()` implementation using OpenAI tool calling.

---

## Phase 2: OpenAI Tool Calling Integration

### Task 2: Normalize tools to OpenAI format
**Files:**
- Modify: `src/tools.py`

**Steps:**
1. Store tool definitions in OpenAI function schema directly:
   - `{ type: "function", function: { name, description, parameters } }`
2. Remove conversion helpers (no Anthropic formats required).
3. Keep execution logic in `execute_tool()` unchanged.

**Expected outcome:** Tools are ready for OpenAI `tools=` without extra conversion.

### Task 3: Update agent loop for OpenAI tool calls
**Files:**
- Modify: `src/agent.py`

**Steps:**
1. Use OpenAI client for tool calling.
2. Loop until no tool calls, then return the final response content.
3. Ensure tool call arguments are parsed and executed with `execute_tool()`.

**Expected outcome:** Deterministic OpenAI tool calling loop.

---

## Phase 3: Tests

### Task 4: Update or add tests for OpenAI‑only behavior
**Files:**
- Modify/Create: `tests/test_agent.py`
- Modify/Create: `tests/test_tools.py`

**Steps:**
1. Mock OpenAI `chat.completions.create` (or `responses.create` if you choose the Responses API).
2. Add tests for:
   - No tool call -> direct response.
   - Tool call -> tool execution -> final response.
3. Remove provider‑specific tests.

**Expected outcome:** Tests cover the single provider flow.

---

## Phase 4 (Optional): Peer Review

### Task 5: Optional OpenAI‑only peer review automation
**Files:**
- Create: `src/review/*`
- Create: `.github/workflows/peer-review.yml`

**Notes:**
- If you still want automated review, use a single OpenAI model for review.
- Drop Gemini consensus logic.

**Expected outcome:** Simple CI review using OpenAI only.

---

## Deliverables
- Codex‑only agent loop
- OpenAI‑formatted tools
- Updated tests
- Reduced dependencies and simpler configuration

## Configuration
- `OPENAI_API_KEY`
- `OPENAI_MODEL` (set to your Codex model name)

---

## Decision Summary
- **PTC/allowed_callers:** Not needed for Codex.
- **Provider strategy:** Not needed unless you plan to re‑introduce multiple providers later.
- **Peer review:** Optional; can be OpenAI‑only if desired.
