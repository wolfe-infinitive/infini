"""
tests/test_requirements_audit.py
Audits the repo to ensure requirements.txt matches actual imports.
If run with  --fix  (e.g.  pytest -v tests/test_requirements_audit.py --fix)
it will automatically update requirements.txt.
"""

import os
import sys
import re
import importlib
import importlib.metadata
from pathlib import Path
import pytest
from stdlib_list import stdlib_list

# === Setup ===
ROOT = Path(__file__).resolve().parents[1]
REQ_FILE = ROOT / "requirements.txt"

# Collect stdlib for current python version
STDLIB_MODULES = set(stdlib_list())

# Mapping for mismatched import/package names
NAME_MAP = {
    "langchain_community": "langchain-community",
    "langchain_core": "langchain-core",
    "langchain_text_splitters": "langchain-text-splitters",
    "sentence_transformers": "sentence-transformers",
    "sse_starlette": "sse-starlette",
    "faiss": "faiss-cpu",
    "faker": "faker",              # normalized lower-case to match pip
    "stdlib_list": "stdlib-list",  # fixed mismatch
}


# --- helpers -----------------------------------------------------------------
def normalize_name(name: str) -> str:
    return NAME_MAP.get(name, name)


def load_requirements():
    """Parse requirements.txt and normalize names."""
    if not REQ_FILE.exists():
        pytest.skip("requirements.txt not found.")
    reqs = []
    for line in REQ_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        pkg = re.split(r"[=<>!]", line)[0].strip().lower()
        reqs.append(pkg)
    return set(reqs)


def extract_imports():
    """Recursively collect all imported top-level packages in repo."""
    imports = set()
    for py_file in ROOT.rglob("*.py"):
        if any(x in str(py_file) for x in ("venv", "site-packages", "__pycache__")):
            continue
        text = py_file.read_text(encoding="utf-8", errors="ignore")
        for match in re.findall(r"^\s*(?:from|import)\s+([a-zA-Z0-9_\.]+)", text, re.MULTILINE):
            root_pkg = match.split(".")[0]
            if (
                root_pkg
                and root_pkg not in STDLIB_MODULES
                and not root_pkg.startswith(("app", "tests", "_"))
            ):
                imports.add(root_pkg.lower())
    return imports


# --- core tests --------------------------------------------------------------
def test_requirements_audit(request):
    """Compare imports vs. requirements.txt; optionally auto-fix."""
    fix_mode = request.config.getoption("--fix")
    imports = {normalize_name(i) for i in extract_imports()}
    requirements = load_requirements()

    missing = sorted(i for i in imports if i not in requirements)
    unused = sorted(r for r in requirements if all(r not in i for i in imports))

    print("\n🔍 Imported packages:", sorted(imports))
    print("📦 Declared requirements:", sorted(requirements))

    if missing:
        print(f"\n❌ Missing from requirements.txt: {missing}")
    if unused:
        print(f"\n⚠️ Possibly unused dependencies: {unused}")

    if fix_mode:
        _auto_fix_requirements(requirements, missing, unused)
        pytest.skip("requirements.txt automatically updated (fix mode).")
    else:
        assert not missing, f"Missing dependencies in requirements.txt: {missing}"
        if unused:
            pytest.skip(f"Unused packages: {unused}")


def test_requirements_installed():
    """Ensure every requirement is installed."""
    requirements = load_requirements()
    installed = {dist.metadata["Name"].lower() for dist in importlib.metadata.distributions()}
    missing_installed = sorted(req for req in requirements if req not in installed)
    if missing_installed:
        print(f"\n❌ Not installed: {missing_installed}")
    assert not missing_installed, f"Missing installed packages: {missing_installed}"


# --- auto-fix utility --------------------------------------------------------
def _auto_fix_requirements(requirements, missing, unused):
    """Update requirements.txt automatically."""
    lines = []
    if REQ_FILE.exists():
        lines = REQ_FILE.read_text().splitlines()

    # Comment out unused
    for i, line in enumerate(lines):
        base = re.split(r"[=<>!]", line.strip().split("#")[0])[0].strip().lower()
        if base in unused and not line.strip().startswith("#"):
            lines[i] = f"# (auto-commented unused) {line}"

    # Add missing at bottom
    if missing:
        lines.append("")
        lines.append("# === auto-added by tests/test_requirements_audit.py ===")
        for pkg in sorted(missing):
            lines.append(pkg)

    REQ_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n🛠️  requirements.txt updated → {REQ_FILE}")