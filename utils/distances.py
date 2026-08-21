def manhattan_distance(a: (int, int), b: (int, int)) -> int:
    """
    Calculate the Manhattan distance between two points a and b.
    :param a: tuple of (x, y) coordinates for point a
    :param b: tuple of (x, y) coordinates for point b
    :return: Manhattan distance as an integer
    """
    return abs(a[0] - b[0]) + abs(a[1] - b[1])
