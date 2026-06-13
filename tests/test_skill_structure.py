import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_skills_pass_structure_audit():
    r = subprocess.run(
        [sys.executable, str(ROOT / "bin" / "audit-skill-structure.py"), "--threshold", "ERROR"],
        cwd=str(ROOT), capture_output=True, text=True,
    )
    assert r.returncode == 0, f"skill-structure-audit reportó ERRORs:\n{r.stdout}\n{r.stderr}"
