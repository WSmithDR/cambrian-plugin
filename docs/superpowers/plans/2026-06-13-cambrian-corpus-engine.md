# cambrian-plugin — Plan 1: Fundación + Motor de corpus

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffoldear `cambrian-plugin` y construir el motor de corpus persistente (append-only, externo, con anti-repetición) que las capas de divergencia consumirán después.

**Architecture:** CLI Python único (`bin/cambrian`) sobre `bin/lib/` (paths/config/gateway), espejando las convenciones de `ankify`. Toda la persistencia resuelve contra `$CAMBRIAN_DATA_DIR` (default `~/.local/share/cambrian/`), nunca en el repo. El corpus es un archivo JSONL append-only por topic con records de tipo `idea` y `status` que se foldean al leer. Config de comportamiento (lentes, umbrales, vocabulario) en `config/*.json` leído en runtime.

**Tech Stack:** Python 3 (stdlib only: `argparse`, `json`, `hashlib`, `time`, `pathlib`), pytest. Sin dependencias externas.

**Alcance:** Este es el **Plan 1 de 3**. Plan 2 = capas de divergencia (skill liviano + workflow `/brainstorm-extremo`). Plan 3 = publish/higiene (multi-CLI manifests, health-check, versioning, git-hooks, CI audits, registro en meta-plugin). Cada plan deja software funcionando y testeable.

**Convención clave (de ankify):** `data_dir()` se resuelve en **call-time** (función que lee el env var en cada llamada), no en import-time. Esto permite que los tests seteen `CAMBRIAN_DATA_DIR=tmp_path` y nunca toquen el data dir real. Preservar esto al editar `bin/lib/`.

---

### Task 0: Scaffold del esqueleto del plugin

**Files:**
- Create: `.claude-plugin/plugin.json`
- Create: `.claude-plugin/marketplace.json`
- Create: `.gitignore`
- Create: `pytest.ini`
- Create: `bin/lib/__init__.py` (vacío)
- Create: `tests/__init__.py` (vacío)

- [ ] **Step 1: Crear `.claude-plugin/plugin.json`**

```json
{
  "name": "cambrian-plugin",
  "version": "0.1.0",
  "description": "Aumenta la creatividad forzando divergencia multi-agente antes de converger. Domain-agnostic. Skill liviano de divergencia inline + workflow pesado /brainstorm-extremo (6 lentes + juez) con memoria anti-repetición.",
  "author": {
    "name": "WSmithDR",
    "url": "https://github.com/WSmithDR"
  },
  "repository": "https://github.com/WSmithDR/cambrian-plugin",
  "homepage": "https://github.com/WSmithDR/cambrian-plugin#readme",
  "license": "MIT",
  "keywords": [
    "claude-code",
    "claude-code-plugin",
    "creativity",
    "brainstorming",
    "multi-agent",
    "divergent-thinking"
  ],
  "skills": "./skills/"
}
```

- [ ] **Step 2: Crear `.claude-plugin/marketplace.json`**

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
      "description": "Aumenta la creatividad forzando divergencia multi-agente antes de converger. Domain-agnostic."
    }
  ]
}
```

- [ ] **Step 3: Crear `.gitignore`**

```gitignore
__pycache__/
*.pyc
.pytest_cache/
.DS_Store
```

- [ ] **Step 4: Crear `pytest.ini`**

```ini
[pytest]
testpaths = tests
addopts = -q
```

- [ ] **Step 5: Crear paquetes Python vacíos**

Crear `bin/lib/__init__.py` con contenido vacío (un comentario):

```python
# cambrian-plugin lib package
```

Crear `tests/__init__.py` con contenido vacío:

```python
```

- [ ] **Step 6: Commit**

```bash
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json .gitignore pytest.ini bin/lib/__init__.py tests/__init__.py
git commit -m "chore: scaffold cambrian-plugin skeleton"
```

---

### Task 1: `paths.py` — resolución de data dir + slug

**Files:**
- Create: `bin/lib/paths.py`
- Create: `tests/conftest.py`
- Test: `tests/test_paths.py`

- [ ] **Step 1: Crear `tests/conftest.py`** (añade `bin/` al path e inyecta un data dir temporal en cada test)

```python
import sys
from pathlib import Path

import pytest

BIN = Path(__file__).resolve().parents[1] / "bin"
sys.path.insert(0, str(BIN))


@pytest.fixture(autouse=True)
def _data_dir(tmp_path, monkeypatch):
    """Redirige CAMBRIAN_DATA_DIR a un tmp por test. Nunca toca el real."""
    monkeypatch.setenv("CAMBRIAN_DATA_DIR", str(tmp_path))
    yield
```

- [ ] **Step 2: Escribir el test que falla** (`tests/test_paths.py`)

```python
import os
from pathlib import Path

from lib import paths


def test_data_dir_honors_env(tmp_path):
    os.environ["CAMBRIAN_DATA_DIR"] = str(tmp_path / "custom")
    assert paths.data_dir() == tmp_path / "custom"


def test_data_dir_default_when_unset(monkeypatch):
    monkeypatch.delenv("CAMBRIAN_DATA_DIR", raising=False)
    assert paths.data_dir() == Path.home() / ".local" / "share" / "cambrian"


def test_corpus_file_path(tmp_path):
    os.environ["CAMBRIAN_DATA_DIR"] = str(tmp_path)
    assert paths.corpus_file("docker") == tmp_path / "corpus" / "docker.jsonl"


def test_slugify():
    assert paths.slugify("Aprender Docker!") == "aprender-docker"
    assert paths.slugify("  GraphQL  vs  REST ") == "graphql-vs-rest"
    assert paths.slugify("") == "untitled"
```

- [ ] **Step 3: Correr el test para verificar que falla**

Run: `pytest tests/test_paths.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'lib.paths'`

- [ ] **Step 4: Implementar `bin/lib/paths.py`**

```python
"""
cambrian-plugin path resolution.
Toda la persistencia resuelve contra CAMBRIAN_DATA_DIR (~/.local/share/cambrian).
Las funciones leen el env en CALL-TIME (no import-time) para que los tests
puedan redirigir el data dir sin tocar el real.
"""

import os
import re
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]


def data_dir() -> Path:
    return Path(
        os.environ.get(
            "CAMBRIAN_DATA_DIR", Path.home() / ".local" / "share" / "cambrian"
        )
    )


def corpus_dir() -> Path:
    return data_dir() / "corpus"


def corpus_file(topic_slug: str) -> Path:
    return corpus_dir() / f"{topic_slug}.jsonl"


def slugify(topic: str) -> str:
    s = topic.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "untitled"
```

- [ ] **Step 5: Correr el test para verificar que pasa**

Run: `pytest tests/test_paths.py -v`
Expected: PASS (4 tests)

- [ ] **Step 6: Commit**

```bash
git add bin/lib/paths.py tests/conftest.py tests/test_paths.py
git commit -m "feat: data dir resolution and slugify in paths.py"
```

---

### Task 2: `config.py` + archivos de config

**Files:**
- Create: `config/vocabulary.json`
- Create: `config/lenses.json`
- Create: `config/thresholds.json`
- Create: `bin/lib/config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Crear `config/vocabulary.json`** (fuente única de status del corpus)

```json
{
  "statuses": ["generada", "aceptada", "rechazada"]
}
```

- [ ] **Step 2: Crear `config/lenses.json`** (las 6 lentes divergentes, configurables)

```json
{
  "lenses": [
    { "name": "minimalista", "mandate": "Proponé la idea más simple y reductiva posible. Quitá, no agregues. Si algo se puede eliminar, eliminalo." },
    { "name": "maximalista", "mandate": "Proponé la versión más ambiciosa y excesiva posible, sin miedo al absurdo ni al presupuesto. Llevá la idea al extremo." },
    { "name": "contrarian", "mandate": "Hacé lo opuesto a la respuesta obvia. Invertí el problema. Si todos van por la izquierda, andá por la derecha." },
    { "name": "interdisciplina", "mandate": "Traé un concepto de un campo completamente ajeno (biología, música, arquitectura, deportes) y forzá la analogía con el problema." },
    { "name": "first-principles", "mandate": "Descomponé el problema a sus átomos irreducibles y reconstruí una solución desde cero, sin asumir nada de cómo se hace habitualmente." },
    { "name": "restriccion-absurda", "mandate": "Resolvé el problema bajo una restricción imposible (sin presupuesto, en 1 minuto, sin texto, sin internet). La restricción fuerza la creatividad." }
  ]
}
```

- [ ] **Step 3: Crear `config/thresholds.json`** (umbrales de comportamiento)

```json
{
  "ideas_per_lens": 5,
  "anti_repetition_window": 200
}
```

- [ ] **Step 4: Escribir el test que falla** (`tests/test_config.py`)

```python
from lib import config


def test_statuses():
    assert config.statuses() == ["generada", "aceptada", "rechazada"]


def test_lenses_has_six():
    lenses = config.lenses()
    assert len(lenses) == 6
    names = [l["name"] for l in lenses]
    assert "minimalista" in names
    assert "restriccion-absurda" in names
    for l in lenses:
        assert l["mandate"].strip()


def test_thresholds():
    t = config.thresholds()
    assert t["ideas_per_lens"] == 5
    assert t["anti_repetition_window"] == 200
```

- [ ] **Step 5: Correr el test para verificar que falla**

Run: `pytest tests/test_config.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'lib.config'`

- [ ] **Step 6: Implementar `bin/lib/config.py`**

```python
"""
cambrian-plugin config reader.
Lee config/*.json del repo (PLUGIN_ROOT/config), no del data dir.
Comportamiento externalizado: lentes, umbrales y vocabulario se editan en JSON.
"""

import json

from .paths import PLUGIN_ROOT


def _config_dir():
    return PLUGIN_ROOT / "config"


def load(name: str) -> dict:
    return json.loads((_config_dir() / name).read_text(encoding="utf-8"))


def lenses() -> list:
    return load("lenses.json")["lenses"]


def thresholds() -> dict:
    return load("thresholds.json")


def vocabulary() -> dict:
    return load("vocabulary.json")


def statuses() -> list:
    return vocabulary()["statuses"]
```

- [ ] **Step 7: Correr el test para verificar que pasa**

Run: `pytest tests/test_config.py -v`
Expected: PASS (3 tests)

- [ ] **Step 8: Commit**

```bash
git add config/vocabulary.json config/lenses.json config/thresholds.json bin/lib/config.py tests/test_config.py
git commit -m "feat: externalized config (lenses, thresholds, vocabulary)"
```

---

### Task 3: `gateway.py` — append de ideas al corpus

**Files:**
- Create: `bin/lib/gateway.py`
- Test: `tests/test_gateway_add.py`

- [ ] **Step 1: Escribir el test que falla** (`tests/test_gateway_add.py`)

```python
import json

import pytest

from lib import gateway, paths


def test_add_idea_creates_jsonl_line():
    idea_id = gateway.add_idea("Docker", "minimalista", "Un solo contenedor sin orquestador")
    assert isinstance(idea_id, str) and len(idea_id) == 8

    f = paths.corpus_file("docker")
    assert f.exists()
    lines = f.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1

    rec = json.loads(lines[0])
    assert rec["type"] == "idea"
    assert rec["topic"] == "Docker"
    assert rec["lens"] == "minimalista"
    assert rec["text"] == "Un solo contenedor sin orquestador"
    assert rec["status"] == "generada"
    assert rec["id"] == idea_id
    assert rec["ts"]


def test_add_idea_default_status_is_generada():
    gateway.add_idea("Docker", "contrarian", "No uses Docker")
    rec = json.loads(paths.corpus_file("docker").read_text(encoding="utf-8").splitlines()[0])
    assert rec["status"] == "generada"


def test_add_idea_rejects_unknown_status():
    with pytest.raises(ValueError, match="unknown status"):
        gateway.add_idea("Docker", "minimalista", "x", status="inventado")


def test_add_idea_rejects_empty_lens():
    with pytest.raises(ValueError, match="lens"):
        gateway.add_idea("Docker", "", "x")


def test_add_idea_is_append_only():
    gateway.add_idea("Docker", "minimalista", "idea uno")
    gateway.add_idea("Docker", "maximalista", "idea dos")
    lines = paths.corpus_file("docker").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2


def test_same_content_yields_same_id():
    a = gateway.add_idea("Docker", "minimalista", "misma idea")
    b = gateway.add_idea("Docker", "minimalista", "misma idea")
    assert a == b
```

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `pytest tests/test_gateway_add.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'lib.gateway'`

- [ ] **Step 3: Implementar `bin/lib/gateway.py`** (solo lo necesario para estos tests)

```python
"""
cambrian-plugin corpus gateway.
El corpus es append-only: un JSONL por topic en $CAMBRIAN_DATA_DIR/corpus/.
Records de tipo 'idea' y 'status'; el status vigente se foldea al leer.
Las skills NUNCA escriben disco directo: pasan por bin/cambrian, que llama acá.
"""

import hashlib
import json
import time

from . import config
from .paths import corpus_dir, corpus_file, slugify


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _gen_id(topic: str, lens: str, text: str) -> str:
    h = hashlib.sha256(f"{topic}|{lens}|{text}".encode("utf-8")).hexdigest()
    return h[:8]


def _validate_status(status: str) -> None:
    valid = config.statuses()
    if status not in valid:
        raise ValueError(f"unknown status '{status}'; valid: {valid}")


def _append(topic: str, rec: dict) -> None:
    corpus_dir().mkdir(parents=True, exist_ok=True)
    with corpus_file(slugify(topic)).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def add_idea(topic: str, lens: str, text: str, status: str = "generada") -> str:
    if not lens or not lens.strip():
        raise ValueError("lens must be a non-empty string")
    _validate_status(status)
    idea_id = _gen_id(topic, lens, text)
    _append(
        topic,
        {
            "id": idea_id,
            "type": "idea",
            "topic": topic,
            "lens": lens,
            "text": text,
            "status": status,
            "ts": _now(),
        },
    )
    return idea_id
```

- [ ] **Step 4: Correr el test para verificar que pasa**

Run: `pytest tests/test_gateway_add.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add bin/lib/gateway.py tests/test_gateway_add.py
git commit -m "feat: append-only idea writes in gateway"
```

---

### Task 4: `gateway.py` — leer ideas con fold de status

**Files:**
- Modify: `bin/lib/gateway.py` (agregar `mark`, `_read_records`, `list_ideas`)
- Test: `tests/test_gateway_read.py`

- [ ] **Step 1: Escribir el test que falla** (`tests/test_gateway_read.py`)

```python
import pytest

from lib import gateway


def test_list_empty_topic_returns_empty():
    assert gateway.list_ideas("inexistente") == []


def test_list_returns_ideas_in_order():
    gateway.add_idea("Docker", "minimalista", "primera")
    gateway.add_idea("Docker", "maximalista", "segunda")
    ideas = gateway.list_ideas("Docker")
    assert [i["text"] for i in ideas] == ["primera", "segunda"]


def test_mark_updates_status_via_fold():
    idea_id = gateway.add_idea("Docker", "minimalista", "candidata")
    gateway.mark("Docker", idea_id, "aceptada")
    ideas = gateway.list_ideas("Docker")
    assert len(ideas) == 1
    assert ideas[0]["status"] == "aceptada"


def test_latest_status_wins():
    idea_id = gateway.add_idea("Docker", "minimalista", "candidata")
    gateway.mark("Docker", idea_id, "aceptada")
    gateway.mark("Docker", idea_id, "rechazada")
    ideas = gateway.list_ideas("Docker")
    assert ideas[0]["status"] == "rechazada"


def test_mark_rejects_unknown_status():
    idea_id = gateway.add_idea("Docker", "minimalista", "x")
    with pytest.raises(ValueError, match="unknown status"):
        gateway.mark("Docker", idea_id, "inventado")


def test_mark_unknown_id_is_ignored_on_read():
    gateway.add_idea("Docker", "minimalista", "real")
    gateway.mark("Docker", "ffffffff", "aceptada")
    ideas = gateway.list_ideas("Docker")
    assert len(ideas) == 1
    assert ideas[0]["status"] == "generada"
```

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `pytest tests/test_gateway_read.py -v`
Expected: FAIL con `AttributeError: module 'lib.gateway' has no attribute 'list_ideas'`

- [ ] **Step 3: Implementar — agregar a `bin/lib/gateway.py`** (al final del archivo)

```python
def mark(topic: str, idea_id: str, status: str) -> None:
    _validate_status(status)
    _append(topic, {"type": "status", "id": idea_id, "status": status, "ts": _now()})


def _read_records(topic: str) -> list:
    f = corpus_file(slugify(topic))
    if not f.exists():
        return []
    records = []
    for line in f.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


def list_ideas(topic: str) -> list:
    records = _read_records(topic)
    ideas = {}
    order = []
    for r in records:
        if r.get("type") == "idea":
            if r["id"] not in ideas:
                order.append(r["id"])
            ideas[r["id"]] = dict(r)
    for r in records:
        if r.get("type") == "status" and r["id"] in ideas:
            ideas[r["id"]]["status"] = r["status"]
    return [ideas[i] for i in order]
```

- [ ] **Step 4: Correr el test para verificar que pasa**

Run: `pytest tests/test_gateway_read.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add bin/lib/gateway.py tests/test_gateway_read.py
git commit -m "feat: read ideas with status fold and mark"
```

---

### Task 5: `gateway.py` — anti-repetición (`seen_texts`)

**Files:**
- Modify: `bin/lib/gateway.py` (agregar `_normalize`, `seen_texts`)
- Test: `tests/test_gateway_seen.py`

- [ ] **Step 1: Escribir el test que falla** (`tests/test_gateway_seen.py`)

```python
from lib import gateway


def test_seen_empty_topic():
    assert gateway.seen_texts("inexistente") == []


def test_seen_returns_unique_texts():
    gateway.add_idea("Docker", "minimalista", "idea A")
    gateway.add_idea("Docker", "maximalista", "idea B")
    seen = gateway.seen_texts("Docker")
    assert "idea A" in seen
    assert "idea B" in seen


def test_seen_dedupes_normalized_text():
    gateway.add_idea("Docker", "minimalista", "Idea Repetida")
    gateway.add_idea("Docker", "maximalista", "idea   repetida")
    seen = gateway.seen_texts("Docker")
    assert len(seen) == 1


def test_seen_respects_limit_window():
    for i in range(10):
        gateway.add_idea("Docker", "minimalista", f"idea {i}")
    seen = gateway.seen_texts("Docker", limit=3)
    assert len(seen) == 3
    # devuelve las más recientes
    assert seen == ["idea 7", "idea 8", "idea 9"]


def test_seen_default_limit_from_config():
    # con pocas ideas, el window default (200) no recorta
    gateway.add_idea("Docker", "minimalista", "una")
    assert gateway.seen_texts("Docker") == ["una"]
```

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `pytest tests/test_gateway_seen.py -v`
Expected: FAIL con `AttributeError: module 'lib.gateway' has no attribute 'seen_texts'`

- [ ] **Step 3: Implementar — agregar a `bin/lib/gateway.py`** (al final del archivo)

```python
def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def seen_texts(topic: str, limit: int = None) -> list:
    if limit is None:
        limit = config.thresholds().get("anti_repetition_window", 200)
    unique = []
    norm_seen = set()
    for idea in list_ideas(topic):
        norm = _normalize(idea["text"])
        if norm not in norm_seen:
            norm_seen.add(norm)
            unique.append(idea["text"])
    return unique[-limit:]
```

- [ ] **Step 4: Correr el test para verificar que pasa**

Run: `pytest tests/test_gateway_seen.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add bin/lib/gateway.py tests/test_gateway_seen.py
git commit -m "feat: anti-repetition seen_texts with normalized dedup and window"
```

---

### Task 6: `bin/cambrian` — CLI dispatcher

**Files:**
- Create: `bin/cambrian`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Escribir el test que falla** (`tests/test_cli.py`) — invoca el CLI como subproceso real

```python
import json
import subprocess
import sys
from pathlib import Path

BIN = Path(__file__).resolve().parents[1] / "bin" / "cambrian"


def _run(args, env, stdin=None):
    return subprocess.run(
        [sys.executable, str(BIN), *args],
        env=env,
        input=stdin,
        capture_output=True,
        text=True,
    )


def _env(tmp_path):
    import os

    e = dict(os.environ)
    e["CAMBRIAN_DATA_DIR"] = str(tmp_path)
    return e


def test_cli_add_then_list(tmp_path):
    env = _env(tmp_path)
    add = _run(["corpus", "add", "--topic", "Docker", "--lens", "minimalista", "--text", "idea cli"], env)
    assert add.returncode == 0
    idea_id = add.stdout.strip()
    assert len(idea_id) == 8

    listed = _run(["corpus", "list", "--topic", "Docker"], env)
    assert listed.returncode == 0
    ideas = json.loads(listed.stdout)
    assert ideas[0]["text"] == "idea cli"
    assert ideas[0]["id"] == idea_id


def test_cli_add_reads_stdin_with_dash(tmp_path):
    env = _env(tmp_path)
    add = _run(
        ["corpus", "add", "--topic", "Docker", "--lens", "contrarian", "--text", "-"],
        env,
        stdin="idea desde stdin",
    )
    assert add.returncode == 0
    listed = _run(["corpus", "list", "--topic", "Docker"], env)
    ideas = json.loads(listed.stdout)
    assert ideas[0]["text"] == "idea desde stdin"


def test_cli_mark_and_seen(tmp_path):
    env = _env(tmp_path)
    add = _run(["corpus", "add", "--topic", "Docker", "--lens", "minimalista", "--text", "marcame"], env)
    idea_id = add.stdout.strip()

    mark = _run(["corpus", "mark", "--topic", "Docker", "--id", idea_id, "--status", "aceptada"], env)
    assert mark.returncode == 0

    listed = _run(["corpus", "list", "--topic", "Docker"], env)
    assert json.loads(listed.stdout)[0]["status"] == "aceptada"

    seen = _run(["corpus", "seen", "--topic", "Docker"], env)
    assert json.loads(seen.stdout) == ["marcame"]


def test_cli_unknown_status_exits_nonzero(tmp_path):
    env = _env(tmp_path)
    r = _run(["corpus", "add", "--topic", "Docker", "--lens", "minimalista", "--text", "x", "--status", "inventado"], env)
    assert r.returncode != 0
    assert "unknown status" in r.stderr
```

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `pytest tests/test_cli.py -v`
Expected: FAIL — `bin/cambrian` no existe (los subprocesos devuelven returncode != 0 con error de "No such file" o el assert de stdout falla)

- [ ] **Step 3: Implementar `bin/cambrian`**

```python
#!/usr/bin/env python3
"""
cambrian — CLI unificado de persistencia del plugin.
Punto de entrada único: las skills nunca tocan disco; shellean a este CLI.
Grupos de subcomandos: corpus (add/list/seen/mark).
Los args de texto aceptan '-' para leer de stdin.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import gateway  # noqa: E402


def _read_text(arg: str) -> str:
    if arg == "-":
        return sys.stdin.read().strip()
    return arg


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cambrian")
    groups = parser.add_subparsers(dest="group", required=True)

    corpus = groups.add_parser("corpus", help="operaciones sobre el corpus de ideas")
    cmds = corpus.add_subparsers(dest="cmd", required=True)

    add = cmds.add_parser("add", help="append una idea")
    add.add_argument("--topic", required=True)
    add.add_argument("--lens", required=True)
    add.add_argument("--text", required=True, help="texto de la idea, o '-' para stdin")
    add.add_argument("--status", default="generada")

    lst = cmds.add_parser("list", help="lista las ideas de un topic (JSON)")
    lst.add_argument("--topic", required=True)

    seen = cmds.add_parser("seen", help="textos únicos ya explorados (anti-repetición)")
    seen.add_argument("--topic", required=True)
    seen.add_argument("--limit", type=int, default=None)

    mark = cmds.add_parser("mark", help="cambia el status de una idea")
    mark.add_argument("--topic", required=True)
    mark.add_argument("--id", required=True)
    mark.add_argument("--status", required=True)

    return parser


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.group == "corpus":
            if args.cmd == "add":
                print(gateway.add_idea(args.topic, args.lens, _read_text(args.text), args.status))
            elif args.cmd == "list":
                print(json.dumps(gateway.list_ideas(args.topic), ensure_ascii=False, indent=2))
            elif args.cmd == "seen":
                print(json.dumps(gateway.seen_texts(args.topic, args.limit), ensure_ascii=False, indent=2))
            elif args.cmd == "mark":
                gateway.mark(args.topic, args.id, args.status)
                print("ok")
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Hacer ejecutable `bin/cambrian`**

Run: `chmod +x bin/cambrian`
Expected: sin output, exit 0

- [ ] **Step 5: Correr el test para verificar que pasa**

Run: `pytest tests/test_cli.py -v`
Expected: PASS (4 tests)

- [ ] **Step 6: Commit**

```bash
git add bin/cambrian tests/test_cli.py
git commit -m "feat: cambrian CLI dispatcher for corpus ops"
```

---

### Task 7: Smoke test + suite completa + README mínimo

**Files:**
- Create: `bin/dev/smoke-test.sh`
- Create: `README.md` (sobrescribe el placeholder actual)

- [ ] **Step 1: Crear `bin/dev/smoke-test.sh`** (round-trip end-to-end en un namespace temporal)

```bash
#!/usr/bin/env bash
# Smoke test de cambrian-plugin: el CLI responde y el corpus hace round-trip.
# Escribe en un data dir temporal; nunca toca el real. Exit 0 = ok.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export CAMBRIAN_DATA_DIR="$TMP"

CLI="python3 $ROOT/bin/cambrian"

echo "1. add idea"
ID="$($CLI corpus add --topic "_smoke_" --lens minimalista --text "idea de smoke")"
[ -n "$ID" ] || { echo "FAIL: add no devolvió id"; exit 1; }

echo "2. list contiene la idea"
$CLI corpus list --topic "_smoke_" | grep -q "idea de smoke" || { echo "FAIL: list"; exit 1; }

echo "3. mark aceptada"
$CLI corpus mark --topic "_smoke_" --id "$ID" --status aceptada >/dev/null
$CLI corpus list --topic "_smoke_" | grep -q '"status": "aceptada"' || { echo "FAIL: mark"; exit 1; }

echo "4. seen devuelve la idea"
$CLI corpus seen --topic "_smoke_" | grep -q "idea de smoke" || { echo "FAIL: seen"; exit 1; }

echo "OK: smoke test passed"
```

- [ ] **Step 2: Hacer ejecutable y correr el smoke test**

Run: `chmod +x bin/dev/smoke-test.sh && bin/dev/smoke-test.sh`
Expected: termina con `OK: smoke test passed`, exit 0

- [ ] **Step 3: Correr la suite completa de pytest**

Run: `pytest`
Expected: PASS — todos los tests (paths, config, gateway add/read/seen, cli) en verde

- [ ] **Step 4: Sobrescribir `README.md`**

```markdown
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
```

- [ ] **Step 5: Commit**

```bash
git add bin/dev/smoke-test.sh README.md
git commit -m "chore: smoke test and README for corpus engine"
```

---

## Self-review (cobertura del spec — Plan 1)

Plan 1 cubre del spec: persistencia externa append-only (§6), data dir `$CAMBRIAN_DATA_DIR` patrón `ANKIFY_DATA_DIR`, anti-repetición (`seen_texts`), `data-gateway` (CLI único, skills no tocan disco), `externalized-config` (lentes/umbrales), `vocabulary-guardian` (status del corpus en `vocabulary.json`), `bundled-scripts` (lógica determinista en `bin/lib`). Status `generada/aceptada/rechazada` consistentes en config, gateway y tests.

**Fuera de Plan 1 (van a Plan 2/3, intencional):** skill liviano, command `/brainstorm-extremo`, workflow 6 lentes + juez, multi-cli manifests (AGENTS.md/opencode.json), health-check, versioning, git-hooks, skill-structure-audit, registro en meta-plugin. El validador estricto de status ya está; el escáner `vocabulary-guardian` como skill se cablea en Plan 2 cuando haya skills que lo invoquen.
```
