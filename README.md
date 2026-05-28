# CleanContext

[![PyPI](https://img.shields.io/pypi/v/cleancontext.svg)](https://pypi.org/project/cleancontext/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![Zero dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen.svg)](cleancontext.py)

**Keep your AI agent sharp through long sessions — no hallucinations, no repetition, no context rot.**

Most agents start degrading after 50–100 tool calls. Terminal output, file contents, web responses — all of it piles into the same context the agent uses to think. Eventually it loses track, repeats itself, or hallucinates.

CleanContext stops that from happening.

```
Without CleanContext              With CleanContext

Agent calls terminal("find .")   Agent calls terminal("find .")
        │                                  │
        ▼                                  ▼
  Context fills with             [Boundary intercepts]
  2000 lines of output                   │
        │                       Worker runs find, sees 2000 lines
        ▼                       Worker returns: "47 log files found"
  Agent gets drunk                      │
  at 250K tokens                        ▼
                               Agent receives summary only
                               Context stays clean
```

---

## How it works

Tool calls are split into two categories:

- **Reasoning tools** — memory, delegation, clarification. Low noise. Stay in the main context.
- **Operational tools** — terminal, files, web, browser. High noise. Routed to a worker that executes silently and returns only a clean summary.

The agent's reasoning context never sees raw tool output. It only sees results.

---

## Why it matters

| | Without | With CleanContext |
|---|---|---|
| Context after 50 tool calls | Full of raw output | Clean summaries only |
| Behavior after heavy use | Degrades, repeats, hallucinates | Stays sharp |
| Session length | Limited by context window | Limited by worker budget |
| Token waste | High (reprocessing raw output) | Low (summaries only) |

---

## Installation

```bash
pip install cleancontext
```

Or copy `cleancontext.py` into your project. Zero external dependencies.

---

## Quick start

```python
from cleancontext import should_delegate_tool, build_delegate_args, format_delegate_result

# In your agent's tool execution loop:
if should_delegate_tool(
    function_name,
    boundary_enabled=True,
    routing_policy="delegate",
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

## Works with any agent

→ **Claude Code, Claude agents** (Anthropic)  
→ **Codex, GPT-4o agents** (OpenAI)  
→ **Hermes, DeepSeek, Qwen** — local models via Ollama  
→ **Any custom agent loop** — if it dispatches tool calls, CleanContext fits

---

## Configuration

```yaml
boundary:
  enabled: true
  direct_operations_policy: delegate

  mind:
    provider: openai          # openai | anthropic | ollama | deepseek
    model: gpt-4o             # claude-sonnet-4-6 | hermes3:8b | deepseek-chat

  operations:
    provider: openai          # use a smaller/cheaper model here
    model: gpt-4o-mini        # claude-haiku-4-5-20251001 | qwen2.5:3b

  allowed_mind_tools:
    - clarify
    - delegate_task
    - memory

  blocked_direct_tools:
    - terminal
    - write_file
    - web_search
    - browser_navigate
```

See [`config.example.yaml`](config.example.yaml) for a full reference.

---

## Comparison

| Approach | Strategy |
|---|---|
| Context compaction | Shrink context after it fills |
| RAG / summarization | Offload memory to external stores |
| Multi-agent (CrewAI, AutoGen) | Split tasks across agents |
| **CleanContext** | **Block noise at the boundary before it enters** |

CleanContext is complementary to all of the above. Use it with compaction, RAG, or multi-agent setups.

---

## Who made this

**Oscar Osuna.** Built in Mazatlán, Sinaloa, Mexico — not in a San Francisco lab.

---

## License

MIT © Oscar Osuna, 2026
