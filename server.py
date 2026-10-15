"""
Small web server (Python standard library only, nothing to install).

Run:  python server.py   ->   open http://localhost:5051
"""

import json
import sys
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from bus_route import CircularRoute

PORT = 5051
STATIC_DIR = Path(__file__).parent / "static"

route = CircularRoute()
for demo_name, demo_waiting in (
    ("Terminal", 6), ("Universidad", 12), ("Hospital", 3), ("Centro", 9),
    ("Estadio", 2), ("Parque", 5), ("Biblioteca", 4), ("Mercado", 7),
):
    route.add_station(demo_name, demo_waiting)

# action name -> function that receives the JSON body and may return extra data
ACTIONS = {
    "add": lambda body: route.add_station(
        body.get("name", ""), int(body.get("waiting", 0) or 0), body.get("after") or None
    ) and None,
    "close": lambda body: route.close_station(body.get("name", "")) and None,
    "forward": lambda body: route.move_forward(),
    "backward": lambda body: route.move_backward(),
    "plan": lambda body: route.shortest_direction(body.get("origin", ""), body.get("target", "")),
    "travel": lambda body: route.travel_to(body.get("target", "")),
    "passengers": lambda body: route.generate_passengers(),
    "reset": lambda body: route.reset(),
}


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
            return self._send_json(route.to_dict())
        return super().do_GET()

    def do_POST(self):
        action = self.path.removeprefix("/api/")
        if action not in ACTIONS:
            return self._send_json({"error": "Acción desconocida."}, 404)
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        try:
            result = ACTIONS[action](body)
        except ValueError as error:
            return self._send_json({"error": str(error), **route.to_dict()}, 400)
        return self._send_json({**route.to_dict(), "result": result})

    def log_message(self, *args):
        pass  # keep the console clean


if __name__ == "__main__":
    server = ThreadingHTTPServer(("localhost", PORT), BusRouteHandler)
    url = f"http://localhost:{PORT}"
    print(f"Ruta circular corriendo en {url}  (Ctrl+C para salir)")
    if "--no-browser" not in sys.argv:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
