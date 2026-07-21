from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _json_version(path: str) -> str:
    return str(json.loads((ROOT / path).read_text(encoding="utf-8"))["version"])


def test_release_version_is_consistent_across_packages_and_runtime() -> None:
    expected = _json_version("tauri/package.json")
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    cargo = tomllib.loads((ROOT / "tauri/src-tauri/Cargo.toml").read_text(encoding="utf-8"))
    backend = (ROOT / "tauri/backend/main.py").read_text(encoding="utf-8")
    frontend = (ROOT / "tauri/tauri-frontend/src/App.jsx").read_text(encoding="utf-8")

    versions = {
        "pyproject": str(pyproject["project"]["version"]),
        "tauri frontend": _json_version("tauri/tauri-frontend/package.json"),
        "tauri config": str(json.loads((ROOT / "tauri/src-tauri/tauri.conf.json").read_text(encoding="utf-8"))["package"]["version"]),
        "cargo": str(cargo["package"]["version"]),
        "backend": re.search(r'"current_version": "([^"]+)"', backend).group(1),
        "frontend": re.search(r'const currentVersion = "([^"]+)"', frontend).group(1),
    }

    assert versions == {name: expected for name in versions}
