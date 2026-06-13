# AGENTS.md — cambrian-plugin

Instrucciones operativas portables entre CLIs (Claude Code, OpenCode).

## Qué es cambrian-plugin

Aumenta la creatividad forzando divergencia multi-agente antes de converger. Domain-agnostic. Dos niveles:
- **`diverge`** (skill inline): divergencia rápida, una sola cabeza, sin agentes.
- **`/brainstorm-extremo <tema>`** (command): 6 lentes contradictorias en paralelo + juez + memoria anti-repetición.

## Reglas operativas

1. Ante una pregunta creativa, conceptual o de diseño abierta: invocar la skill `diverge` antes de responder.
2. Para problemas complejos o que requieren divergencia profunda: escalar a `/brainstorm-extremo <tema>`.
3. `bin/cambrian` es la CLI unificada del datadir (`$CAMBRIAN_DATA_DIR`, default `~/.local/share/cambrian/`). Nunca leer/escribir el datadir directamente.
4. Nunca filtrar ideas antes de presentarlas: mostrar CRUDO, luego el juez converge.

## Nombres de tools entre CLIs

| Concepto | Claude Code | OpenCode |
|---|---|---|
| Invocar skill | `Skill("diverge")` | tool nativo `skill` |
| Ejecutar comando | `Bash(...)` | `bash` nativo |
| Subagente | `Agent(...)` | subagente nativo |

## Setup de desarrollo

Tras clonar, instalar los git hooks una vez: `bash bin/dev/setup.sh`
(pre-commit corre los tests; post-commit auto-bumpea la versión por conventional commit).
