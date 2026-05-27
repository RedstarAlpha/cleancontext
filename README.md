# CleanContext

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)

**Expand your agent's effective context without changing your model.**

CleanContext keeps your agent's reasoning context clean by routing operational tool calls to a separate, disposable execution context. The result: your agent thinks in a window that never fills up — no matter how many tool calls it makes.

---

## The problem

AI agents hit a hard limit: the context window.

Every tool call — terminal output, file contents, web responses, browser HTML — gets appended to the same context the model uses to reason and talk. After dozens of tool calls, the reasoning model is buried under operational noise. It loses track of the goal, starts repeating itself, or hallucinates.

The standard responses — compaction, summarization, RAG — all try to clean up *after* the window fills. They shrink what's already there.

**CleanContext takes a different approach: keep the window clean from the start.**

---

## How it works

Tool calls are split into two groups:

- **Reasoning tools** — memory, task delegation, clarification. Low output volume. Stay in the mind's context.
- **Operational tools** — terminal, files, web, browser. High output volume. Routed to a separate execution context.

When the agent calls an operational tool, CleanContext intercepts it, runs it in an isolated worker context, and returns only a clean summary to the reasoning model. The raw output never touches the main context window.

```
Agent calls terminal("find . -name '*.log'")
        │
        ▼
  [CleanContext boundary]
        │
        ├──► Worker context (disposable)
        │         runs find, sees 2,000 lines of output
        │         summarizes: "47 log files found, largest: error.log (2.3MB)"
        │
        ◄── reasoning context receives the summary only
        │
        ▼
Agent responds to user — context window unchanged
```

The worker context is created per tool call and discarded after. It never accumulates.

---

## The result

| Without CleanContext | With CleanContext |
|---|---|
| Context fills with raw tool output | Context contains only summaries |
| Agent degrades after ~50 tool calls | Agent stays sharp across hundreds of calls |
| Long sessions require compaction or restart | Long sessions run uninterrupted |
| Effective context = model's context limit | Effective context = model's limit × N workers |

Your agent's reasoning window stays the same size regardless of how many operations it performs.

---

## Key concepts

**Reasoning context** — The main context window. Contains conversation, identity, goals, and tool summaries. Never sees raw operational output.

**Worker context** — A disposable execution context, created per tool call. Runs the operation, summarizes the result, and is discarded. Does not accumulate.

**Boundary** — The routing layer that intercepts tool calls and decides: does this stay in the reasoning context, or go to a worker? Configured via `config.yaml`.

---

## Who benefits

- Agents running **long sessions** — coding assistants, research agents, devops bots
- Any agent that makes **more than a few dozen tool calls** per session
- Teams whose agents **degrade mid-session** from context overload
- Developers building on **LangGraph, OpenAI Agents SDK, LangChain, or custom loops**

If your agent has ever gotten confused, repetitive, or inconsistent after heavy tool use — this is what was happening, and CleanContext prevents it.

---

## Where to implement

CleanContext is framework-agnostic. Drop it into any agent with a tool execution loop:

| Framework | Integration point |
|---|---|
| **LangGraph** | Tool node, before `ToolExecutor` |
| **OpenAI Agents SDK** | Override the tool runner in the agent loop |
| **LangChain AgentExecutor** | Wrap `tool.run()` calls |
| **Custom loops** | Before your tool dispatch |

`cleancontext.py` has zero external dependencies — copy it into any project.

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
    worker_response = your_worker_call(args)
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
    model: gpt-4o-mini                 # Use a smaller model — workers are disposable
    toolsets: [terminal, file, web, browser]

  allowed_mind_tools:                  # Stay in reasoning context
    - memory
    - clarify
    - delegate_task

  blocked_direct_tools:                # Go to worker context
    - terminal
    - write_file
    - web_search
    - browser_navigate
```

See [`config.example.yaml`](config.example.yaml) for a full reference.

---

## Comparison

| Approach | What it does |
|---|---|
| Context compaction | Shrinks the context after it fills |
| RAG / summarization | Offloads memory to external stores |
| Multi-agent (AutoGen, CrewAI) | Splits tasks across agents |
| **CleanContext** | **Prevents operational noise from entering the reasoning context** |

CleanContext is not a memory system and not an orchestration framework. It's a boundary that keeps reasoning clean by separating *what the agent thinks* from *what the agent does*.

---

## License

MIT © Oscar Osuna, 2026
