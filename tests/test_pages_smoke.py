from __future__ import annotations

import ast
import json
from pathlib import Path


def test_tauri_backend_syntax_valid() -> None:
    """Ensure the Tauri Python backend module is syntactically valid (no runtime imports executed)."""
    backend = Path("tauri/backend/main.py")
    assert backend.exists(), "Tauri backend missing"
    src = backend.read_text(encoding="utf-8")
    ast.parse(src)


def test_tauri_window_uses_native_decorations() -> None:
    """Commodity Lab should use the native OS window frame, not a borderless shell."""
    config = json.loads(Path("tauri/src-tauri/tauri.conf.json").read_text(encoding="utf-8"))
    window = config["tauri"]["windows"][0]

    assert window["decorations"] is True
    assert window["transparent"] is False
    assert window["resizable"] is True
