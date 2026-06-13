#!/bin/bash
# Diagnóstico de cambrian-plugin. Imprime ✓/✗ por chequeo. Exit 0 siempre (es reporte).
set -uo pipefail

ROOT="${CLAUDE_PLUGIN_ROOT:-${OPENCODE_PLUGIN_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")}}"

echo "cambrian-plugin — health check"

# 1. Identidad y versión
if [ -f "$ROOT/.claude-plugin/plugin.json" ]; then
  ver=$(python3 -c "import json;print(json.load(open('$ROOT/.claude-plugin/plugin.json'))['version'])" 2>/dev/null || echo "?")
  echo "✓ versión: cambrian-plugin v$ver"
else
  echo "✗ no se encontró .claude-plugin/plugin.json (plugin no cargado)"
fi

# 2. Skills
if [ -d "$ROOT/skills" ]; then
  echo "✓ skills: $(ls "$ROOT/skills" | tr '\n' ' ')"
else
  echo "✗ falta skills/"
fi

# 3. Command
if [ -f "$ROOT/commands/brainstorm-extremo.md" ]; then
  echo "✓ command: /brainstorm-extremo presente"
else
  echo "✗ falta commands/brainstorm-extremo.md"
fi

# 4. CLI responde
if python3 "$ROOT/bin/cambrian" --help >/dev/null 2>&1; then
  echo "✓ bin/cambrian responde"
else
  echo "✗ bin/cambrian no responde"
fi

# 5. Datadir
DATADIR="${CAMBRIAN_DATA_DIR:-$HOME/.local/share/cambrian}"
if [ -d "$DATADIR" ]; then
  echo "✓ datadir: $DATADIR"
else
  echo "· datadir no inicializado (normal en primera ejecución): $DATADIR"
fi

exit 0
