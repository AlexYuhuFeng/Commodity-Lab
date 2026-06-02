import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path

from streamlit.web import bootstrap


def _project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parent.parent


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _open_browser(url: str) -> None:
    time.sleep(2)
    webbrowser.open(url, new=1)


def _show_splash(stop_event: threading.Event) -> None:
    try:
        import tkinter as tk
    except ImportError:
        return

    root = tk.Tk()
    root.overrideredirect(True)
    root.configure(background="#081123")
    width, height = 380, 180
    x = (root.winfo_screenwidth() - width) // 2
    y = (root.winfo_screenheight() - height) // 2
    root.geometry(f"{width}x{height}+{x}+{y}")

    label = tk.Label(
        root,
        text="Hedge Lab Terminal",
        font=("Segoe UI", 18, "bold"),
        fg="#eef2ff",
        bg="#081123",
    )
    label.pack(pady=(28, 8))

    status = tk.Label(
        root,
        text="Preparing the desktop learning experience...",
        font=("Segoe UI", 11),
        fg="#cbd5e1",
        bg="#081123",
    )
    status.pack(pady=(0, 12))

    progress = tk.Canvas(root, width=320, height=10, bg="#0b1220", highlightthickness=0)
    progress.create_rectangle(0, 0, 320, 10, fill="#2563eb", outline="")
    progress.pack(pady=(8, 0))

    def check():
        if stop_event.is_set():
            root.destroy()
        else:
            root.after(200, check)

    root.after(200, check)
    root.mainloop()


def main() -> None:
    root = _project_root()
    app_main = root / "app" / "main.py"
    if not app_main.exists():
        raise FileNotFoundError(f"Streamlit entry file not found: {app_main}")

    port = _find_free_port()
    url = f"http://127.0.0.1:{port}"

    os.environ.setdefault("STREAMLIT_SERVER_ADDRESS", "127.0.0.1")
    os.environ.setdefault("STREAMLIT_SERVER_PORT", str(port))
    os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "true")
    os.environ.setdefault("STREAMLIT_SERVER_FILE_WATCHER_TYPE", "none")
    os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")

    threading.Thread(target=_open_browser, args=(url,), daemon=True).start()

    stop_event = threading.Event()
    splash_thread = threading.Thread(target=_show_splash, args=(stop_event,), daemon=True)
    splash_thread.start()

    try:
        bootstrap.run(
            str(app_main),
            False,
            [],
            {
                "server.address": "127.0.0.1",
                "server.port": port,
                "server.headless": True,
                "server.fileWatcherType": "none",
                "browser.gatherUsageStats": False,
                "global.developmentMode": False,
            },
        )
    finally:
        stop_event.set()
        splash_thread.join(timeout=5)


if __name__ == "__main__":
    main()
