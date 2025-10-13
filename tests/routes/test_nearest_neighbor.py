from routes.nearest_neighbor import NearestNeighbor


class MockGrid:
    def __init__(self):
        self.grid = [
            [1, 1, 1, 1],
            [1, 0, 0, 1],
            [1, 0, 0, 1],
            [1, 0, 0, 1],
            [1, 0, 0, 1],
            [1, 0, 0, 1],
            [1, 0, 0, 1],
            [1, 1, 1, 1],
        ]

    def calculate_warehouse_distance(self, loc1: tuple[int, int], loc2: tuple[int, int]) -> int:
        if loc2 == (1, 1):
            return 5
        elif loc2 == (2, 2):
            return 10
        else:
            return 15


def test_find_nearest_neighbor():
    grid = MockGrid()
    locations = [{'x': 1, 'y': 1}, {'x': 2, 'y': 2}, {'x': 3, 'y': 3}]
    start_pos = {'x': 0, 'y': 0}

    location = {'x': 1, 'y': 1}
    route = NearestNeighbor(grid, locations, start_pos)
    nearest = route._find_nearest_neighbor(start_pos, locations)
    assert nearest == location


def test_compute_route_orchestration(mocker):
    mock_astar_class = mocker.patch('routes.nearest_neighbor.AStar')
    mock_astar_class.return_value.calculate_a_star_route.return_value = ['mocked', 'final', 'route']

    grid = MockGrid()
    locations = [{'x': 1, 'y': 1}, {'x': 2, 'y': 2}, {'x': 3, 'y': 3}]
    start_pos = {'x': 0, 'y': 0}
    route_finder = NearestNeighbor(grid, locations, start_pos)

    final_route = route_finder.compute_route()

    mock_astar_class.assert_called_once_with(grid.grid)

    expected_nn_sequence = [
        {'x': 0, 'y': 0},
        {'x': 1, 'y': 1},
        {'x': 2, 'y': 2},
        {'x': 3, 'y': 3},
        {'x': 0, 'y': 0}
    ]
    mock_astar_class.return_value.calculate_a_star_route.assert_called_once_with(expected_nn_sequence)

    assert final_route == ['mocked', 'final', 'route']
