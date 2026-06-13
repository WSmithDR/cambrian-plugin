# cambrian-plugin — Plan 2: Capas de divergencia

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir las dos capas creativas sobre el motor de corpus del Plan 1: el skill liviano `diverge` (divergencia inline, siempre disponible) y el command pesado `/brainstorm-extremo` (6 lentes en paralelo + juez, con anti-repetición y persistencia).

**Architecture:** El skill `diverge` es un `SKILL.md` de metodología (prosa, una sola cabeza, sin spawnear agentes) con frontmatter CSO para auto-activarse. El command `/brainstorm-extremo` es un markdown que **orquesta el fan-out de forma portable**: lee el corpus (`bin/cambrian corpus seen`), carga las lentes (`bin/cambrian lenses`), abanica 6 subagentes (uno por lente) con la primitiva de subagentes del CLI (Agent/Task en Claude Code, subagentes en OpenCode), presenta crudo + síntesis del juez, y persiste todo (`bin/cambrian corpus add`). Se agrega un subcomando CLI `lenses` para que command y agentes lean los mandatos desde `config/lenses.json` (externalized-config) en vez de hardcodearlos.

**Tech Stack:** Igual que Plan 1 — Python 3 stdlib + pytest para el código (`lenses` CLI + tests de referencias). SKILL.md y el command son prosa portable (Claude Code + OpenCode).

**Alcance:** Plan **2 de 3**. Requiere Plan 1 mergeado/presente (usa `bin/cambrian`, `bin/lib`, `config/lenses.json`). Plan 3 = publish/higiene (multi-cli manifests AGENTS.md/opencode.json, health-check, versioning, git-hooks, skill-structure-audit en CI, registro en meta-plugin).

**Decisiones de este plan (faithful al spec aprobado):**
1. Workflow pesado = **command markdown orquestador portable** (CC + OpenCode). Harness JS determinista CC-only = mejora futura, NO en el MVP.
2. **Solo el workflow pesado persiste** al corpus. El skill liviano `diverge` es efímero (no escribe corpus).
3. Las 6 lentes y sus mandatos salen de `config/lenses.json` vía `bin/cambrian lenses`. Nada hardcodeado.
4. Anti-repetición: el command corre `corpus seen` ANTES y `corpus add` DESPUÉS.

---

### Task 1: subcomando `bin/cambrian lenses`

Expone las lentes desde `config/lenses.json` para que el command y los subagentes las lean de la fuente única.

**Files:**
- Modify: `bin/cambrian` (agregar grupo `lenses`)
- Test: `tests/test_lenses_cli.py`

- [ ] **Step 1: Escribir el test que falla** (`tests/test_lenses_cli.py`)

```python
import json
import subprocess
import sys
from pathlib import Path

BIN = Path(__file__).resolve().parents[1] / "bin" / "cambrian"


def _run(args):
    return subprocess.run(
        [sys.executable, str(BIN), *args],
        capture_output=True,
        text=True,
    )


def test_lenses_outputs_six_lenses_json():
    r = _run(["lenses"])
    assert r.returncode == 0
    lenses = json.loads(r.stdout)
    assert len(lenses) == 6
    names = [l["name"] for l in lenses]
    assert "minimalista" in names
    assert "restriccion-absurda" in names
    for l in lenses:
        assert l["name"]
        assert l["mandate"].strip()
```

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `cd /home/wagner/Documentos/dev-projects/personal_tools/cambrian-plugin && python3 -m pytest tests/test_lenses_cli.py -v`
Expected: FAIL — `bin/cambrian lenses` no es un subcomando válido (argparse error, returncode != 0)

- [ ] **Step 3: Implementar — agregar el grupo `lenses` en `bin/cambrian`**

En `_build_parser()`, después de registrar el grupo `corpus` (antes de `return parser`), agregar:

```python
    groups.add_parser("lenses", help="emite las 6 lentes divergentes (JSON) desde config")
```

En `main()`, dentro del `try`, agregar una rama para el grupo `lenses` (después del bloque `if args.group == "corpus":`):

```python
        elif args.group == "lenses":
            from lib import config

            print(json.dumps(config.lenses(), ensure_ascii=False, indent=2))
```

- [ ] **Step 4: Correr el test para verificar que pasa**

Run: `python3 -m pytest tests/test_lenses_cli.py -v`
Expected: PASS (1 test)

- [ ] **Step 5: Correr la suite completa (no romper Plan 1)**

Run: `python3 -m pytest -q`
Expected: PASS — todos los tests previos + el nuevo

- [ ] **Step 6: Commit**

```bash
git add bin/cambrian tests/test_lenses_cli.py
git commit -m "feat: cambrian lenses subcommand reads lenses from config"
```

---

### Task 2: skill liviano `diverge` (metodología inline)

**Files:**
- Create: `skills/diverge/SKILL.md`

- [ ] **Step 1: Crear `skills/diverge/SKILL.md`** con exactamente este contenido

```markdown
---
name: diverge
description: Use when the user asks for ideas, brainstorming, alternatives, names, angles, approaches, or any open-ended creative generation in any language ("dame ideas", "brainstorm", "cómo podría", "alternativas a", "nombres para"). Forces divergence — quantity before judgement, inversion, forced analogy, absurd constraint — before converging, to break the first-plausible-answer bias. For DEEP multi-agent divergence (6 parallel lenses + judge, with anti-repetition memory) use the /brainstorm-extremo command instead.
---

# diverge — divergencia creativa inline

Aumentás la creatividad cambiando el PROCESO, no el modelo: forzás divergencia antes de converger. Una sola cabeza (vos), sin spawnear agentes — eso es trabajo del command `/brainstorm-extremo`.

## Iron Law

**Prohibido evaluar, filtrar o recomendar antes de generar al menos 12 ideas crudas.** Si te encontrás justificando por qué una idea es buena o mala antes de llegar a 12, parás y seguís generando.

## Proceso

1. **Cantidad antes de calidad.** Generá ≥12 ideas crudas. Sin auto-censura. Las ideas malas son peldaños hacia las buenas.
2. **Rompé el patrón a propósito** — pasá por al menos 3 de estas palancas mientras generás:
   - **Inversión:** ¿cuál sería la solución OPUESTA? Resolvé el problema al revés.
   - **Analogía forzada:** ¿cómo lo resolvería la biología / la música / la arquitectura / un deporte?
   - **Restricción absurda:** ¿y si tuvieras 1 minuto / cero presupuesto / nada de texto?
   - **First principles:** descomponé a lo atómico y reconstruí sin asumir cómo se hace siempre.
   - **Minimalista vs maximalista:** la versión más reductiva Y la más excesiva.
3. **Recién ahí convergé.** Agrupá, descartá lo débil, combiná lo fuerte, y recomendá 2-3 con su porqué. Mostrá también las ideas crudas descartadas: en creatividad el valor está en ver el espacio completo.

## Red Flags

| Pensamiento | Realidad |
|---|---|
| "La primera idea ya es buena" | Ese es exactamente el sesgo que rompemos. Generá 12. |
| "No hace falta tanto para esto" | Lo simple es donde más se nota la respuesta obvia. Divergí igual. |
| "Evalúo rápido cuál sirve" | Evaluar temprano mata la divergencia. Primero las 12. |

## Cuándo escalar al command

Si el tema es importante, vale tokens, o querés divergencia profunda con memoria anti-repetición entre sesiones, sugerí: **"¿Querés que lo lleve a `/brainstorm-extremo`? Lanza 6 lentes contradictorias en paralelo + un juez, y recuerda lo ya explorado para ir más lejos."**
```

- [ ] **Step 2: Verificar que `SKILL.md` no tiene bloques de script embebidos grandes** (regla skill-structure-audit: SKILL.md solo instrucciones)

Run: `grep -nE '^\s*(python3|bash|node|sh) ' skills/diverge/SKILL.md || echo "sin bloques de script — ok"`
Expected: `sin bloques de script — ok`

- [ ] **Step 3: Commit**

```bash
git add skills/diverge/SKILL.md
git commit -m "feat: diverge skill — inline divergence methodology"
```

---

### Task 3: command `/brainstorm-extremo` (orquestador portable)

**Files:**
- Create: `commands/brainstorm-extremo.md`

- [ ] **Step 1: Crear `commands/brainstorm-extremo.md`** con exactamente este contenido

```markdown
---
description: Divergencia creativa profunda — 6 lentes contradictorias en paralelo + juez sintetizador, con memoria anti-repetición. Uso: /brainstorm-extremo <tema o problema>
---

# /brainstorm-extremo

Orquestás divergencia multi-agente sobre el tema en `$ARGUMENTS`. Portable: usás la primitiva de subagentes del CLI (Agent/Task en Claude Code, subagentes en OpenCode). Si `$ARGUMENTS` está vacío, preguntá el tema antes de seguir.

Definí `TOPIC` = el tema/problema de `$ARGUMENTS` (una frase corta, sirve como clave del corpus).

## Paso 1 — Leer memoria anti-repetición

Corré:

    bin/cambrian corpus seen --topic "TOPIC"

Esto devuelve (JSON) las ideas ya exploradas para este tema. Guardá la lista como `YA_EXPLORADO`. Si está vacía, es la primera corrida.

## Paso 2 — Cargar las lentes

Corré:

    bin/cambrian lenses

Devuelve (JSON) las 6 lentes con `name` y `mandate`. Son la fuente única — no inventes ni hardcodees mandatos.

## Paso 3 — Fan-out divergente (6 subagentes en paralelo)

Lanzá **un subagente por lente** (los 6 concurrentes, en un solo mensaje con varias tool-calls). A cada subagente dale exactamente:

- **Tema:** `TOPIC`.
- **Tu mandato (lente):** el `mandate` de esa lente.
- **Ya explorado (NO repitas, andá más lejos):** la lista `YA_EXPLORADO`.
- **Instrucción:** "Generá al menos 5 ideas crudas siguiendo tu mandato al extremo. No evalúes, no filtres, no te disculpes. Devolvé solo una lista de ideas, una por línea."

Cada subagente devuelve sus ideas crudas. Recolectá `{lente, ideas[]}` para las 6.

## Paso 4 — Presentar CRUDO (antes de filtrar)

Mostrale al usuario las ideas crudas agrupadas por lente, las 6. Esto es deliberado: el material "loco" sin filtrar es lo que hace distinto al plugin.

## Paso 5 — Juez sintetizador

Lanzá **un** subagente juez con TODAS las ideas crudas de las 6 lentes. Su mandato: "No generás ideas nuevas. Descartá lo débil, combiná lo fuerte, y devolvé las 5-8 mejores ideas rankeadas, cada una con una línea de por qué. Podés fusionar ideas de lentes distintas." Presentá la síntesis del juez después del crudo.

## Paso 6 — Persistir al corpus

Por CADA idea cruda generada (de las 6 lentes), persistila:

    bin/cambrian corpus add --topic "TOPIC" --lens "<nombre-de-la-lente>" --text "<texto de la idea>"

(Status default `generada`.) Esto alimenta la anti-repetición de la próxima corrida.

## Paso 7 — Ofrecer feedback

Decile al usuario que puede marcar las que le sirven o descarta:

    bin/cambrian corpus mark --topic "TOPIC" --id <id> --status aceptada    # o rechazada

(El id de cada idea lo devuelve `corpus list --topic "TOPIC"`.)
```

- [ ] **Step 2: Commit**

```bash
git add commands/brainstorm-extremo.md
git commit -m "feat: /brainstorm-extremo command — portable 6-lens fan-out + judge"
```

---

### Task 4: test de referencias (skill + command apuntan a CLI real)

Valida que los comandos `bin/cambrian` referenciados en el skill y el command existen de verdad, y que los artefactos de prosa tienen el frontmatter requerido. Espeja `test_skill_refs.py` de ankify.

**Files:**
- Test: `tests/test_artifact_refs.py`

- [ ] **Step 1: Escribir el test que falla** (`tests/test_artifact_refs.py`)

```python
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "bin" / "cambrian"


def _cli_ok(args):
    """True si `bin/cambrian <args> --help` sale 0 (subcomando válido)."""
    r = subprocess.run(
        [sys.executable, str(BIN), *args, "--help"],
        capture_output=True,
        text=True,
    )
    return r.returncode == 0


def test_skill_file_has_frontmatter():
    text = (ROOT / "skills" / "diverge" / "SKILL.md").read_text(encoding="utf-8")
    assert text.startswith("---")
    assert re.search(r"^name:\s*diverge\s*$", text, re.MULTILINE)
    assert re.search(r"^description:\s*\S", text, re.MULTILINE)


def test_command_file_has_frontmatter():
    text = (ROOT / "commands" / "brainstorm-extremo.md").read_text(encoding="utf-8")
    assert text.startswith("---")
    assert re.search(r"^description:\s*\S", text, re.MULTILINE)


def test_command_references_only_real_cli_subcommands():
    text = (ROOT / "commands" / "brainstorm-extremo.md").read_text(encoding="utf-8")
    # Cada `bin/cambrian <grupo> <cmd>` referenciado debe resolver.
    refs = set(re.findall(r"bin/cambrian\s+(\w+)\s+(\w+)", text))
    assert refs, "el command debería referenciar subcomandos de bin/cambrian"
    for group, cmd in refs:
        assert _cli_ok([group, cmd]), f"subcomando inexistente: bin/cambrian {group} {cmd}"


def test_command_references_lenses_group():
    text = (ROOT / "commands" / "brainstorm-extremo.md").read_text(encoding="utf-8")
    assert re.search(r"bin/cambrian\s+lenses", text)
    assert _cli_ok(["lenses"])
```

- [ ] **Step 2: Correr el test para verificar que pasa o falla correctamente**

Run: `python3 -m pytest tests/test_artifact_refs.py -v`
Expected: PASS (4 tests) — los archivos del skill/command ya existen de Tasks 2-3 y los subcomandos existen de Task 1. Si algún ref no resuelve, FALLA señalando exactamente cuál (ese es el valor del test).

- [ ] **Step 3: Commit**

```bash
git add tests/test_artifact_refs.py
git commit -m "test: validate skill/command frontmatter and CLI refs"
```

---

### Task 5: actualizar README con las capas de divergencia

**Files:**
- Modify: `README.md` (agregar sección "Uso")

- [ ] **Step 1: Editar `README.md`** — insertar esta sección justo después del título y el blockquote de la metáfora (antes de la sección `## Estado`)

```markdown
## Uso

**Divergencia inline (siempre disponible):** pedí ideas normal — "dame ideas para X", "alternativas a Y", "nombres para Z". El skill `diverge` se activa solo y fuerza divergencia (≥12 ideas crudas, inversión, analogías, restricciones) antes de converger.

**Divergencia profunda:** `/brainstorm-extremo <tema>` — lanza 6 lentes contradictorias en paralelo (minimalista, maximalista, contrarian, interdisciplina, first-principles, restricción absurda) + un juez sintetizador. Te muestra el crudo de cada lente y después la síntesis. Recuerda lo ya explorado (anti-repetición) y persiste todo al corpus.
```

- [ ] **Step 2: Actualizar la sección `## Estado`** — reemplazar la línea de estado del Plan 1 por:

```markdown
## Estado

En construcción. **Plan 1 ✓** motor de corpus. **Plan 2 ✓** capas de divergencia (skill `diverge` + `/brainstorm-extremo`). Plan 3 (pendiente): publish/higiene (multi-CLI manifests, health-check, versioning, git-hooks, registro en meta-plugin).
```

- [ ] **Step 3: Correr la suite completa**

Run: `python3 -m pytest -q && bin/dev/smoke-test.sh`
Expected: pytest todo verde + `OK: smoke test passed`

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: README usage for divergence layers"
```

---

## Self-review (cobertura del spec — Plan 2)

Plan 2 cubre del spec: capa liviana (skill `diverge`, §3, auto-activada, una cabeza, cantidad-antes-de-calidad + inversión/analogía/restricción/first-principles), capa pesada (command `/brainstorm-extremo`, §3-4, 6 lentes en paralelo + juez), output crudo + síntesis (§5), anti-repetición leyendo corpus antes (§6), persistencia de lo generado después (§6, solo el workflow persiste), lentes desde `config/lenses.json` (§4, externalized-config, vía nuevo `bin/cambrian lenses`), portabilidad CC + OpenCode (§2, orquestación markdown vía primitiva de subagentes). Status `generada` consistente con Plan 1.

**Fuera de Plan 2 (van a Plan 3, intencional):** AGENTS.md / opencode.json (manifiestos multi-CLI), health-check, versioning, git-hooks, skill-structure-audit en CI, registro en meta-plugin. Harness JS determinista CC-only = mejora futura documentada, no MVP. El skill `diverge` no persiste al corpus (decisión del spec: solo el workflow pesado escribe).

**Nota de ejecución:** Tasks 2 y 3 son artefactos de prosa (SKILL.md y command) — su "test" es estructural (Task 4: frontmatter + refs a CLI reales). La calidad de la prosa orquestadora se valida en la revisión de spec/calidad, no con unit tests.
