import heapq


class AStar:
    """
    A* pathfinding algorithm implementation.
    """

    def __init__(self, grid):
        self.grid = grid
        self.rows = len(grid)
        self.cols = len(grid[0]) if grid else 0

    def calculate_a_star_route(self, route):
        """
            Generates a full path through warehouse using A* between accessible tiles near stock locations.
        """

        full_route = []
        for i in range(len(route) - 1):
            # Original shelf coordinates (likely blocked)
            raw_start = (route[i]['x'], route[i]['y'])
            raw_end = (route[i + 1]['x'], route[i + 1]['y'])

            def _stock_loc_coordinate_to_route_loc(coordinate: tuple[int, int], is_aisle=False) -> tuple[int, int]:
                """Convert stock location coordinates to route coordinates. Coordinates are inverted as (y,x)."""
                coordinate = list(coordinate)
                y = coordinate[1]
                x = coordinate[0]

                # this is the location of the packing station and therefore the only legal location that is on an aisle
                if x == 0 and y == 0:
                    return x, y

                if not is_aisle and self.grid[y][x]:
                    raise ValueError("The given coordinate is a aisle not a location.")

                if is_aisle and self.grid[y][x]:
                    return x, y

                if is_aisle and not self.grid[y][x]:
                    raise ValueError(
                        "The given coordinate is expected to be a aisle however it is not. (is_aisle=False but should be true).")

                if self.grid[y][x + 1]:
                    return x + 1, y
                return x - 1, y

            # Convert to nearest accessible (aisle) coordinates
            start = _stock_loc_coordinate_to_route_loc(raw_start, False)
            end = _stock_loc_coordinate_to_route_loc(raw_end, False)

            # Use A* to get path between these two
            path_segment = self._a_star(start, end)

            if path_segment:
                # Avoid duplicate positions when paths overlap
                if full_route and full_route[-1] == path_segment[0]:
                    full_route.extend(path_segment[1:])
                else:
                    full_route.extend(path_segment)
        return full_route

    def _a_star(self, start, dest):
        open_set = []
        heapq.heappush(open_set, (0, start))  # (f_score, position)

        came_from = {}
        g_score = {start: 0}

        while open_set:
            _, current = heapq.heappop(open_set)

            if current == dest:
                return self._reconstruct_path(came_from, current)

            for neighbor in self._get_possible_neighbors(current):
                tentative_g = g_score[current] + 1  # Assume cost between nodes is 1
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f = self._f_score(tentative_g, neighbor, dest)
                    heapq.heappush(open_set, (f, neighbor))

        return None

    def _reconstruct_path(self, came_from, current):
        """Trace back the path from end to start."""
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        return path[::-1]

    def _get_possible_neighbors(self, position):
        """Return valid neighbor coordinates from current position."""
        neighbors = []
        directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        for dx, dy in directions:
            neighbor = (position[0] + dx, position[1] + dy)
            if self._check_if_possible_path(neighbor):
                neighbors.append(neighbor)
        return neighbors

    def _check_if_possible_path(self, position):
        """Check bounds and if position is walkable (1 = walkable, 0 = blocked)."""
        x, y = position
        if 0 <= x < len(self.grid[0]) and 0 <= y < len(self.grid):
            return self.grid[y][x] == 1
        return False

    def _f_score(self, g, s_coordinate, e_coordinate):
        """f(n) = g(n) + h(n), where h is the Manhattan distance"""
        h = abs(s_coordinate[0] - e_coordinate[0]) + abs(s_coordinate[1] - e_coordinate[1])
        return g + h