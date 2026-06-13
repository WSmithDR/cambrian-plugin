---
name: cambrian-health
description: "Verifica que cambrian-plugin está bien integrado — versión, skills, command, bin/cambrian y datadir. Correr tras instalar/actualizar el plugin o para diagnosticar por qué algo no funciona."
---

# cambrian-health

Corré el diagnóstico y presentá el resultado al usuario tal cual, resumiendo al final si está todo OK o qué acción correctiva hace falta.

    bash "${CLAUDE_PLUGIN_ROOT}/skills/cambrian-health/scripts/check.sh"

Si `CLAUDE_PLUGIN_ROOT` está vacío (OpenCode u otro CLI), resolvé la raíz con `bin/git/plugin-root.sh` y corré el mismo script desde ahí.
