"""
Small web server (Python standard library only, nothing to install).

Run:  python server.py         (only this computer)
      python server.py --lan   (phones on the same WiFi too)
      ->   open http://localhost:5051
"""

import json
import socket
import sys
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from api import handle

PORT = 5051
STATIC_DIR = Path(__file__).parent / "static"


class BusRouteHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")  # always serve the latest files
        super().end_headers()

    def _send_json(self, payload, status=200):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/api/state":
            return self._send_json(*handle("state"))
        return super().do_GET()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        return self._send_json(*handle(self.path.removeprefix("/api/"), body))

    def log_message(self, *args):
        pass  # keep the console clean


def local_ip():
    """IP of this computer on the local network (WiFi / LAN)."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        probe.connect(("8.8.8.8", 80))  # no data is sent, it only picks the network card
        return probe.getsockname()[0]


if __name__ == "__main__":
    lan = "--lan" in sys.argv
    server = ThreadingHTTPServer(("0.0.0.0" if lan else "localhost", PORT), BusRouteHandler)
    url = f"http://localhost:{PORT}"
    print(f"Ruta circular corriendo en {url}  (Ctrl+C para salir)")
    if lan:
        print(f"Desde otro dispositivo en la misma red: http://{local_ip()}:{PORT}")
    if "--no-browser" not in sys.argv:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
