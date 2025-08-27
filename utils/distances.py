def manhattan_distance(a: (int, int), b: (int, int)) -> int:
    """
    Calculate the Manhattan distance between two points a and b.
    :param a: tuple of (x, y) coordinates for point a
    :param b: tuple of (x, y) coordinates for point b
    :return: Manhattan distance as an integer
    """
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def total_manhattan_distance(route: list[tuple[tuple[int, int], tuple[int, int]]]) -> int:
    """
    Calculate the total Manhattan distance of a route defined by edges.
    :param route: list of edges, where each edge is ((x1, y1), (x2, y2))
    :return: total Manhattan distance as an integer
    """
    return sum(manhattan_distance(route[i], route[i + 1]) for i in range(len(route) - 1))
