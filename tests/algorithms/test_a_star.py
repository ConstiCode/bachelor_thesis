from algorithms.a_star import AStar


def test_a_star_neighbors():
    grid = [[1]*5 for _ in range(5)]
    astar = AStar(grid)
    neighbors = astar._get_possible_neighbors((2, 2))
    expected = [(3, 2), (2, 3), (1, 2), (2, 1)]
    assert set(neighbors) == set(expected)

def test_a_star_check_bounds():
    grid = [[1]*5 for _ in range(5)]
    astar = AStar(grid)
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