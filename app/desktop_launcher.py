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


if __name__ == "__main__":
    main()
