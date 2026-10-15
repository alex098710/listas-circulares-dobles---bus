"""
Circular Bus Route - Circular Doubly Linked List.

Every Station is linked to the following station (next) and the previous one
(prev). The last station links back to the first one, so the bus can drive
around the route forever, in either direction, and always choose the
shortest way between two stations.
"""

import random

FORWARD = "forward"
BACKWARD = "backward"


class Station:
    """A bus stop. It is the node of the circular doubly linked list."""

    def __init__(self, name, waiting=0):
        self.name = name
        self.waiting = waiting   # passengers waiting at the stop
        self.next = self         # a single station is linked to itself
        self.prev = self

    def to_dict(self):
        return {
            "name": self.name,
            "waiting": self.waiting,
            "next": self.next.name,
            "prev": self.prev.name,
        }


class CircularRoute:
    """Circular doubly linked list of stations served by one bus."""

    MAX_STATIONS = 14
    BUS_CAPACITY = 40

    def __init__(self):
        self.head = None        # first station of the route (reference point only)
        self.bus = None         # station where the bus is parked right now
        self.size = 0
        self.on_board = 0
        self.delivered = 0
        self.log = []

    # ------------------------------------------------------------------ helpers
    def is_empty(self):
        return self.head is None

    def _record(self, message):
        self.log.insert(0, message)
        del self.log[30:]

    def traverse(self, start=None, direction=FORWARD):
        """Visit every station exactly once, following next or prev.

        Stop condition: we are back at the starting node (there is no None).
        """
        if self.is_empty():
            return
        start = start or self.head
        node = start
        while True:
            yield node
            node = node.next if direction == FORWARD else node.prev
            if node is start:
                break

    def find_station(self, name):
        for station in self.traverse():
            if station.name.lower() == name.strip().lower():
                return station
        return None

    def _get(self, name):
        station = self.find_station(name)
        if station is None:
            raise ValueError(f"No existe la estación {name}.")
        return station

    # ---------------------------------------------------------------- insertion
    def add_station(self, name, waiting=0, after=None):
        """Insert a station at the end of the route, or right after `after`."""
        name = name.strip()
        if not name:
            raise ValueError("El nombre de la estación no puede estar vacío.")
        if self.size >= self.MAX_STATIONS:
            raise ValueError(f"La ruta admite máximo {self.MAX_STATIONS} estaciones.")
        if self.find_station(name):
            raise ValueError(f"La estación {name} ya existe.")

        new_station = Station(name, waiting)
        if self.is_empty():
            self.head = self.bus = new_station
        else:
            previous = self._get(after) if after else self.head.prev  # tail by default
            new_station.prev = previous
            new_station.next = previous.next
            previous.next.prev = new_station
            previous.next = new_station
        self.size += 1
        self._record(f"🚏 Se abrió la estación {name}.")
        return new_station

    # ----------------------------------------------------------------- deletion
    def close_station(self, name):
        """Unlink a station. Its neighbours get linked to each other."""
        station = self._get(name)
        if self.size == 1:
            self.head = self.bus = None
        else:
            station.prev.next = station.next
            station.next.prev = station.prev
            if station is self.head:
                self.head = station.next
            if station is self.bus:
                self.bus = station.next
                self._record(f"🚌 El bus se movió a {self.bus.name} porque cerraron su estación.")
        station.next = station.prev = station  # fully detached
        self.size -= 1
        self._record(f"⛔ Se cerró la estación {station.name}.")
        return station

    # ----------------------------------------------------------------- driving
    def _require_bus(self):
        if self.is_empty():
            raise ValueError("La ruta no tiene estaciones.")

    def _arrive(self, station):
        """Bus stops at a station: drop passengers and pick up the waiting ones."""
        self.bus = station
        dropped = random.randint(0, self.on_board)
        self.on_board -= dropped
        self.delivered += dropped
        boarding = min(station.waiting, self.BUS_CAPACITY - self.on_board)
        station.waiting -= boarding
        self.on_board += boarding
        return dropped, boarding

    def move_forward(self):
        self._require_bus()
        dropped, boarding = self._arrive(self.bus.next)
        self._record(f"➡️ Bus avanzó a {self.bus.name} (bajaron {dropped}, subieron {boarding}).")

    def move_backward(self):
        self._require_bus()
        dropped, boarding = self._arrive(self.bus.prev)
        self._record(f"⬅️ Bus retrocedió a {self.bus.name} (bajaron {dropped}, subieron {boarding}).")

    def path_between(self, origin_name, target_name, direction):
        """List of stations from origin to target following one direction."""
        origin = self._get(origin_name)
        target = self._get(target_name)
        path = [origin]
        node = origin
        while node is not target:
            node = node.next if direction == FORWARD else node.prev
            path.append(node)
        return path

    def stops_between(self, origin_name, target_name, direction=FORWARD):
        return len(self.path_between(origin_name, target_name, direction)) - 1

    def shortest_direction(self, origin_name, target_name):
        """Compare both ways around the circle and pick the shorter one."""
        forward = self.path_between(origin_name, target_name, FORWARD)
        backward = self.path_between(origin_name, target_name, BACKWARD)
        best = FORWARD if len(forward) <= len(backward) else BACKWARD
        return {
            "best": best,
            "forward": [s.name for s in forward],
            "backward": [s.name for s in backward],
            "forward_stops": len(forward) - 1,
            "backward_stops": len(backward) - 1,
        }

    def travel_to(self, target_name):
        """Drive the bus to a station using the shortest direction."""
        self._require_bus()
        plan = self.shortest_direction(self.bus.name, target_name)
        path = plan[plan["best"]]
        for name in path[1:]:
            self._arrive(self._get(name))
        sense = "adelante (next)" if plan["best"] == FORWARD else "atrás (prev)"
        self._record(
            f"🧭 Bus viajó a {self.bus.name} por {sense}: {len(path) - 1} paradas."
        )
        return plan

    def generate_passengers(self):
        for station in self.traverse():
            station.waiting += random.randint(0, 8)
        self._record("👥 Llegaron nuevos pasajeros a las estaciones.")

    def reset(self):
        self.__init__()

    # ------------------------------------------------------------ serialization
    def to_dict(self):
        return {
            "stations": [s.to_dict() for s in self.traverse()],
            "head": self.head.name if self.head else None,
            "tail": self.head.prev.name if self.head else None,
            "bus": self.bus.name if self.bus else None,
            "size": self.size,
            "on_board": self.on_board,
            "capacity": self.BUS_CAPACITY,
            "delivered": self.delivered,
            "log": self.log,
        }
