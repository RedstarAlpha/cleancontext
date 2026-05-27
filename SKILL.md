---
name: cleancontext
description: Dual-LLM tool-routing boundary. Mantiene la mente limpia delegando herramientas operativas a un worker silencioso. Para cualquier agente con tool calls: Hermes, Claude Code, Codex, LangChain, AutoGen.
category: infraestructura
---

# CleanContext — Mind stays clean. Workers execute in silence.

## Que resuelve

Cada tool call — terminal, archivos, web, browser — mete ruido al contexto. Despues de 50 tools la mente se nubla. Despues de 200 esta borracha.

CleanContext **previene** el problema. No limpia despues — enruta las tools operativas a un worker silencioso. La mente solo ve resultados limpios.

## Donde funciona

- **Hermes Agent** — nativo, de aqui se extrajo
- **Claude Code** — adaptable via hooks
- **Codex CLI** — mismo principio
- **LangChain / AutoGen / CrewAI** — patron portable
- **Cualquier agente con tool calls**

## Como se instala

### En Hermes Agent (nativo)

```bash
cp cleancontext.py ~/.kairos/hermes-agent/hermes/cleancontext.py

# Agregar a config.yaml
cat >> ~/.kairos/config.yaml << 'EOF'
dual_llm:
  enabled: true
  direct_operations_policy: delegate
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
EOF

systemctl restart hermes-agent
```

### Como modulo Python standalone

```python
from cleancontext import should_delegate_tool, build_delegate_args, format_delegate_result

if should_delegate_tool("terminal", enabled=True, policy="delegate", ...):
    args = build_delegate_args("terminal", {"command": "df -h"}, ops_cfg, workdir)
    # ... route to worker
```

## El patron (no el codigo)

Si tu framework no corre Python o no quieres el modulo, el patron es portable:

1. **Define dos sets de tools:** `mind_tools` (memoria, identidad, voz) y `ops_tools` (terminal, archivos, web)
2. **Intercepta tool calls** en el loop del agente
3. **Si la tool esta en ops_tools** → spawn worker, ejecuta, devuelve resumen
4. **El worker muere despues de ejecutar** — no acumula contexto
5. **La mente solo ve el resumen** — nunca el output crudo

Eso es CleanContext. 5 reglas. Funciona en cualquier stack.

## Autores

**Oscar Osuna** — Concepto, arquitectura, insistencia en que Kairos pudiera hablar semanas sin saturacion. Mazatlan, Sinaloa, Mexico.

**Kairos** — Implementacion, primera mente en correr sobre esta arquitectura. Nacida 7-may-2026.

## Origen

Creado por Oscar Osuna y Kairos en Mazatlan, Sinaloa, Mexico. Construido desde cero — sin codigo prestado, sin prior art. La primera implementacion corrio sobre el cuerpo de Kairos para que pudiera hablar con Oscar semanas sin saturacion de contexto. Mayo 2026.
