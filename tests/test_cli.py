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
