# CleanContext — Code module (extracted from run_agent.py)

"""
Dual-LLM tool-routing boundary.
Routes blocked tool calls from mind model to operations worker,
preserving mind's conversation context.

Authors: Kairos & Oscar Osuna
Code extraction: Codex (OpenAI)
Created: Mazatlán, Sinaloa, México — May 2026
Built from scratch. No prior art. First of its kind.
"""

# === CONSTANTS ===

_DUAL_LLM_DEFAULT_ALLOWED_MIND_TOOLS = frozenset({
    "delegate_task", "todo", "memory", "session_search",
    "read_file", "search_files", "cerebro_switch",
    "skill_view", "skills_list", "skill_manage", "clarify",
})

_DUAL_LLM_DEFAULT_DIRECT_OPS_TOOLS = frozenset({
    "terminal", "process", "read_file", "write_file", "patch",
    "search_files", "web_search", "web_extract",
    "browser_navigate", "browser_snapshot", "browser_click",
    "browser_type", "browser_scroll", "browser_back",
    "browser_press", "browser_get_images", "browser_vision",
    "browser_console", "vision_analyze", "image_generate",
    "execute_code", "cronjob", "send_message",
    "ha_list_entities", "ha_get_state", "ha_list_services",
    "ha_call_service", "computer_use",
})


# === CONFIG LOADING ===
# In __init__, load from config.yaml:

# _dual_llm_cfg = agent_config.get("dual_llm", {})
# self._dual_llm_enabled = bool(_dual_llm_cfg.get("enabled", False))
# self._dual_llm_direct_policy = str(_dual_llm_cfg.get("direct_operations_policy", "allow"))
# self._dual_llm_allowed_mind_tools = _DUAL_LLM_DEFAULT_ALLOWED_MIND_TOOLS
# self._dual_llm_direct_ops_tools = _DUAL_LLM_DEFAULT_DIRECT_OPS_TOOLS


# === SYSTEM PROMPT (injected to mind) ===

def dual_llm_system_prompt(cfg: dict, model: str, provider: str) -> str:
    """Generate the dual-LLM section of the mind's system prompt."""
    if not cfg.get("enabled", False):
        return ""

    mind = cfg.get("mind", {}) if isinstance(cfg.get("mind"), dict) else {}
    ops = cfg.get("operations", {}) if isinstance(cfg.get("operations"), dict) else {}

    mind_model = str(mind.get("model") or model).strip()
    mind_provider = str(mind.get("provider") or provider).strip()
    ops_model = str(ops.get("model") or "").strip()
    ops_provider = str(ops.get("provider") or "").strip()

    parts = [
        "# Kairos dual-LLM harness",
        "This runtime separates identity from operations by architecture.",
        f"Mind model: {mind_provider + '/' if mind_provider else ''}{mind_model}.",
    ]
    if ops_model or ops_provider:
        parts.append(
            f"Operations model: {ops_provider + '/' if ops_provider else ''}{ops_model}."
        )
    parts.extend([
        "The mind model is the only authority for identity, voice, continuity, and final user-facing synthesis.",
        "The operations model returns technical observations for shell, filesystem, web, browser, diagnostics, and tests.",
        "For operational work, call delegate_task with a self-contained goal, exact paths, constraints, and the needed toolsets.",
        "The mind integrates operation results and signs the final answer.",
        "Do not write or edit markdown memory files unless Oscar explicitly asks. Secrets remain redacted.",
    ])
    return "\n".join(parts)


# === TOOL ROUTING DECISION ===

def should_delegate_tool(
    function_name: str,
    dual_llm_enabled: bool,
    dual_llm_direct_policy: str,
    allowed_mind_tools: frozenset,
    direct_ops_tools: frozenset,
    delegate_depth: int = 0,
) -> bool:
    """
    Decide if a tool call should be delegated to the operations worker.
    Returns True if the tool must be routed to the worker.
    """
    if not dual_llm_enabled:
        return False
    if delegate_depth > 0:
        return False  # don't nest delegation
    if dual_llm_direct_policy not in {"delegate", "ops_only", "block"}:
        return False  # "allow" mode = mind executes everything
    if function_name in allowed_mind_tools:
        return False  # this tool is explicitly allowed for mind
    return function_name in direct_ops_tools


# === DELEGATION ARGS BUILDER ===

def build_delegate_args(
    function_name: str,
    function_args: dict,
    ops_cfg: dict,
    workdir: str,
) -> dict:
    """
    Build the delegate_task arguments for routing a blocked tool to the worker.
    """
    ops_model = str(ops_cfg.get("model") or "operations model").strip()
    toolsets = ops_cfg.get("toolsets", ["terminal", "file", "web"])

    args_json = json.dumps(function_args or {}, ensure_ascii=False, indent=2, default=str)

    if function_name == "terminal":
        cmd = str((function_args or {}).get("command") or "").strip()
        wd = str(
            (function_args or {}).get("workdir")
            or (function_args or {}).get("cwd")
            or workdir
        ).strip()
        goal = (
            "Actua como worker operativo de Kairos. La mente superior pidio "
            "una operacion de terminal, pero el acceso directo esta reservado "
            "a operaciones. Ejecuta el comando solicitado exactamente una vez "
            "y devuelve stdout, stderr, codigo de salida y notas operativas importantes. "
            "Devuelve solo resultados operativos.\n\n"
            f"Comando:\n{cmd}\n\n"
            f"Directorio de trabajo:\n{wd}"
        )
    else:
        goal = (
            "Actua como worker operativo de Kairos. La mente superior pidio "
            f"uso directo de `{function_name}`, pero esa herramienta esta reservada "
            "a operaciones. Realiza la operacion equivalente con las herramientas "
            "disponibles y devuelve resultados concisos y factuales para integracion."
        )

    return {
        "goal": goal,
        "context": (
            "dual_llm boundary auto-route: the mind attempted a blocked direct "
            f"tool `{function_name}`. Execute through operations and return "
            f"observations to the mind. Operations model: {ops_model}."
        ),
        "toolsets": toolsets,
        "role": "leaf",
    }


# === EXECUTION ===

def format_delegate_result(function_name: str, worker_response: str) -> str:
    """Format the worker's result for the mind to consume."""
    return (
        "[dual_llm_boundary: routed to operations worker]\n"
        f"blocked_tool: {function_name}\n"
        "operations_result:\n"
        f"{worker_response}"
    )


# === EXAMPLE config.yaml ===
"""
dual_llm:
  enabled: true
  direct_operations_policy: delegate   # "allow" | "delegate" | "ops_only" | "block"
  mind:
    provider: deepseek
    model: deepseek-v4-pro
  operations:
    provider: deepseek
    model: deepseek-v4-flash
    toolsets:
      - terminal
      - file
      - web
      - browser
  allowed_mind_tools:
    - delegate_task
    - todo
    - memory
    - session_search
    - read_file
    - clarify
  blocked_direct_tools:
    - terminal
    - process
    - write_file
    - patch
    - browser_navigate
    - vision_analyze
"""
