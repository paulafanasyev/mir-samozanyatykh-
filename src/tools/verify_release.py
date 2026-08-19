"""Deterministic release gate for the repository."""
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", "node_modules", ".dart_tool"}
FORBIDDEN_SUFFIXES = {".pyc", ".pyo", ".db", ".log"}

def cleanup_generated():
    for p in ROOT.rglob("*"):
        if p.is_dir() and p.name in FORBIDDEN_DIRS:
            shutil.rmtree(p, ignore_errors=True)
    for p in ROOT.rglob("*"):
        if p.is_file() and p.suffix in FORBIDDEN_SUFFIXES:
            p.unlink(missing_ok=True)

cleanup_generated()
commands = [
    [sys.executable, "tools/security_regression_check.py"],
    [sys.executable, "tools/api_contract_audit.py"],
    [sys.executable, "tools/functional_contract_audit_v8.4.28.py"],
    [sys.executable, "tools/functional_integrity_audit_v8.4.28.py"],
    [sys.executable, "tools/functional_integrity_audit_v8.4.34.py"],
    [sys.executable, "-m", "compileall", "-q", "app", "tests", "tools"],
]
for command in commands:
    print("$", " ".join(command))
    subprocess.run(command, cwd=ROOT, check=True)

cleanup_generated()
bad = []
for p in ROOT.rglob("*"):
    if any(part in FORBIDDEN_DIRS for part in p.parts):
        bad.append(str(p))
    elif p.is_file() and p.suffix in FORBIDDEN_SUFFIXES:
        bad.append(str(p))
if bad:
    print("FORBIDDEN_RELEASE_ARTIFACTS")
    print("\n".join(bad[:100]))
    sys.exit(1)
print("RELEASE_GATE=PASS")
