"""
CleanContext — keep your AI agent sharp through long sessions.

Prevents context rot by routing high-noise tool calls (terminal, files, web)
to a disposable worker. The agent's reasoning context only receives clean summaries,
not raw output — no hallucinations, no repetition, no degradation.

Usage:
    from cleancontext import should_delegate_tool, build_delegate_args, format_delegate_result
"""

from __future__ import annotations

import json


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_ALLOWED_MIND_TOOLS: frozenset[str] = frozenset({
    "clarify",
    "delegate_task",
    "memory",
    "read_file",
    "search_files",
    "todo",
})

DEFAULT_OPS_TOOLS: frozenset[str] = frozenset({
    "browser_back",
    "browser_click",
    "browser_console",
    "browser_get_images",
    "browser_navigate",
    "browser_press",
    "browser_scroll",
    "browser_snapshot",
    "browser_type",
    "browser_vision",
    "cronjob",
    "execute_code",
    "image_generate",
    "patch",
    "process",
    "send_message",
    "terminal",
    "vision_analyze",
    "web_extract",
    "web_search",
    "write_file",
})


# ---------------------------------------------------------------------------
# System prompt injection
# ---------------------------------------------------------------------------

def boundary_system_prompt(cfg: dict, model: str = "", provider: str = "") -> str:
    """Return the boundary section to inject into the mind model's system prompt."""
    if not cfg.get("enabled", False):
        return ""

    mind = cfg.get("mind") or {}
    ops = cfg.get("operations") or {}

    mind_id = "/".join(filter(None, [mind.get("provider"), mind.get("model") or model]))
    ops_id = "/".join(filter(None, [ops.get("provider"), ops.get("model")]))

    lines = [
        "## Tool routing",
        "This agent uses a context isolation boundary.",
        f"Mind model: {mind_id or 'configured model'}.",
    ]
    if ops_id:
        lines.append(f"Operations model: {ops_id}.")
    lines.extend([
        "The mind model handles conversation, reasoning, and final responses.",
        "The operations model executes terminal commands, file I/O, web, and browser tools.",
        "For operational tasks, call delegate_task with a self-contained goal and required toolsets.",
        "The mind integrates operation results and composes the final answer.",
    ])
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Routing decision
# ---------------------------------------------------------------------------

def should_delegate_tool(
    function_name: str,
    boundary_enabled: bool = True,
    routing_policy: str = "delegate",
    allowed_mind_tools: frozenset[str] | None = None,
    direct_ops_tools: frozenset[str] | None = None,
    delegate_depth: int = 0,
) -> bool:
    """
    Return True if this tool call should be routed to the operations worker.

    Args:
        function_name: Name of the tool being called.
        boundary_enabled: Master switch. If False, mind executes everything.
        routing_policy: Routing policy. "delegate" routes blocked tools
            to the worker. "allow" disables routing. "block" rejects blocked tools.
        allowed_mind_tools: Tools the mind may call directly.
        direct_ops_tools: Tools that must go to the worker.
        delegate_depth: Current delegation nesting level. Prevents recursive delegation.
    """
    if not boundary_enabled:
        return False
    if delegate_depth > 0:
        return False
    if routing_policy not in {"delegate", "ops_only", "block"}:
        return False

    mind_tools = allowed_mind_tools if allowed_mind_tools is not None else DEFAULT_ALLOWED_MIND_TOOLS
    ops_tools = direct_ops_tools if direct_ops_tools is not None else DEFAULT_OPS_TOOLS

    if function_name in mind_tools:
        return False
    return function_name in ops_tools


# ---------------------------------------------------------------------------
# Delegation args builder
# ---------------------------------------------------------------------------

def build_delegate_args(
    function_name: str,
    function_args: dict | None,
    ops_cfg: dict | None = None,
    workdir: str = ".",
) -> dict:
    """
    Build the delegate_task arguments for routing a blocked tool to the worker.

    Args:
        function_name: Name of the blocked tool.
        function_args: Arguments the mind passed to the tool.
        ops_cfg: The `operations` section of boundary config.
        workdir: Agent's current working directory.

    Returns:
        A dict suitable for passing to your delegate_task / worker call.
    """
    cfg = ops_cfg or {}
    ops_model = str(cfg.get("model") or "operations model").strip()
    toolsets = cfg.get("toolsets") or ["terminal", "file", "web"]
    args = function_args or {}

    if function_name == "terminal":
        cmd = str(args.get("command") or "").strip()
        wd = str(args.get("workdir") or args.get("cwd") or workdir).strip()
        goal = (
            f"You are an operations worker. Execute the following terminal command "
            f"exactly once and return: stdout, stderr, exit code, and any critical observations.\n\n"
            f"Command: {cmd}\n"
            f"Working directory: {wd}"
        )
    else:
        args_json = json.dumps(args, ensure_ascii=False, indent=2, default=str)
        goal = (
            f"You are an operations worker. Execute the following operation using "
            f"available tools and return concise, factual results.\n\n"
            f"Tool: {function_name}\n"
            f"Args:\n{args_json}"
        )

    return {
        "goal": goal,
        "context": (
            f"boundary: mind attempted blocked tool `{function_name}`. "
            f"Execute and return results. Operations model: {ops_model}."
        ),
        "toolsets": toolsets,
        "role": "leaf",
    }


# ---------------------------------------------------------------------------
# Result formatter
# ---------------------------------------------------------------------------

def format_delegate_result(function_name: str, worker_response: str) -> str:
    """Format the worker's result for the mind to consume."""
    return (
        f"[boundary: routed to operations worker]\n"
        f"tool: {function_name}\n"
        f"result:\n{worker_response}"
    )
