import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_health_skill_frontmatter():
    text = (ROOT / "skills" / "cambrian-health" / "SKILL.md").read_text(encoding="utf-8")
    assert text.startswith("---")
    assert re.search(r"^name:\s*cambrian-health\s*$", text, re.MULTILINE)


def test_health_script_runs_and_reports():
    script = ROOT / "skills" / "cambrian-health" / "scripts" / "check.sh"
    r = subprocess.run(
        ["bash", str(script)],
        capture_output=True, text=True,
        env={"CLAUDE_PLUGIN_ROOT": str(ROOT), "HOME": "/tmp", "PATH": "/usr/bin:/bin"},
    )
    assert r.returncode == 0
    assert "cambrian-plugin v" in r.stdout
