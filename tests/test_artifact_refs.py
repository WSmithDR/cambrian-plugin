import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "bin" / "cambrian"


def _cli_ok(args):
    """True si `bin/cambrian <args> --help` sale 0 (subcomando válido)."""
    r = subprocess.run(
        [sys.executable, str(BIN), *args, "--help"],
        capture_output=True,
        text=True,
    )
    return r.returncode == 0


def test_skill_file_has_frontmatter():
    text = (ROOT / "skills" / "diverge" / "SKILL.md").read_text(encoding="utf-8")
    assert text.startswith("---")
    assert re.search(r"^name:\s*diverge\s*$", text, re.MULTILINE)
    assert re.search(r"^description:\s*\S", text, re.MULTILINE)


def test_command_file_has_frontmatter():
    text = (ROOT / "commands" / "brainstorm-extremo.md").read_text(encoding="utf-8")
    assert text.startswith("---")
    assert re.search(r"^description:\s*\S", text, re.MULTILINE)


def test_command_references_only_real_cli_subcommands():
    text = (ROOT / "commands" / "brainstorm-extremo.md").read_text(encoding="utf-8")
    # Cada `$CAMBRIAN <grupo> <cmd>` referenciado debe resolver.
    refs = set(re.findall(r"\$CAMBRIAN\s+(\w+)\s+(\w+)", text))
    assert refs, "el command debería referenciar subcomandos de $CAMBRIAN"
    for group, cmd in refs:
        assert _cli_ok([group, cmd]), f"subcomando inexistente: cambrian {group} {cmd}"


def test_command_references_lenses_group():
    text = (ROOT / "commands" / "brainstorm-extremo.md").read_text(encoding="utf-8")
    assert re.search(r"\$CAMBRIAN\s+lenses", text)
    assert _cli_ok(["lenses"])


def test_command_defines_rooted_cambrian_var():
    text = (ROOT / "commands" / "brainstorm-extremo.md").read_text(encoding="utf-8")
    assert 'CAMBRIAN="$CLAUDE_PLUGIN_ROOT/bin/cambrian"' in text, (
        "el command debe definir CAMBRIAN rooteado a $CLAUDE_PLUGIN_ROOT"
    )
