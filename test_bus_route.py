"""Run:  python -m unittest -v"""

import unittest

from bus_route import BACKWARD, FORWARD, CircularRoute


def names(route, direction=FORWARD):
    return [s.name for s in route.traverse(direction=direction)]


class CircularRouteTest(unittest.TestCase):
    def setUp(self):
        self.route = CircularRoute()
        for name in ("A", "B", "C", "D", "E", "F"):
            self.route.add_station(name)

    def assert_fully_linked(self):
        for station in self.route.traverse():
            self.assertIs(station.next.prev, station)
            self.assertIs(station.prev.next, station)

    def test_last_station_links_to_first(self):
        self.assertEqual(self.route.head.prev.name, "F")
        self.assertEqual(self.route.head.prev.next.name, "A")
        self.assert_fully_linked()

    def test_single_station_points_to_itself(self):
        route = CircularRoute()
        only = route.add_station("Solo")
        self.assertIs(only.next, only)
        self.assertIs(only.prev, only)

    def test_insert_after(self):
        self.route.add_station("X", after="C")
        self.assertEqual(names(self.route), ["A", "B", "C", "X", "D", "E", "F"])
        self.assert_fully_linked()

    def test_backward_traversal(self):
        self.assertEqual(names(self.route, BACKWARD), ["A", "F", "E", "D", "C", "B"])

    def test_close_head_station_with_bus(self):
        self.route.close_station("A")
        self.assertEqual(self.route.head.name, "B")
        self.assertEqual(self.route.bus.name, "B")
        self.assertEqual(names(self.route), ["B", "C", "D", "E", "F"])
        self.assert_fully_linked()

    def test_close_last_remaining_station(self):
        route = CircularRoute()
        route.add_station("Solo")
        route.close_station("Solo")
        self.assertTrue(route.is_empty())

    def test_route_never_ends(self):
        for _ in range(6):
            self.route.move_forward()
        self.assertEqual(self.route.bus.name, "A")
        self.route.move_backward()
        self.assertEqual(self.route.bus.name, "F")

    def test_shortest_direction(self):
        plan = self.route.shortest_direction("A", "E")
        self.assertEqual(plan["best"], BACKWARD)
        self.assertEqual(plan["backward"], ["A", "F", "E"])
        self.assertEqual(plan["forward_stops"], 4)
        self.assertEqual(self.route.shortest_direction("A", "C")["best"], FORWARD)

    def test_travel_to_uses_shortest_way(self):
        plan = self.route.travel_to("F")
        self.assertEqual(plan["best"], BACKWARD)
        self.assertEqual(self.route.bus.name, "F")

    def test_bus_capacity_is_respected(self):
        self.route.find_station("B").waiting = 100
        self.route.move_forward()
        self.assertLessEqual(self.route.on_board, CircularRoute.BUS_CAPACITY)

    def test_duplicate_station_rejected(self):
        with self.assertRaises(ValueError):
            self.route.add_station("a")


if __name__ == "__main__":
    unittest.main()
