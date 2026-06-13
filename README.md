# cambrian-plugin

Plugin de Claude Code (y OpenCode) que **aumenta la creatividad** forzando divergencia multi-agente antes de converger. Domain-agnostic.

> La explosión cámbrica fue un estallido súbito de formas diversas antes de que la selección convergiera. Este plugin hace lo mismo con ideas: estalla, después selecciona.

## Estado

En construcción. **Plan 1 (este):** motor de corpus persistente. Plan 2: capas de divergencia (skill liviano + `/brainstorm-extremo`). Plan 3: publish/higiene.

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
