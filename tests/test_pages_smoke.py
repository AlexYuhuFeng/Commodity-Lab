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


def test_tauri_window_launches_windowed_with_native_controls() -> None:
    """Commodity Lab should open as a normal resizable window with reliable native controls."""
    config = json.loads(Path("tauri/src-tauri/tauri.conf.json").read_text(encoding="utf-8"))
    window = config["tauri"]["windows"][0]

    assert window["maximized"] is False
    assert window["fullscreen"] is False
    assert window["decorations"] is True
    assert window["transparent"] is False
    assert window["resizable"] is True


def test_tauri_shutdown_cleans_backend_on_window_close() -> None:
    """Closing the desktop window must not leave the bundled backend listening on port 8000."""
    main_rs = Path("tauri/src-tauri/src/main.rs").read_text(encoding="utf-8")
    backend_py = Path("tauri/backend/main.py").read_text(encoding="utf-8")

    assert "on_window_event" in main_rs
    assert "WindowEvent::CloseRequested" in main_rs
    assert "RunEvent::ExitRequested" in main_rs
    assert "COMMODITY_LAB_PARENT_PID" in main_rs
    assert "COMMODITY_LAB_PARENT_PID" in backend_py
    assert "_start_parent_watchdog" in backend_py
