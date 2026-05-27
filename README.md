# CleanContext

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)

**Mind stays clean. Workers execute in silence.**

CleanContext is a dual-LLM tool-routing boundary for long-running AI agents. Instead of letting every tool call pollute the reasoning model's context, CleanContext intercepts operational tools and routes them to a silent worker model — keeping the mind clean for conversation.

---

## Why

Every tool call dumps raw output into the agent's context window — terminal logs, file contents, HTTP responses, browser HTML. After dozens of calls, the reasoning model loses track of the conversation.

Existing approaches (context compaction, summarization, RAG) clean up *after* the contamination happens.

**CleanContext prevents it.**

---

## Key concepts

**Mind model** — The reasoning model. Handles conversation, identity, and high-level decisions. Receives only clean summaries from tool calls. Never sees raw output.

**Worker model** — The operations model. Executes blocked tools (terminal, file I/O, web, browser), summarizes results, and returns them to the mind. Spawned per tool call, discarded after.

**Boundary** — The routing layer. Intercepts tool calls before execution and decides: does this go to the mind directly, or to the worker? Configurable via `config.yaml` — no code changes required to adjust routing.

**Context contamination** — What happens when raw tool output (200-line `ls -la`, full HTML page, stack trace) accumulates in the reasoning model's context window. CleanContext's goal is to prevent this entirely.

---

## How it works

```
User message
    │
    ▼
Mind model  ──── calls terminal("df -h") ────►  Worker model
(reasoning)                                      (operations)
    │                                                  │
    │◄──────── "Disk: 46% used, 234G free" ◄──────────┤
    │
    ▼
Response to user
```

The boundary sits between the mind and the tool executor. If the tool is on the blocked list, the worker handles it and returns a clean one-line summary. The mind integrates the result without ever seeing raw output.

---

## Who it's for

- **Agent developers** building assistants that run long sessions (hours, not minutes)
- **Teams** running coding agents, devops bots, or research agents that hit hundreds of tool calls per session
- **Anyone** using frameworks like LangGraph, OpenAI Agents SDK, or custom loops who has seen their agent degrade mid-session from context overload

If your agent has ever "gotten drunk" — started hallucinating, repeating itself, or losing track of the task after heavy tool use — CleanContext addresses the root cause.

---

## Where to implement

CleanContext is framework-agnostic. Drop it into any agent that has a tool execution loop:

| Framework | How to integrate |
|---|---|
| **LangGraph** | Add routing logic in the tool node before calling `ToolExecutor` |
| **OpenAI Agents SDK** | Override the tool runner in the agent loop |
| **LangChain AgentExecutor** | Wrap `tool.run()` calls with the boundary check |
| **Custom loops** | Insert `should_delegate_tool()` before your tool dispatch |
| **Hermes / similar** | Configure via `config.yaml`, no code changes needed |

The `cleancontext.py` module has zero external dependencies — copy it into any project.

---

## Installation

```bash
pip install cleancontext
```

Or copy `cleancontext.py` directly into your project.

---

## Quick start

```python
from cleancontext import should_delegate_tool, build_delegate_args, format_delegate_result

# In your agent's tool execution loop:
if should_delegate_tool(
    function_name,
    dual_llm_enabled=True,
    dual_llm_direct_policy="delegate",
    allowed_mind_tools=MIND_TOOLS,
    direct_ops_tools=OPS_TOOLS,
):
    args = build_delegate_args(function_name, function_args, ops_cfg, workdir)
    worker_response = your_worker_call(args)          # plug in your worker here
    result = format_delegate_result(function_name, worker_response)
else:
    result = run_tool_directly(function_name, function_args)
```

---

## Configuration

```yaml
dual_llm:
  enabled: true
  direct_operations_policy: delegate   # allow | delegate | ops_only | block

  mind:
    provider: openai
    model: gpt-4o

  operations:
    provider: openai
    model: gpt-4o-mini
    toolsets: [terminal, file, web, browser]

  allowed_mind_tools:
    - memory
    - clarify
    - delegate_task

  blocked_direct_tools:
    - terminal
    - write_file
    - web_search
    - browser_navigate
```

`direct_operations_policy` controls behavior when a blocked tool is called:

| Value | Behavior |
|---|---|
| `delegate` | Route to worker, return result to mind |
| `allow` | Mind executes everything directly (boundary disabled) |
| `ops_only` | Worker executes, result not returned to mind |
| `block` | Tool call is rejected |

See [`config.example.yaml`](config.example.yaml) for a full reference.

---

## Comparison

| Framework | What it splits |
|---|---|
| AutoGen, CrewAI, MetaGPT | **Tasks** across multiple agents |
| CleanContext | **Tools** across two models within one agent |

Multi-agent frameworks divide work between agents that think. CleanContext routes tools between models within a single agent process — the mind never stops reasoning, it just has a silent worker handling execution behind it.

---

## License

MIT © Oscar Osuna, 2026
