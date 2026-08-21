from routes.base import BaseRoute


class ExampleRoute(BaseRoute):
    def compute_route(self):
        pass


class MockGrid:
    def calculate_warehouse_distance(self, loc1: tuple[int, int], loc2: tuple[int, int]) -> int:
        return 10


def test_base_route_instantiation():
    grid = object()
    locations = [1, 6, 13]
    start_pos = 1
    route = ExampleRoute(grid, locations, start_pos)
    assert route.grid == grid
    assert route.locations == locations
    assert route.start_pos == start_pos
    assert route.route_length == 0


def test_compute_route_length():
    grid = MockGrid()
    route = ExampleRoute(grid, [1, 6, 13], 1)
    visit_sequence = [(0, 0), (1, 0), (1, 1)]

    route.compute_and_set_route_length(visit_sequence)
    expected_length = 20
    assert expected_length == route.route_length
