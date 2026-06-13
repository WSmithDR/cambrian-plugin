# cambrian-plugin — Diseño (spec)

**Fecha:** 2026-06-13
**Estado:** Diseño aprobado por secciones · auditado contra catálogo cli-plugin-template · pendiente revisión final del usuario
**Repo:** `github.com:WSmithDR/cambrian-plugin`

---

## 1. Qué es y por qué

`cambrian-plugin` es un plugin **domain-agnostic** cuyo único objetivo es **aumentar la creatividad** de las ideas/respuestas.

**Insight base:** la creatividad en un LLM no se logra cambiando el modelo, sino el *proceso*. Hay que **forzar divergencia antes de converger** y romper el sesgo de la "primera respuesta plausible". El plugin no inventa inteligencia nueva: estructura el proceso para que la inteligencia existente explore más lejos antes de elegir.

**Nombre:** la explosión cámbrica (estallido súbito de formas diversas antes de que la selección converja) es la metáfora exacta: estallido de ideas → selección.

**Alcance:** 100% divergencia creativa. No hace coaching ni crítica de vida personal, no es un asesor. (Ver §7.)

---

## 2. Compatibilidad CLI (constraint de primera clase)

**Targets: Claude Code + OpenCode.** Se adopta el feature `multi-cli-compat` desde el día uno.

| Componente | Portabilidad |
|---|---|
| `skill` divergencia inline | 100% portable (solo SKILL.md). |
| `command` `/brainstorm-extremo` | Portable (ambos CLIs soportan commands). |
| corpus / persistencia | Portable vía `data-gateway` (abstracción agnóstica). |
| workflow pesado (fan-out 6 lentes) | **Funciona en ambos, mecánica distinta:** en Claude Code puede usar orquestación determinista (harness Workflow/Task); en OpenCode se abanica vía su primitiva de subagentes (model-driven, menos determinista). Se abstrae detrás del command + `AGENTS.md`. |

**Implicancia honesta:** la orquestación *determinista* del workflow pesado es Claude-Code-only. La paridad funcional (las 6 lentes + juez sí corren en OpenCode) se logra delegando el fan-out a la primitiva de subagentes de cada CLI, no al harness JS específico de Claude Code. Tool-name translation y manifiestos por CLI los provee `multi-cli-compat`. Se proveen `AGENTS.md` (OpenCode/genérico) además del manifiesto de Claude Code.

---

## 3. Arquitectura: dos capas

```
cambrian-plugin/
├── skill        (capa liviana — siempre disponible, auto-activada)
│     └── metodología inline de divergencia en una sola cabeza:
│         forzar cantidad antes de calidad (N ideas antes de evaluar),
│         inversión, analogías forzadas, restricciones. Barato.
│
├── command  /brainstorm-extremo   (dispara la capa pesada)
│     └── invoca el fan-out de lentes (portable por CLI)
│
├── workflow     (capa pesada — multi-agente)
│     ├── 6 lentes divergentes en paralelo (mandatos contradictorios)
│     ├── lee corpus previo del topic → "esto ya se exploró, andá más lejos"
│     ├── devuelve CRUDO por lente + SÍNTESIS del juez
│     └── persiste todo lo generado al corpus externo (vía data-gateway)
│
├── config/      (externalized-config: nº lentes, nº ideas, ventana anti-rep)
├── bin/lib/     (data-gateway + bundled-scripts: leer/escribir/deduplicar corpus)
└── (sin persistencia propia — el corpus vive AFUERA, ver §5)
```

**Flujo de uso:**
- Pedís ideas de forma normal → el **skill** se auto-activa y fuerza divergencia en una sola pasada. Barato, siempre disponible.
- Querés el martillo grande → `/brainstorm-extremo` → el **workflow** abanica las 6 lentes, lee el corpus para no repetirse, y devuelve crudo + síntesis.

**Forma del workflow (`agent-pipeline`):** fase divergente paralela (6 lentes, `parallel-agents`) → contrato de artefacto JSON → fase del juez (revisor/QA que filtra, combina, rankea). El contrato JSON entre lentes y juez es explícito.

---

## 4. Las 6 lentes + juez (workflow pesado)

Agentes en paralelo, cada uno con un mandato **contradictorio** respecto de los otros. Cada lente produce **varias** ideas (cantidad antes de calidad), no una sola.

| # | Lente | Mandato |
|---|---|---|
| 1 | **Minimalista** | La idea más simple/reductiva posible. Quitá, no agregues. |
| 2 | **Maximalista** | La versión más ambiciosa/excesiva, sin miedo al absurdo. |
| 3 | **Contrarian** | Hacé lo opuesto a la respuesta obvia. Invertí el problema. |
| 4 | **Interdisciplina** | Traé un concepto de un campo random y forzá la analogía. |
| 5 | **First Principles** | Descomponé a lo atómico y reconstruí desde cero. |
| 6 | **Restricción Absurda** | Resolvé bajo una restricción imposible (sin presupuesto, en 1 minuto, sin texto, etc.). |
| — | **Juez sintetizador** | No genera. Recibe todo, descarta lo débil, combina lo fuerte, rankea. |

**Configurable (`externalized-config`):** el número de lentes, los mandatos y el nº de ideas por lente viven en `config/*.json` leídos en runtime, no hardcodeados. v1 trae estas 6.

**Vocabulario de dominio (`vocabulary-guardian`):** los nombres de las lentes y los status del corpus (`generada | aceptada | rechazada`) son fuente única de verdad en `config/vocabulary.json`; un escáner detecta términos no registrados antes de usarlos.

---

## 5. Output

`/brainstorm-extremo` devuelve **crudo + síntesis** (decisión deliberada):

1. **Crudo por lente:** las ideas sin filtrar de cada una de las 6 lentes. Acá está el material "loco" que normalmente se descarta y que es justo lo que hace al plugin distinto.
2. **Síntesis del juez:** las mejores ideas filtradas, combinadas y rankeadas.

Mostrar el crudo es intencional: en creatividad el valor está en ver el espacio completo de ideas, no solo lo que el juez dejó pasar.

---

## 6. Persistencia (corpus externo)

**Principio clave: el corpus vive FUERA del directorio del plugin.** `cambrian-plugin` no posee la persistencia — solo **lee y escribe** contra un data dir externo, vía la abstracción `data-gateway` (las skills nunca tocan disco directo; pasan por un CLI unificado + `bin/lib/`). Sigue el patrón `ANKIFY_DATA_DIR` del ecosistema. Portable entre CLIs.

- **Formato:** append-only. Cada idea generada se guarda con:
  `{ topic, lente, texto, status: generada | aceptada | rechazada, timestamp }`
- **Se guarda todo:** tanto lo aceptado como lo rechazado.
- **Anti-repetición (el uso killer):** antes de cada corrida, el workflow lee el corpus de ese `topic` y le pasa a las lentes un resumen de "esto ya se exploró, andá más lejos". Acá la persistencia **aumenta** la novedad en vez de matarla. La deduplicación/lectura determinista la hacen scripts (`bundled-scripts`), no el LLM.

**Decisión de diseño crítica — por qué solo anti-repetición:** un sistema de aprendizaje ingenuo (re-sugerir lo que se aceptó antes) produce **regresión a la media** y vuelve al plugin *menos* creativo. `cambrian-plugin` por eso es **tonto respecto del aprendizaje**: solo escribe el corpus y aplica anti-repetición. Cualquier aprendizaje sobre el corpus es responsabilidad del meta-plugin (§7).

---

## 7. Relación con el meta-plugin (cli-plugin-template / growth)

El **proceso de mejora/aprendizaje es responsabilidad del meta-plugin `cli-plugin-template`**, que **ya está habilitado a nivel de usuario** (feature `growth-engine`: captura de feedback + hotpatch + growth). Reparto de responsabilidades:

- **`cambrian-plugin`:** genera divergencia, lee/escribe el corpus, aplica anti-repetición. **No implementa aprendizaje.**
- **Meta-plugin (ya activo):** administra la evolución del plugin (feedback/fricción → hotpatch), y a futuro puede minar el corpus para afinar lentes (meta-gusto). `cambrian-plugin` NO re-implementa nada de esto.

`cambrian-plugin` debe funcionar de forma autónoma (con un data dir por defecto) aunque el meta-plugin no intervenga. Se da de alta en el registry del meta-plugin (`plugin-register`) para que administre su evolución.

---

## 8. Fuera de alcance (MVP) y herramientas separadas

**Diferido a fases futuras (documentado, no en v1):**
- **Fase 2 — Hook detector de "tibias" (Claude-Code-only):** un hook (`claude-code-hooks`) que detecta respuestas tibias (primera idea plausible, poca divergencia) y reinyecta presión. Difícil de calibrar; requiere saber primero qué es "tibio" en la práctica. No portable a OpenCode.
- **Fase 3 — Modo full-auto:** el plugin decide solo cuándo meter divergencia, sin comandos.

**Responsabilidad del meta-plugin, NO de cambrian:**
- Afinar lentes según meta-gusto / minar el corpus → `growth-engine` (ya habilitado a nivel usuario).

**Herramienta separada (NO va acá):**
- **Advisor "brutal-honesty":** persona de asesor convergente/crítico. Es otro eje (crítica convergente, no divergencia) y framed como asesor personal. Sería un plugin aparte. Meterlo acá ensuciaría el propósito.

---

## 9. Features del catálogo adoptados

Resultado de la auditoría contra `cli-plugin-template` (CATALOG.md v1.17.0).

**Bakeados en la arquitectura (v1):**
- `multi-cli-compat` — Claude Code + OpenCode (§2).
- `agent-pipeline` + `parallel-agents` — forma del workflow 6 lentes → juez (§3).
- `data-gateway` — abstracción de persistencia del corpus (§6).
- `externalized-config` — nº lentes / ideas / ventana anti-rep (§4).
- `vocabulary-guardian` — nombres de lentes + status del corpus (§4).
- `bundled-scripts` — lectura/dedupe determinista del corpus (§6).

**Al scaffoldear (higiene dev/publish, alto valor/bajo costo):**
- `versioning`, `docs-conventions`, `health-check`, `git-hooks`, `portability-audit`.
- `skill-structure-audit` — fuerza modularización (`SKILL.md` solo instrucciones, lógica → `scripts/`, plantillas → `references/`); enganchar en pre-commit/CI.
- `skill-authoring` — convenciones CSO para que skill y command disparen.

**Práctica durante el build (no es un componente del plugin):**
- `plugin-capture-learning` — cada vez que aparezca un gotcha de compatibilidad CC↔OpenCode durante la construcción, capturarlo como `signal:discovery` en el store de evolución del meta-plugin.

**Quality / fase 2:**
- `skill-evals` — verificar que el skill liviano dispare cuando se piden ideas (optimizar `description`/CSO). Claude-Code-only.

**Descartados para este plugin:**
- `growth-engine` (responsabilidad del meta-plugin ya activo, §7), `proposal-gate` (persistir ideas no es irreversible), `mcp-*` (no se envuelve MCP externo), `session-memory` como base (es claude-code-only; la persistencia portable la da `data-gateway`).

---

## 10. Componentes del MVP (v1)

| Componente | Tipo | Función |
|---|---|---|
| `skill` divergencia inline | Skill | Auto-activa; fuerza divergencia en una sola cabeza. Portable. |
| `/brainstorm-extremo` | Command | Dispara el fan-out pesado. Portable. |
| workflow 6 lentes + juez | Workflow / subagentes | Divergencia multi-agente paralela + síntesis. Determinista en CC, subagentes en OpenCode. |
| `bin/lib/` + `config/` | Gateway + config | Lee/escribe corpus externo; anti-repetición; lentes configurables. |
| `health-check` | Skill | Diagnóstico (versión, skills, MCPs). |

**Trigger del MVP:** solo explícito (comando + auto-activación del skill). Sin hooks.

---

## 11. Decisiones registradas (trazabilidad)

1. Es un **plugin completo**, no un skill suelto. *(2026-06-12)*
2. **Domain-agnostic**, no específico de marketing.
3. Núcleo **en capas**: skill liviano + workflow pesado.
4. Trigger **solo explícito** (A) en MVP; hook (B) y full-auto (C) diferidos.
5. Output **crudo + síntesis** (B).
6. Persistencia **fuera del plugin** + aprendizaje **solo anti-repetición** (A) en MVP.
7. Brutal-honesty advisor **excluido** (C).
8. Set default: **6 lentes** (se agregaron First Principles y Restricción Absurda).
9. Nombre: **cambrian-plugin**.
10. **Multi-CLI: Claude Code + OpenCode** (`multi-cli-compat`). Orquestación determinista del workflow = CC-only; paridad funcional en OpenCode vía subagentes.
11. **Aprendizaje = responsabilidad del meta-plugin** `cli-plugin-template` (ya habilitado a nivel usuario). cambrian no re-implementa growth.
12. Features del catálogo adoptados: `multi-cli-compat`, `agent-pipeline`, `parallel-agents`, `data-gateway`, `externalized-config`, `vocabulary-guardian`, `bundled-scripts` (v1) + higiene al scaffoldear.
