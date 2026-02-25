import os
import socket
import subprocess
import sys
import time
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import messagebox

from streamlit.web import bootstrap


def _project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parent.parent


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _resolve_port() -> int:
    value = os.environ.get("COMMODITY_LAB_PORT", "").strip()
    if not value:
        return 8501
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError("COMMODITY_LAB_PORT must be an integer") from exc


def _wait_for_server(host: str, port: int, timeout_sec: float = 30.0) -> bool:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1.0)
            try:
                sock.connect((host, port))
                return True
            except OSError:
                time.sleep(0.4)
    return False


def _open_url(url: str) -> bool:
    try:
        if sys.platform.startswith("win"):
            subprocess.Popen(["cmd", "/c", "start", "", url], shell=False)
            return True
        return webbrowser.open(url, new=1)
    except Exception:
        return False


def _run_streamlit_server(app_main: Path, host: str, port: int) -> None:
    bootstrap.run(
        str(app_main),
        False,
        [],
        {
            "server.address": host,
            "server.port": port,
            "server.headless": True,
            "server.fileWatcherType": "none",
            "browser.gatherUsageStats": False,
            "global.developmentMode": False,
        },
    )


def _spawn_server_process(port: int) -> subprocess.Popen[str]:
    env = os.environ.copy()
    env["STREAMLIT_SERVER_ADDRESS"] = "127.0.0.1"
    env["STREAMLIT_SERVER_PORT"] = str(port)
    env["STREAMLIT_SERVER_HEADLESS"] = "true"
    env["STREAMLIT_SERVER_FILE_WATCHER_TYPE"] = "none"
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

    if getattr(sys, "frozen", False):
        cmd = [sys.executable, "--internal-run-streamlit", "--port", str(port)]
    else:
        cmd = [sys.executable, str(Path(__file__).resolve()), "--internal-run-streamlit", "--port", str(port)]

    return subprocess.Popen(cmd, env=env)


def _show_status_window(url: str, server_proc: subprocess.Popen[str]) -> None:
    root = tk.Tk()
    root.title("Commodity Lab")
    root.geometry("480x240")
    root.resizable(False, False)

    tk.Label(root, text="Commodity Lab is running", font=("Segoe UI", 12, "bold")).pack(pady=(16, 8))
    tk.Label(root, text="Open this local URL in your browser:", font=("Segoe UI", 10)).pack()

    url_var = tk.StringVar(value=url)
    entry = tk.Entry(root, textvariable=url_var, width=54, justify="center")
    entry.pack(pady=(8, 10))

    status_var = tk.StringVar(value=f"Status: running (pid {server_proc.pid})")
    tk.Label(root, textvariable=status_var, fg="#1f6f2e", font=("Segoe UI", 9)).pack(pady=(0, 10))

    def open_now() -> None:
        if _open_url(url):
            status_var.set("Status: browser open requested")
        else:
            status_var.set("Status: unable to open browser automatically")
            messagebox.showwarning("Open Browser Failed", f"Please open manually:\n{url}")

    def copy_url() -> None:
        root.clipboard_clear()
        root.clipboard_append(url)
        status_var.set("Status: URL copied to clipboard")

    def shutdown() -> None:
        try:
            server_proc.terminate()
            server_proc.wait(timeout=5)
        except Exception:
            server_proc.kill()
        os._exit(0)

    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=6)

    tk.Button(btn_frame, text="Open Browser", command=open_now, width=16).pack(side="left", padx=6)
    tk.Button(btn_frame, text="Copy URL", command=copy_url, width=12).pack(side="left", padx=6)
    tk.Button(btn_frame, text="Quit", command=shutdown, width=10).pack(side="left", padx=6)

    root.protocol("WM_DELETE_WINDOW", shutdown)
    root.mainloop()


def _internal_server_main(port: int) -> None:
    project_root = _project_root()
    app_main = project_root / "app" / "main.py"
    if not app_main.exists():
        raise FileNotFoundError(f"Streamlit entry file not found: {app_main}")
    _run_streamlit_server(app_main, "127.0.0.1", port)


def _parse_internal_port(argv: list[str]) -> int:
    for i, item in enumerate(argv):
        if item == "--port" and i + 1 < len(argv):
            return int(argv[i + 1])
    raise ValueError("Missing --port for internal server mode")


def main() -> None:
    if "--internal-run-streamlit" in sys.argv:
        _internal_server_main(_parse_internal_port(sys.argv))
        return

    host = "127.0.0.1"
    port = _resolve_port()
    url = f"http://{host}:{port}"

    server_proc = _spawn_server_process(port)

    if not _wait_for_server(host, port, timeout_sec=40):
        server_proc.kill()
        raise RuntimeError("Commodity Lab failed to start local server in time")

    _open_url(url)

    # headless mode for CI/manual checks
    if os.environ.get("COMMODITY_LAB_HEADLESS") == "1" or (sys.platform != "win32" and not os.environ.get("DISPLAY")):
        try:
            while True:
                if server_proc.poll() is not None:
                    raise RuntimeError("Commodity Lab server exited unexpectedly")
                time.sleep(1)
        finally:
            if server_proc.poll() is None:
                server_proc.terminate()
        return

    _show_status_window(url, server_proc)


if __name__ == "__main__":
    main()
