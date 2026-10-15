"""
Actions the web page can ask for. Shared by the local server (server.py)
and by the in-browser Python used on GitHub Pages (Pyodide).
"""

from bus_route import CircularRoute

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


def handle(action, body=None):
    """Run an action and return (payload, http_status)."""
    if action == "state":
        return route.to_dict(), 200
    if action not in ACTIONS:
        return {"error": "Acción desconocida."}, 404
    try:
        result = ACTIONS[action](body or {})
    except ValueError as error:
        return {"error": str(error), **route.to_dict()}, 400
    return {**route.to_dict(), "result": result}, 200
