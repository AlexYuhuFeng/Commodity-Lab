from __future__ import annotations

import ast
from pathlib import Path


def test_tauri_backend_syntax_valid() -> None:
    """Ensure the Tauri Python backend module is syntactically valid (no runtime imports executed)."""
    backend = Path("tauri/backend/main.py")
    assert backend.exists(), "Tauri backend missing"
    src = backend.read_text(encoding="utf-8")
    ast.parse(src)
