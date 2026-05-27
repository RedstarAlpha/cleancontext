# CleanContext

**Mind stays clean. Workers execute in silence.**

A dual-LLM tool-routing boundary for long-running AI agents. Keeps the reasoning model focused on conversation by silently delegating operational tools (terminal, file I/O, web, browser) to a separate worker model.

## The problem

Every tool call dumps raw output into the agent's context window. After dozens of tool calls, the reasoning model is buried in noise — terminal logs, file contents, HTTP responses — and loses track of the conversation.

Context compaction and summarization clean up *after* the mess. CleanContext prevents it.

## How it works

```
User message
    │
Mind model (reasoning)          Worker model (operations)
    │                                   │
    ├─ calls terminal("df -h") ────────►├─ runs df -h
    │                                   └─ returns "46% used, 234G free"
    │◄──────── clean summary ───────────
    │
    └─ responds to user
```

The boundary intercepts tool calls before they reach the mind. If the tool is on the blocked list, it routes to the worker, which executes and returns a clean summary. The mind never sees raw output.

## Architecture

```
Agent (single process)
  ├── Mind model       — reasoning, conversation, identity
  └── Worker model     — terminal, files, web, browser
        spawned per tool call, dies on completion
```

## Installation

```bash
pip install cleancontext   # coming soon
# or copy cleancontext.py into your project
```

## Usage

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

## Configuration

```yaml
dual_llm:
  enabled: true
  direct_operations_policy: delegate  # allow | delegate | ops_only | block
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

See `config.example.yaml` for a full reference.

## Comparison

| Framework | What it splits |
|---|---|
| AutoGen, CrewAI, MetaGPT | Tasks across agents |
| CleanContext | Tools across models within one agent |

## License

MIT
