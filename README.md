# cambrian-plugin

Plugin de Claude Code (y OpenCode) que **aumenta la creatividad** forzando divergencia multi-agente antes de converger. Domain-agnostic.

> La explosión cámbrica fue un estallido súbito de formas diversas antes de que la selección convergiera. Este plugin hace lo mismo con ideas: estalla, después selecciona.

## Uso

**Divergencia inline (siempre disponible):** pedí ideas normal — "dame ideas para X", "alternativas a Y", "nombres para Z". El skill `diverge` se activa solo y fuerza divergencia (≥12 ideas crudas, inversión, analogías, restricciones) antes de converger.

**Divergencia profunda:** `/brainstorm-extremo <tema>` — lanza 6 lentes contradictorias en paralelo (minimalista, maximalista, contrarian, interdisciplina, first-principles, restricción absurda) + un juez sintetizador. Te muestra el crudo de cada lente y después la síntesis. Recuerda lo ya explorado (anti-repetición) y persiste todo al corpus.

## Instalación

**1. Registrar el marketplace (una vez):**
```bash
claude plugin marketplace add WSmithDR/cambrian-plugin
```

**2. Instalar en el proyecto:**
```bash
claude plugin install cambrian-plugin@cambrian-plugin --scope project
```

### OpenCode (global)

cambrian es creatividad domain-agnostic, así que se registra **global** (disponible en cualquier proyecto), no per-repo. Una vez:
```bash
bash bin/install-opencode.sh          # registra en ~/.config/opencode/opencode.json
bash bin/install-opencode.sh --uninstall   # revertir
```
Esto agrega el injector a `plugin[]` y `skills/` a `skills.paths`. Las skills (`diverge`, `cambrian-health`) quedan disponibles en toda sesión de OpenCode; el bootstrap de `AGENTS.md` solo se inyecta dentro de este repo (sentinel guard).

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

## Estado

**Plan 1 ✓** corpus engine · **Plan 2 ✓** capas de divergencia · **Plan 3 ✓** publish/higiene (multi-CLI, health, versioning, hooks). Pendiente: registro en el meta-plugin (`/plugin-register`).

## Motor de corpus (`bin/cambrian`)

Toda la persistencia vive **fuera del plugin**, en `$CAMBRIAN_DATA_DIR` (default `~/.local/share/cambrian/`). El corpus es append-only, un JSONL por topic.

```bash
# agregar una idea (status default: generada)
bin/cambrian corpus add --topic "Docker" --lens minimalista --text "Un solo contenedor"

# listar ideas de un topic (JSON, con status vigente)
bin/cambrian corpus list --topic "Docker"

# textos ya explorados (anti-repetición: alimenta a las lentes para divergir más lejos)
bin/cambrian corpus seen --topic "Docker"

# cambiar el status de una idea (aceptada | rechazada)
bin/cambrian corpus mark --topic "Docker" --id <id> --status aceptada
```

## Desarrollo

Tras clonar, instalá los git hooks (una vez):
```bash
bash bin/dev/setup.sh
```

```bash
pytest                 # suite completa
bin/dev/smoke-test.sh  # round-trip del corpus en data dir temporal
```

## Configuración

Comportamiento externalizado en `config/`:
- `lenses.json` — las 6 lentes divergentes y sus mandatos.
- `thresholds.json` — `ideas_per_lens`, `anti_repetition_window`.
- `vocabulary.json` — status válidos del corpus (`generada`/`aceptada`/`rechazada`).
