import pytest
from algorithms.a_star import AStar

# -----------------------------
# Fixtures for test grids
# -----------------------------

@pytest.fixture
def empty_grid():
    """5x5 empty grid (all walkable)"""
    return [[1]*5 for _ in range(5)]

@pytest.fixture
def blocked_grid():
    """5x5 grid with a central block"""
    grid = [[1]*5 for _ in range(5)]
    grid[2][2] = 0
    return grid

@pytest.fixture
def single_path_grid():
    """3x3 grid with a single straight path"""
    grid = [
        [1, 1, 1],
        [0, 0, 1],
        [1, 1, 1]
    ]
    return grid

# -----------------------------
# Tests
# -----------------------------

def test_a_star_simple_path(empty_grid):
    astar = AStar(empty_grid)
    start = {'x': 0, 'y': 0}
    end = {'x': 4, 'y': 4}
    route = astar.calculate_a_star_route([start, end])
    assert route[0] == (0, 0)
    assert route[-1] == (4, 4)
    # Path length should be Manhattan distance + 1
    assert len(route) == 9  # minimal path in a 5x5 grid corner to corner

def test_a_star_blocked_path(blocked_grid):
    astar = AStar(blocked_grid)
    start = {'x': 0, 'y': 0}
    end = {'x': 4, 'y': 4}
    route = astar.calculate_a_star_route([start, end])
    assert route[0] == (0, 0)
    assert route[-1] == (4, 4)
    # Ensure blocked cell (2,2) is not in path
    assert (2, 2) not in route

def test_a_star_no_path():
    grid = [
        [1, 0, 1],
        [0, 0, 0],
        [1, 0, 1]
    ]
    astar = AStar(grid)
    start = {'x': 0, 'y': 0}
    end = {'x': 2, 'y': 2}
    route = astar.calculate_a_star_route([start, end])
    assert route == []  # no path exists

def test_a_star_multi_step_route(single_path_grid):
    astar = AStar(single_path_grid)
    waypoints = [
        {'x': 0, 'y': 0},
        {'x': 2, 'y': 0},
        {'x': 2, 'y': 2}
    ]
    route = astar.calculate_a_star_route(waypoints)
    assert route[0] == (0, 0)
    assert route[-1] == (2, 2)
    # Ensure route goes through intermediate waypoint
    assert (2, 0) in route

def test_a_star_neighbors(empty_grid):
    astar = AStar(empty_grid)
    neighbors = astar._get_possible_neighbors((2, 2))
    expected = [(3, 2), (2, 3), (1, 2), (2, 1)]
    assert set(neighbors) == set(expected)

def test_a_star_check_bounds(empty_grid):
    astar = AStar(empty_grid)
    assert astar._check_if_possible_path((-1, 0)) is False
    assert astar._check_if_possible_path((0, -1)) is False
    assert astar._check_if_possible_path((5, 0)) is False
    assert astar._check_if_possible_path((0, 5)) is False
    assert astar._check_if_possible_path((2, 2)) is True

def test_a_star_f_score():
    astar = AStar([[1]])
    g = 3
    start = (0, 0)
    end = (2, 2)
    f = astar._f_score(g, start, end)
    # f = g + manhattan distance
    assert f == 3 + 4
