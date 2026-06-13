# cambrian-plugin

Plugin de Claude Code (y OpenCode) que **aumenta la creatividad** forzando divergencia multi-agente antes de converger. Domain-agnostic.

> La explosión cámbrica fue un estallido súbito de formas diversas antes de que la selección convergiera. Este plugin hace lo mismo con ideas: estalla, después selecciona.

## Uso

**Divergencia inline (siempre disponible):** pedí ideas normal — "dame ideas para X", "alternativas a Y", "nombres para Z". El skill `diverge` se activa solo y fuerza divergencia (≥12 ideas crudas, inversión, analogías, restricciones) antes de converger.

**Divergencia profunda:** `/brainstorm-extremo <tema>` — lanza 6 lentes contradictorias en paralelo (minimalista, maximalista, contrarian, interdisciplina, first-principles, restricción absurda) + un juez sintetizador. Te muestra el crudo de cada lente y después la síntesis. Recuerda lo ya explorado (anti-repetición) y persiste todo al corpus.

## Estado

En construcción. **Plan 1 ✓** motor de corpus. **Plan 2 ✓** capas de divergencia (skill `diverge` + `/brainstorm-extremo`). Plan 3 (pendiente): publish/higiene (multi-CLI manifests, health-check, versioning, git-hooks, registro en meta-plugin).

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

```bash
pytest                 # suite completa
bin/dev/smoke-test.sh  # round-trip end-to-end en data dir temporal
```

## Configuración

Comportamiento externalizado en `config/`:
- `lenses.json` — las 6 lentes divergentes y sus mandatos.
- `thresholds.json` — `ideas_per_lens`, `anti_repetition_window`.
- `vocabulary.json` — status válidos del corpus (`generada`/`aceptada`/`rechazada`).
