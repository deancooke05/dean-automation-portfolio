from __future__ import annotations

import argparse
import json
import mimetypes
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from src.service import OrganiserService


BASE = Path(__file__).resolve().parent
WEB = BASE / "web"
SERVICE = OrganiserService(BASE)


class AppHandler(BaseHTTPRequestHandler):
    server_version = "CookeFileOrganiser/1.1"

    def log_message(self, format: str, *args) -> None:
        return

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/defaults":
            self.send_json(SERVICE.defaults())
            return
        if path == "/report":
            self.send_file(BASE / "outputs" / "organisation_report.html", "text/html")
            return
        requested = "index.html" if path == "/" else path.lstrip("/")
        candidate = (WEB / requested).resolve()
        if WEB.resolve() not in candidate.parents and candidate != WEB.resolve():
            self.send_error(403)
            return
        if candidate.is_file():
            self.send_file(candidate)
        else:
            self.send_error(404)

    def do_POST(self) -> None:
        try:
            payload = self.read_json()
            path = urlparse(self.path).path
            if path == "/api/preview":
                result = SERVICE.preview(
                    payload.get("source", ""),
                    payload.get("destination", ""),
                    mode=payload.get("mode", "copy"),
                    recursive=bool(payload.get("recursive", False)),
                    config=payload.get("config") or None,
                )
            elif path == "/api/apply":
                result = SERVICE.apply()
            elif path == "/api/undo":
                result = SERVICE.undo()
            elif path == "/api/choose-folder":
                result = {"path": choose_folder(payload.get("initial", ""))}
            else:
                self.send_error(404)
                return
            self.send_json(result)
        except (ValueError, FileNotFoundError, json.JSONDecodeError) as error:
            self.send_json({"error": str(error)}, status=400)
        except Exception as error:
            self.send_json({"error": f"Unexpected error: {error}"}, status=500)

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length) or b"{}")

    def send_json(self, payload: dict, *, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path: Path, content_type: str | None = None) -> None:
        if not path.is_file():
            self.send_error(404)
            return
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type or mimetypes.guess_type(path.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def choose_folder(initial: str = "") -> str:
    """Open a native folder chooser in a separate process for Tk/macOS safety."""
    initial_path = Path(initial).expanduser()
    if not initial_path.is_absolute():
        initial_path = BASE / initial_path
    if not initial_path.exists():
        initial_path = BASE
    script = (
        "import sys, tkinter as tk; from tkinter import filedialog; "
        "root=tk.Tk(); root.withdraw(); root.attributes('-topmost', True); "
        "value=filedialog.askdirectory(title='Choose a folder', initialdir=sys.argv[1]); "
        "print(value); root.destroy()"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script, str(initial_path)],
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    if completed.returncode != 0:
        raise ValueError("The folder chooser could not be opened. Paste the folder path instead.")
    return completed.stdout.strip()

def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch the Smart File Organiser interface.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0, help="Use 0 to select a free local port.")
    parser.add_argument("--no-browser", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = arguments()
    server = ThreadingHTTPServer((args.host, args.port), AppHandler)
    url = f"http://{args.host}:{server.server_port}"
    print(f"Smart File Organiser is ready at {url}")
    print("Press Control+C to stop it.")
    if not args.no_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nSmart File Organiser stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
