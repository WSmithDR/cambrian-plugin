import json
import os
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
    assert os.path.basename(os.readlink(p)) == "AGENTS.md"


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
