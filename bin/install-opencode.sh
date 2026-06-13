#!/usr/bin/env bash
# install-opencode.sh — Registra cambrian-plugin como plugin global de OpenCode.
#
# cambrian es una herramienta de creatividad domain-agnostic: la querés disponible en
# CUALQUIER proyecto, así que usa la estrategia "global" (a diferencia de un plugin
# per-repo). Esto agrega el injector JS a plugin[] y el dir skills/ a skills.paths del
# ~/.config/opencode/opencode.json. Idempotente.
#
# Uso: bash bin/install-opencode.sh [--uninstall]

set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OC_CONFIG="${HOME}/.config/opencode/opencode.json"
PLUGIN_REL=".opencode/plugins/cambrian.js"

if [ ! -f "$OC_CONFIG" ]; then
  echo "✗ No existe $OC_CONFIG — OpenCode no está configurado"
  exit 1
fi

python3 - "$OC_CONFIG" "$PLUGIN_ROOT" "$PLUGIN_REL" "${1:-}" <<'PYEOF'
import json, os, sys

cfg_path, root, plugin_rel, action = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
plugin_abs = os.path.join(root, plugin_rel)
skills_abs = os.path.join(root, "skills")

with open(cfg_path) as f:
    cfg = json.load(f)

changed = False
is_uninstall = (action == "--uninstall")

# Plugin JS entry (injector de AGENTS.md, sentinel-guarded a su propio repo)
plugs = cfg.setdefault("plugin", [])
if is_uninstall:
    if plugin_abs in plugs:
        cfg["plugin"] = [p for p in plugs if p != plugin_abs]
        changed = True
        print(f"  ✓ plugin removido: {plugin_abs}")
    else:
        print("  - plugin no estaba registrado")
else:
    if plugin_abs not in plugs:
        plugs.append(plugin_abs)
        changed = True
        print(f"  ✓ plugin registrado: {plugin_abs}")
    else:
        print("  - plugin ya registrado")

# Skills paths (OpenCode schema: {"paths": [...]}, no un array plano)
skills_obj = cfg.setdefault("skills", {"paths": []})
if not isinstance(skills_obj, dict) or "paths" not in skills_obj:
    old = skills_obj if isinstance(skills_obj, list) else []
    skills_obj = {"paths": old}
    cfg["skills"] = skills_obj

paths = skills_obj["paths"]
if is_uninstall:
    if skills_abs in paths:
        cfg["skills"]["paths"] = [p for p in paths if p != skills_abs]
        changed = True
        print(f"  ✓ skills removidas: {skills_abs}")
    else:
        print("  - skills no estaban registradas")
else:
    if skills_abs not in paths:
        paths.append(skills_abs)
        changed = True
        print(f"  ✓ skills agregadas: {skills_abs}")
    else:
        print("  - skills ya registradas")

if changed:
    with open(cfg_path, "w") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")
    os.chmod(cfg_path, 0o644)
    print(f"\n✓ {cfg_path} actualizado")
else:
    print("\n✓ Todo ya estaba en su estado final")
PYEOF
