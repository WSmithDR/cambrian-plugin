---
description: Divergencia creativa profunda — 6 lentes contradictorias en paralelo + juez sintetizador, con memoria anti-repetición. Uso: /brainstorm-extremo <tema o problema>
---

# /brainstorm-extremo

Orquestás divergencia multi-agente sobre el tema en `$ARGUMENTS`. Portable: usás la primitiva de subagentes del CLI (Agent/Task en Claude Code, subagentes en OpenCode). Si `$ARGUMENTS` está vacío, preguntá el tema antes de seguir.

Definí `TOPIC` = el tema/problema de `$ARGUMENTS` (una frase corta, sirve como clave del corpus).

Resolvé la raíz del plugin una sola vez. En Claude Code está en `$CLAUDE_PLUGIN_ROOT`:

    CAMBRIAN="$CLAUDE_PLUGIN_ROOT/bin/cambrian"

Usá `$CAMBRIAN` en TODAS las llamadas siguientes — nunca `bin/cambrian` a secas (no resolvería desde el directorio del usuario). La generalización del rooting para OpenCode se completa en el Plan 3 (resolver multi-CLI).

## Paso 1 — Leer memoria anti-repetición

Corré:

    $CAMBRIAN corpus seen --topic "TOPIC"

Esto devuelve (JSON) las ideas ya exploradas para este tema. Guardá la lista como `YA_EXPLORADO`. Si está vacía, es la primera corrida.

## Paso 2 — Cargar las lentes

Corré:

    $CAMBRIAN lenses

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

    printf '%s' "<texto de la idea>" | $CAMBRIAN corpus add --topic "TOPIC" --lens "<nombre-de-la-lente>" --text -

(Status default `generada`.) Esto alimenta la anti-repetición de la próxima corrida. Capturá y mostrá el id que devuelve cada `corpus add` junto al texto de la idea, para que el usuario pueda marcarlas sin tener que correr `corpus list`.

## Paso 7 — Ofrecer feedback

Decile al usuario que puede marcar las que le sirven o descarta:

    $CAMBRIAN corpus mark --topic "TOPIC" --id <id> --status aceptada    # o rechazada

(El id de cada idea lo devuelve `$CAMBRIAN corpus list --topic "TOPIC"`.)
