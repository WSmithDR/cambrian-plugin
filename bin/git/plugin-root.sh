#!/bin/bash
# Resuelve la raíz de cambrian-plugin de forma portable entre CLIs.
# Prioridad: OPENCODE_PLUGIN_ROOT / CLAUDE_PLUGIN_ROOT > .claude/settings.json > git root > PWD
# Uso: PLUGIN_ROOT=$(bash /ruta/a/plugin-root.sh)
set -euo pipefail

if [ -n "${OPENCODE_PLUGIN_ROOT:-}" ]; then echo "$OPENCODE_PLUGIN_ROOT"; exit 0; fi
if [ -n "${CLAUDE_PLUGIN_ROOT:-}" ]; then echo "$CLAUDE_PLUGIN_ROOT"; exit 0; fi

SETTINGS=".claude/settings.json"
if [ -f "$SETTINGS" ]; then
  root=$(python3 -c "
import json
data = json.load(open('$SETTINGS'))
plugs = data.get('plugins', [])
if plugs: print(plugs[0])
" 2>/dev/null || true)
  if [ -n "$root" ]; then echo "$root"; exit 0; fi
fi

root=$(git rev-parse --show-toplevel 2>/dev/null || true)
if [ -n "$root" ]; then echo "$root"; exit 0; fi

echo "$PWD"
exit 0
