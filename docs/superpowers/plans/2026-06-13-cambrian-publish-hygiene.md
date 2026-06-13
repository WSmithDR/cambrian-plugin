# cambrian-plugin — Plan 3: Publish + higiene (multi-CLI, health, versioning, hooks)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Completar `cambrian-plugin` para que sea **portable (Claude Code + OpenCode), diagnosticable, versionado y publicable**, e integrar las features de higiene del catálogo `cli-plugin-template`.

**Architecture:** Integra 6 features del catálogo, adaptadas a cambrian (`bin/cambrian`, `CAMBRIAN_DATA_DIR`): `multi-cli-compat` (resolver de plugin-root portable + `opencode.json` + `AGENTS.md` + injector OpenCode), `health-check` (skill `cambrian-health` modular), `git-hooks` (setup + pre-commit con pytest), `versioning` (post-commit semver por conventional commits), `skill-structure-audit` (scanner en pre-commit), `docs-conventions` (secciones README). El registro en el meta-plugin (`plugin-register`) es externo y se hace aparte.

**Tech Stack:** Bash (hooks, resolver, setup), Python 3 stdlib (audit script, version bump embebido), JS ESM (injector OpenCode), pytest para los guards.

**Alcance:** Plan **3 de 3**. Requiere Plan 1 + Plan 2 presentes. Cierra el MVP publicable.

**Decisiones (judgment calls resueltos):**
1. `AGENTS.md` = guía portable canónica; `CLAUDE.md` = symlink a `AGENTS.md`.
2. `opencode.json` apunta a `./skills/` directo (sin symlink `.opencode/skills`); se mantiene el injector `.opencode/plugins/cambrian.js`.
3. Rooting portable: cadena de env vars inline en el command (`CLAUDE_PLUGIN_ROOT` → `OPENCODE_PLUGIN_ROOT` → git-root) + script `bin/git/plugin-root.sh` para otros usos.
4. `cambrian-health` es **modular** (lógica en `scripts/check.sh`) para cumplir `skill-structure-audit`.
5. `marketplace.json` gana campo `version` por entrada de plugin.
6. **Registro en meta-plugin = externo** (`/plugin-register`), fuera de este plan (no agrega archivos al repo).

**Orden de dependencias:** Task 1 (multi-cli) y Task 2 (health) son independientes → primero (funcional/portabilidad). Task 3 (git-hooks) → Task 4 (versioning, su post-commit) → Task 5 (skill-structure-audit, se cablea en pre-commit). Task 6 (docs) independiente. Task 7 = verificación final.

---

### Task 1: multi-cli-compat (rooting portable + OpenCode + AGENTS.md)

**Files:**
- Create: `bin/git/plugin-root.sh`
- Create: `opencode.json`
- Create: `.opencode/plugins/cambrian.js`
- Create: `AGENTS.md`
- Create: `CLAUDE.md` (symlink → `AGENTS.md`)
- Modify: `commands/brainstorm-extremo.md` (resolver portable)
- Modify: `tests/test_artifact_refs.py` (guard del nuevo rooting)
- Test: `tests/test_multicli.py`

- [ ] **Step 1: Crear `bin/git/plugin-root.sh`**

```bash
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
```

- [ ] **Step 2: chmod + sanity del resolver**

Run: `cd /home/wagner/Documentos/dev-projects/personal_tools/cambrian-plugin && chmod +x bin/git/plugin-root.sh && CLAUDE_PLUGIN_ROOT=/tmp/x bash bin/git/plugin-root.sh`
Expected: imprime `/tmp/x`

- [ ] **Step 3: Crear `opencode.json`**

```json
{
  "$schema": "https://opencode.ai/config.json",
  "skills": {
    "paths": ["./skills/"]
  },
  "plugin": [
    "./.opencode/plugins/cambrian.js"
  ]
}
```

- [ ] **Step 4: Crear `.opencode/plugins/cambrian.js`** (injector de AGENTS.md, guard por sentinel)

```js
// .opencode/plugins/cambrian.js
// Inyecta el bootstrap de AGENTS.md en la primera sesión de OpenCode, solo dentro de este repo.
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PLUGIN_ROOT = path.resolve(__dirname, '../..'); // .opencode/plugins -> repo root
const AGENTS_MD = path.join(PLUGIN_ROOT, 'AGENTS.md');

function isInOwnRepo() {
  try {
    const sentinel = path.join(PLUGIN_ROOT, '.claude-plugin', 'plugin.json');
    return fs.existsSync(sentinel) && process.cwd().startsWith(PLUGIN_ROOT);
  } catch {
    return false;
  }
}

let _cache;
function getBootstrap() {
  if (_cache !== undefined) return _cache;
  try {
    _cache = fs.existsSync(AGENTS_MD) ? fs.readFileSync(AGENTS_MD, 'utf8').trim() : null;
  } catch {
    _cache = null;
  }
  return _cache;
}

const CambrianPlugin = () => {
  if (!isInOwnRepo()) return {};
  return {
    'experimental.chat.messages.transform': async (_input, output) => {
      if (!output.messages?.length) return;
      const firstUser = output.messages.find((m) => m.info?.role === 'user');
      if (!firstUser?.parts?.length) return;
      const already = firstUser.parts.some(
        (p) => p.type === 'text' && p.text?.includes('cambrian-plugin')
      );
      if (!already) {
        const bootstrap = getBootstrap();
        if (bootstrap) {
          firstUser.parts.unshift({ type: 'text', text: `<MANDATORY>\n${bootstrap}\n</MANDATORY>` });
        }
      }
    },
  };
};

export default CambrianPlugin;
```

- [ ] **Step 5: Crear `AGENTS.md`** (guía portable canónica — self-contained, sin referenciar CLAUDE.md para evitar circularidad con el symlink)

```markdown
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
```

- [ ] **Step 6: Crear `CLAUDE.md` como symlink a `AGENTS.md`**

Run: `ln -sf AGENTS.md CLAUDE.md && readlink CLAUDE.md`
Expected: imprime `AGENTS.md`

- [ ] **Step 7: Modificar el resolver en `commands/brainstorm-extremo.md`**

Reemplazar el bloque actual de resolución (la línea `CAMBRIAN="$CLAUDE_PLUGIN_ROOT/bin/cambrian"` y su contexto) por esta versión portable. El bloque debe quedar así:

```
Resolvé la raíz del plugin (portable Claude Code + OpenCode) y armá la ruta a la CLI:

    PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-${OPENCODE_PLUGIN_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")}}"
    CAMBRIAN="$PLUGIN_ROOT/bin/cambrian"

Usá `$CAMBRIAN` en TODAS las llamadas siguientes — nunca `bin/cambrian` a secas (no resolvería desde el directorio del usuario).
```

No cambiar el resto del command; las llamadas siguen usando `$CAMBRIAN`.

- [ ] **Step 8: Actualizar el guard en `tests/test_artifact_refs.py`**

El test `test_command_defines_rooted_cambrian_var` asume el rooting viejo. Reemplazar su cuerpo para validar el rooting portable nuevo:

```python
def test_command_defines_rooted_cambrian_var():
    text = (ROOT / "commands" / "brainstorm-extremo.md").read_text(encoding="utf-8")
    # rooting portable: ambas env vars + CAMBRIAN derivado de PLUGIN_ROOT
    assert "CLAUDE_PLUGIN_ROOT" in text
    assert "OPENCODE_PLUGIN_ROOT" in text
    assert 'CAMBRIAN="$PLUGIN_ROOT/bin/cambrian"' in text
```

- [ ] **Step 9: Escribir el test de multi-CLI** (`tests/test_multicli.py`)

```python
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_opencode_json_valid_and_points_to_skills():
    data = json.loads((ROOT / "opencode.json").read_text(encoding="utf-8"))
    assert "./skills/" in data["skills"]["paths"]
    assert any("cambrian.js" in p for p in data["plugin"])


def test_agents_md_exists_and_mentions_plugin():
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "cambrian-plugin" in text
    assert "diverge" in text
    assert "brainstorm-extremo" in text


def test_claude_md_is_symlink_to_agents():
    p = ROOT / "CLAUDE.md"
    assert p.is_symlink()
    assert Path(p.readlink()).name == "AGENTS.md"


def test_plugin_root_resolver_honors_env():
    r = subprocess.run(
        ["bash", str(ROOT / "bin" / "git" / "plugin-root.sh")],
        capture_output=True, text=True,
        env={"CLAUDE_PLUGIN_ROOT": "/tmp/cambrian-test", "PATH": "/usr/bin:/bin"},
    )
    assert r.returncode == 0
    assert r.stdout.strip() == "/tmp/cambrian-test"


def test_opencode_injector_exists():
    assert (ROOT / ".opencode" / "plugins" / "cambrian.js").exists()
```

- [ ] **Step 10: Correr los tests y la suite completa**

Run: `python3 -m pytest tests/test_multicli.py tests/test_artifact_refs.py -v && python3 -m pytest -q`
Expected: PASS — multi-cli (5) + artifact-refs actualizados + suite completa verde

- [ ] **Step 11: Commit**

```bash
git add bin/git/plugin-root.sh opencode.json .opencode AGENTS.md CLAUDE.md commands/brainstorm-extremo.md tests/test_multicli.py tests/test_artifact_refs.py
git commit -m "feat: multi-cli-compat — portable root resolver, opencode.json, AGENTS.md"
```

---

### Task 2: health-check (`cambrian-health`, modular)

Skill modular: `SKILL.md` solo invoca; la lógica vive en `scripts/check.sh` (requisito de `skill-structure-audit`).

**Files:**
- Create: `skills/cambrian-health/SKILL.md`
- Create: `skills/cambrian-health/scripts/check.sh`
- Test: `tests/test_health_skill.py`

- [ ] **Step 1: Crear `skills/cambrian-health/scripts/check.sh`**

```bash
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
```

- [ ] **Step 2: Crear `skills/cambrian-health/SKILL.md`** (solo invocación, ≤2 líneas de bash)

```markdown
---
name: cambrian-health
description: "Verifica que cambrian-plugin está bien integrado — versión, skills, command, bin/cambrian y datadir. Correr tras instalar/actualizar el plugin o para diagnosticar por qué algo no funciona."
---

# cambrian-health

Corré el diagnóstico y presentá el resultado al usuario tal cual, resumiendo al final si está todo OK o qué acción correctiva hace falta.

    bash "${CLAUDE_PLUGIN_ROOT}/skills/cambrian-health/scripts/check.sh"

Si `CLAUDE_PLUGIN_ROOT` está vacío (OpenCode u otro CLI), resolvé la raíz con `bin/git/plugin-root.sh` y corré el mismo script desde ahí.
```

- [ ] **Step 3: chmod + correr el script de health**

Run: `chmod +x skills/cambrian-health/scripts/check.sh && CLAUDE_PLUGIN_ROOT="$PWD" bash skills/cambrian-health/scripts/check.sh`
Expected: imprime los 5 chequeos, la mayoría ✓ (datadir puede ser `·`), exit 0

- [ ] **Step 4: Escribir el test** (`tests/test_health_skill.py`)

```python
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_health_skill_frontmatter():
    text = (ROOT / "skills" / "cambrian-health" / "SKILL.md").read_text(encoding="utf-8")
    assert text.startswith("---")
    assert re.search(r"^name:\s*cambrian-health\s*$", text, re.MULTILINE)


def test_health_script_runs_and_reports():
    script = ROOT / "skills" / "cambrian-health" / "scripts" / "check.sh"
    r = subprocess.run(
        ["bash", str(script)],
        capture_output=True, text=True,
        env={"CLAUDE_PLUGIN_ROOT": str(ROOT), "HOME": "/tmp", "PATH": "/usr/bin:/bin"},
    )
    assert r.returncode == 0
    assert "cambrian-plugin v" in r.stdout
    assert "bin/cambrian responde" in r.stdout
```

- [ ] **Step 5: Correr el test**

Run: `python3 -m pytest tests/test_health_skill.py -v`
Expected: PASS (2 tests)

- [ ] **Step 6: Commit**

```bash
git add skills/cambrian-health/
git commit -m "feat: cambrian-health skill (modular diagnostic)"
```

---

### Task 3: git-hooks (setup + pre-commit)

**Files:**
- Create: `bin/dev/setup.sh`
- Create: `bin/dev/git-hooks/pre-commit`

- [ ] **Step 1: Crear `bin/dev/setup.sh`**

```bash
#!/bin/bash
# Setup de desarrollo de cambrian-plugin. Ejecutar una vez tras clonar: bash bin/dev/setup.sh
set -euo pipefail
REPO_ROOT="$(git rev-parse --show-toplevel)"

install_hook() {
    local name="$1"
    local src="$REPO_ROOT/bin/dev/git-hooks/$name"
    local dst="$REPO_ROOT/.git/hooks/$name"
    chmod +x "$src"
    if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then
        echo "  $name ya instalado"
    else
        ln -sf "$src" "$dst"
        echo "  $name instalado -> .git/hooks/$name"
    fi
}

echo "cambrian-plugin — setup de desarrollo"
install_hook "pre-commit"
install_hook "post-commit"
echo "Listo. pre-commit corre tests; post-commit auto-bumpea version."
```

- [ ] **Step 2: Crear `bin/dev/git-hooks/pre-commit`** (incluye ya el bloque de skill-structure-audit, que se activa en Task 5 cuando exista el script)

```bash
#!/bin/bash
# pre-commit — corre pytest y el audit de estructura de skills.
# Instalado via symlink por bin/dev/setup.sh. Skip: git commit --no-verify
set -euo pipefail
PLUGIN_ROOT="$(cd "$(git rev-parse --show-toplevel)" && pwd)"
cd "$PLUGIN_ROOT"

echo "--- pytest..."
python3 -m pytest tests/ -q || { echo "--- Tests FAILED. Commit bloqueado (--no-verify para saltar)."; exit 1; }
echo "--- Tests OK."

if [ -f "$PLUGIN_ROOT/bin/audit-skill-structure.py" ]; then
  echo "--- skill structure audit..."
  python3 "$PLUGIN_ROOT/bin/audit-skill-structure.py" --threshold ERROR || {
    echo "--- Skill structure audit FAILED. Commit bloqueado."; exit 1; }
  echo "--- Skill structure audit OK."
fi

echo "--- OK."
exit 0
```

- [ ] **Step 3: Instalar hooks y verificar que el pre-commit corre** (post-commit se crea en Task 4; el setup lo chmodea aunque todavía no exista — ajustar: correr setup recién después de Task 4. Por ahora solo chmod + ejecución directa del pre-commit)

Run: `chmod +x bin/dev/setup.sh bin/dev/git-hooks/pre-commit && bash bin/dev/git-hooks/pre-commit`
Expected: corre pytest (todo verde), imprime `--- OK.` (el bloque de audit se saltea porque el script aún no existe), exit 0

- [ ] **Step 4: Commit**

```bash
git add bin/dev/setup.sh bin/dev/git-hooks/pre-commit
git commit -m "feat: git-hooks — setup.sh and pre-commit (pytest)"
```

---

### Task 4: versioning (post-commit semver)

**Files:**
- Modify: `.claude-plugin/marketplace.json` (agregar `version` a la entrada del plugin)
- Create: `bin/dev/git-hooks/post-commit`

- [ ] **Step 1: Agregar `version` a `.claude-plugin/marketplace.json`** — la entrada del plugin debe incluir `"version": "0.1.0"`. El archivo debe quedar:

```json
{
  "name": "cambrian-plugin",
  "owner": {
    "name": "WSmithDR",
    "url": "https://github.com/WSmithDR"
  },
  "plugins": [
    {
      "name": "cambrian-plugin",
      "source": "./",
      "version": "0.1.0",
      "description": "Aumenta la creatividad forzando divergencia multi-agente antes de converger. Domain-agnostic."
    }
  ]
}
```

- [ ] **Step 2: Crear `bin/dev/git-hooks/post-commit`**

```bash
#!/bin/bash
# post-commit: auto-bump semver en plugin.json (y sync marketplace/opencode) y amenda el commit.
# feat: -> minor | fix/chore/docs/refactor/... -> patch | feat!: o BREAKING CHANGE -> major
set -euo pipefail
REPO_ROOT="$(git rev-parse --show-toplevel)"
PLUGIN_JSON="$REPO_ROOT/.claude-plugin/plugin.json"
SENTINEL="$REPO_ROOT/.git/.version-bump-in-progress"

[ -f "$SENTINEL" ] && exit 0
if git diff --name-only HEAD~1 HEAD 2>/dev/null | grep -q "\.claude-plugin/plugin\.json"; then
  exit 0
fi

MSG="$(git log -1 --pretty=%B)"
if echo "$MSG" | grep -qE '^feat(\(.+\))?!:|BREAKING[[:space:]]CHANGE'; then BUMP="major"
elif echo "$MSG" | grep -qE '^feat(\(.+\))?:'; then BUMP="minor"
else BUMP="patch"; fi

CURRENT="$(python3 -c "import json;print(json.load(open('$PLUGIN_JSON'))['version'])")"
if ! echo "$CURRENT" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$'; then
  echo "post-commit: versión inválida '$CURRENT' — saltando"; exit 0
fi

NEW="$(CURRENT="$CURRENT" BUMP="$BUMP" python3 -c "
import os
v = os.environ['CURRENT'].split('.'); M,m,p = int(v[0]),int(v[1]),int(v[2])
b = os.environ['BUMP']
if b=='major': M,m,p = M+1,0,0
elif b=='minor': m,p = m+1,0
else: p += 1
print(f'{M}.{m}.{p}')")"

NEW="$NEW" REPO_ROOT="$REPO_ROOT" python3 -c '
import json, os
new = os.environ["NEW"]; root = os.environ["REPO_ROOT"]
def upd(rel, fn):
    full = os.path.join(root, rel)
    if not os.path.exists(full): return
    with open(full) as f: d = json.load(f)
    fn(d)
    with open(full, "w") as f:
        json.dump(d, f, indent=2); f.write("\n")
def set_top(d): d["version"] = new
def set_market(d):
    if isinstance(d.get("metadata"), dict) and "version" in d["metadata"]: d["metadata"]["version"] = new
    for p in d.get("plugins", []):
        if isinstance(p, dict) and "version" in p: p["version"] = new
upd(".claude-plugin/plugin.json", set_top)
upd(".claude-plugin/marketplace.json", set_market)
'

for rel in .claude-plugin/plugin.json .claude-plugin/marketplace.json; do
  [ -f "$REPO_ROOT/$rel" ] && git add "$REPO_ROOT/$rel"
done

touch "$SENTINEL"
git commit --amend --no-edit --no-verify
rm -f "$SENTINEL"
echo "  version: $CURRENT -> $NEW ($BUMP)"
```

- [ ] **Step 3: chmod + test manual del bump** (en un commit de prueba, luego reset suave para no dejar basura)

Run:
```bash
chmod +x bin/dev/git-hooks/post-commit
bash bin/dev/setup.sh    # instala pre-commit + post-commit como symlinks
git add .claude-plugin/marketplace.json bin/dev/git-hooks/post-commit
git commit -m "feat: versioning — post-commit semver bump and marketplace sync"
```
Expected: el commit dispara el post-commit; como el mensaje es `feat:`, bumpea minor `0.1.0 → 0.2.0` y amenda. Verificá:

Run: `python3 -c "import json;print(json.load(open('.claude-plugin/plugin.json'))['version'])"`
Expected: `0.2.0`

- [ ] **Step 4: Verificar que marketplace quedó sincronizado**

Run: `python3 -c "import json;print(json.load(open('.claude-plugin/marketplace.json'))['plugins'][0]['version'])"`
Expected: `0.2.0`

(No hace falta commit extra: el post-commit ya amendó el commit del Step 3 con las versiones sincronizadas.)

---

### Task 5: skill-structure-audit (scanner en pre-commit)

**Files:**
- Create: `bin/audit-skill-structure.py` (copia del catálogo)

- [ ] **Step 1: Copiar el scanner del catálogo a `bin/`**

Run:
```bash
cp "/home/wagner/.claude/plugins/cache/cli-plugin-template/cli-plugin-template/1.17.0/features/skill-structure-audit/files/audit-skill-structure.py" bin/audit-skill-structure.py
chmod +x bin/audit-skill-structure.py
```

- [ ] **Step 2: Correr el audit sobre las skills de cambrian**

Run: `python3 bin/audit-skill-structure.py --threshold ERROR; echo "exit=$?"`
Expected: `exit=0` — `skills/diverge/SKILL.md` es prosa pura y `skills/cambrian-health/` es modular (bash en `scripts/`, no en SKILL.md). Si reporta ERROR, es un bug a corregir en la skill ofensora (mover bash de SKILL.md a `scripts/`).

- [ ] **Step 3: Test que el audit pasa** (`tests/test_skill_structure.py`)

```python
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_skills_pass_structure_audit():
    r = subprocess.run(
        [sys.executable, str(ROOT / "bin" / "audit-skill-structure.py"), "--threshold", "ERROR"],
        cwd=str(ROOT), capture_output=True, text=True,
    )
    assert r.returncode == 0, f"skill-structure-audit reportó ERRORs:\n{r.stdout}\n{r.stderr}"
```

- [ ] **Step 4: Correr el test + verificar que el pre-commit ahora cablea el audit**

Run: `python3 -m pytest tests/test_skill_structure.py -v && bash bin/dev/git-hooks/pre-commit`
Expected: test PASS; el pre-commit ahora sí corre el bloque de audit (porque `bin/audit-skill-structure.py` existe) y termina `--- OK.`

- [ ] **Step 5: Commit**

```bash
git add bin/audit-skill-structure.py tests/test_skill_structure.py
git commit -m "feat: skill-structure-audit scanner wired into pre-commit"
```

---

### Task 6: docs-conventions (secciones README)

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Insertar las secciones de convenciones** en `README.md`, después de la sección `## Uso` (o donde encaje mejor antes de `## Desarrollo`):

```markdown
## Instalación

**1. Registrar el marketplace (una vez):**
```bash
claude plugin marketplace add WSmithDR/cambrian-plugin
```

**2. Instalar en el proyecto:**
```bash
claude plugin install cambrian-plugin@cambrian-plugin --scope project
```

## Actualizar

> El CLI cachea el plugin: refrescá el marketplace y reinstalá.
```bash
/plugin marketplace update cambrian-plugin
/plugin install cambrian-plugin@cambrian-plugin --scope project
```
En sesión activa, `/reload-plugins`. Verificá la versión con `/cambrian-health`.

## Versionado

Semver automático por prefijo de commit:

| Prefijo | Bump |
|---|---|
| `feat:` | minor |
| `fix:`, `chore:`, `docs:`, `refactor:`, `test:`, `ci:` | patch |
| `feat!:` o `BREAKING CHANGE` | major |
```

- [ ] **Step 2: Actualizar la sección `## Desarrollo`** para incluir el setup de hooks:

```markdown
## Desarrollo

Tras clonar, instalá los git hooks (una vez):
```bash
bash bin/dev/setup.sh
```

```bash
pytest                 # suite completa
bin/dev/smoke-test.sh  # round-trip del corpus en data dir temporal
```
```

- [ ] **Step 3: Actualizar `## Estado`** a:

```markdown
## Estado

**Plan 1 ✓** corpus engine · **Plan 2 ✓** capas de divergencia · **Plan 3 ✓** publish/higiene (multi-CLI, health, versioning, hooks). Pendiente: registro en el meta-plugin (`/plugin-register`).
```

- [ ] **Step 4: Correr la suite completa + smoke**

Run: `python3 -m pytest -q && bin/dev/smoke-test.sh`
Expected: todo verde + `OK: smoke test passed`

- [ ] **Step 5: Commit** (mensaje `docs:` → post-commit bumpea patch)

```bash
git add README.md
git commit -m "docs: install/update/versioning conventions"
```

---

### Task 7: Verificación final

- [ ] **Step 1: Suite completa + smoke + audits**

Run:
```bash
python3 -m pytest -q
bin/dev/smoke-test.sh
python3 bin/audit-skill-structure.py --threshold ERROR; echo "skill-audit exit=$?"
python3 "/home/wagner/.claude/plugins/cache/cli-plugin-template/cli-plugin-template/1.17.0/features/portability-audit/files/audit-portability.py" .
```
Expected: pytest verde, smoke ok, skill-audit exit=0, portability sin CRITICAL.

- [ ] **Step 2: Verificar plugin.json/marketplace versiones coinciden**

Run: `python3 -c "import json; a=json.load(open('.claude-plugin/plugin.json'))['version']; b=json.load(open('.claude-plugin/marketplace.json'))['plugins'][0]['version']; print(a,b); assert a==b"`
Expected: imprime la misma versión dos veces, sin AssertionError.

- [ ] **Step 3: Reporte de cierre** — listar `git log --oneline` de Plan 3 y confirmar estado verde. (Sin commit; es verificación.)

---

## Self-review (cobertura del spec — Plan 3)

Plan 3 cubre del spec: multi-CLI Claude Code + OpenCode (§2 — resolver portable, opencode.json, AGENTS.md, injector; completa el rooting OpenCode que quedó pendiente en Plan 2), health-check (higiene), versioning + docs-conventions + git-hooks + skill-structure-audit (higiene de publish, §9). El registro en el meta-plugin (`plugin-register`) queda como paso externo post-plan (no agrega archivos al repo, §7 del spec: el meta-plugin administra la evolución).

**Portabilidad:** el resolver evita rutas absolutas/`bin/cambrian` desnudo; `audit-portability.py` debe salir sin CRITICAL en Task 7.
**skill-structure-audit:** `cambrian-health` se diseñó modular (bash en `scripts/`) para no violar la regla; `diverge` es prosa. El test `test_skill_structure.py` lo garantiza en CI.
**Nota de versionado:** una vez activo el post-commit, los commits de Plan 3 a partir de Task 4 bumpean la versión automáticamente; los números exactos pueden variar según el orden, pero plugin.json y marketplace.json quedan sincronizados (verificado en Task 7 Step 2).

**Fuera de Plan 3:** harness JS determinista CC-only (mejora futura), hook detector de "tibias" (F2), full-auto (F3), meta-gusto/growth (meta-plugin). Brutal-honesty advisor = plugin aparte.
