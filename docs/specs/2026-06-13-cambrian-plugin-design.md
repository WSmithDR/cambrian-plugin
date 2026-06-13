# cambrian-plugin — Diseño (spec)

**Fecha:** 2026-06-13
**Estado:** Diseño aprobado por secciones · pendiente revisión final del usuario
**Repo:** `github.com:WSmithDR/cambrian-plugin`

---

## 1. Qué es y por qué

`cambrian-plugin` es un plugin de Claude Code **domain-agnostic** cuyo único objetivo es **aumentar la creatividad** de las ideas/respuestas de Claude.

**Insight base:** la creatividad en un LLM no se logra cambiando el modelo, sino el *proceso*. Hay que **forzar divergencia antes de converger** y romper el sesgo de la "primera respuesta plausible". El plugin no inventa inteligencia nueva: estructura el proceso para que la inteligencia existente explore más lejos antes de elegir.

**Nombre:** la explosión cámbrica (estallido súbito de formas diversas antes de que la selección converja) es la metáfora exacta del plugin: estallido de ideas → selección.

**Alcance:** 100% divergencia creativa. No hace coaching, no hace crítica de vida personal, no es un asesor. (Ver §7.)

---

## 2. Arquitectura: dos capas

```
cambrian-plugin/
├── skill        (capa liviana — siempre disponible, auto-activada)
│     └── metodología inline de divergencia en una sola cabeza:
│         forzar cantidad antes de calidad (N ideas antes de evaluar),
│         inversión, analogías forzadas, restricciones. Barato.
│
├── command  /brainstorm-extremo   (dispara la capa pesada)
│     └── invoca el workflow
│
├── workflow     (capa pesada — multi-agente)
│     ├── 6 lentes divergentes en paralelo (mandatos contradictorios)
│     ├── lee corpus previo del topic → "esto ya se exploró, andá más lejos"
│     ├── devuelve CRUDO por lente + SÍNTESIS del juez
│     └── persiste todo lo generado al corpus externo
│
└── (sin persistencia propia — el corpus vive AFUERA, ver §5)
```

**Flujo de uso:**
- Pedís ideas de forma normal → el **skill** se auto-activa y fuerza divergencia en una sola pasada. Barato, siempre disponible.
- Querés el martillo grande → `/brainstorm-extremo` → el **workflow** lanza las 6 lentes en paralelo, lee el corpus para no repetirse, y devuelve crudo + síntesis.

---

## 3. Las 6 lentes + juez (workflow pesado)

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

**Configurable:** en v1 vienen estas 6 lentes, pero el número y los mandatos se pueden editar. (El afinado automático de lentes es trabajo del meta-plugin — fase 2, §6.)

---

## 4. Output

`/brainstorm-extremo` devuelve **crudo + síntesis** (decisión deliberada):

1. **Crudo por lente:** las ideas sin filtrar de cada una de las 6 lentes. Acá está el material "loco" que normalmente se descarta y que es justo lo que hace al plugin distinto.
2. **Síntesis del juez:** las mejores ideas filtradas, combinadas y rankeadas.

Mostrar el crudo es intencional: en creatividad el valor está en ver el espacio completo de ideas, no solo lo que el juez dejó pasar.

---

## 5. Persistencia (corpus externo)

**Principio clave: el corpus vive FUERA del directorio del plugin.** `cambrian-plugin` no posee la persistencia — solo **lee y escribe** contra un data dir externo administrado por el **meta-plugin** (§6). Esto sigue el patrón `ANKIFY_DATA_DIR` del ecosistema del usuario.

- **Formato:** append-only. Cada idea generada se guarda con:
  `{ topic, lente, texto, status: generada | aceptada | rechazada, timestamp }`
- **Se guarda todo:** tanto lo aceptado como lo rechazado.
- **Anti-repetición (el uso killer):** antes de cada corrida, el workflow lee el corpus de ese `topic` y le pasa a las lentes un resumen de "esto ya se exploró, andá más lejos". Acá la persistencia **aumenta** la novedad en vez de matarla.

**Decisión de diseño crítica — por qué solo anti-repetición y no "reusá lo que funcionó":** un sistema de aprendizaje ingenuo (re-sugerir lo que se aceptó antes) produce **regresión a la media** y vuelve al plugin *menos* creativo con el tiempo. El MVP por eso aprende **solo** a no repetirse. Aprender el "meta-gusto" del usuario (qué lentes retiene vs descarta) queda para fase 2 y lo hace el meta-plugin, ajustando *proceso/lentes*, nunca reusando *contenido*.

---

## 6. Relación con el meta-plugin

Existe (o existirá) un **meta-plugin** separado cuyo trabajo es mejorar las ideas / administrar el aprendizaje. Reparto de responsabilidades:

- **`cambrian-plugin`:** genera divergencia, lee/escribe el corpus, aplica anti-repetición. Tonto respecto del aprendizaje.
- **Meta-plugin:** posee el data dir, mina el corpus, afina lentes según meta-gusto, etc.

`cambrian-plugin` debe funcionar de forma autónoma (con un data dir por defecto) aunque el meta-plugin no esté presente.

---

## 7. Fuera de alcance (MVP) y herramientas separadas

**Diferido a fases futuras (documentado, no en v1):**
- **Fase 2 — Hook detector de "tibias":** un hook que detecta respuestas tibias (primera idea plausible, poca divergencia) y reinyecta presión automáticamente. Difícil de calibrar; requiere saber primero qué es "tibio" en la práctica.
- **Fase 2 — Aprendizaje de meta-gusto:** afinar lentes/prompts según qué retiene el usuario (lo hace el meta-plugin).
- **Fase 3 — Modo full-auto:** el plugin decide solo cuándo meter divergencia, sin comandos.

**Herramienta separada (NO va acá):**
- **Advisor "brutal-honesty":** persona de asesor convergente/crítico (honestidad brutal, exponer puntos ciegos, plan priorizado). Es otro eje (crítica convergente, no divergencia) y framed como asesor personal. Sería un plugin aparte. Meterlo acá ensuciaría el propósito de `cambrian-plugin`.

---

## 8. Componentes del MVP (v1)

| Componente | Tipo | Función |
|---|---|---|
| `skill` divergencia inline | Skill | Auto-activa; fuerza divergencia en una sola cabeza. |
| `/brainstorm-extremo` | Command | Dispara el workflow pesado. |
| workflow 6 lentes + juez | Workflow | Divergencia multi-agente paralela + síntesis. |
| lectura/escritura de corpus | Lib | Lee/escribe el data dir externo; aplica anti-repetición. |

**Trigger del MVP:** solo explícito (comando + auto-activación del skill). Sin hooks.

---

## 9. Decisiones registradas (trazabilidad del brainstorming)

1. Es un **plugin completo**, no un skill suelto. *(2026-06-12)*
2. **Domain-agnostic**, no específico de marketing.
3. Núcleo **en capas**: skill liviano + workflow pesado.
4. Trigger **solo explícito** (A) en MVP; hook (B) y full-auto (C) diferidos.
5. Output **crudo + síntesis** (B).
6. Persistencia **fuera del plugin** + aprendizaje **solo anti-repetición** (A) en MVP.
7. Brutal-honesty advisor **excluido** de este plugin (C).
8. Set default: **6 lentes** (se agregaron First Principles y Restricción Absurda).
9. Nombre: **cambrian-plugin**.
