import math
import heapq
from collections import Counter
from flask import Flask, render_template, request, jsonify
import random

app = Flask(__name__)


def _f_score(g, s_coordinate, e_coordinate):
    """f(n) = g(n) + h(n), where h is the Manhattan distance"""
    h = abs(s_coordinate[0] - e_coordinate[0]) + abs(s_coordinate[1] - e_coordinate[1])
    return g + h


def _check_if_possible_path(grid, position):
    """Check bounds and if position is walkable (1 = walkable, 0 = blocked)."""
    x, y = position
    if 0 <= x < len(grid[0]) and 0 <= y < len(grid):
        return grid[y][x] == 1
    return False


def _get_possible_neighbors(grid, position):
    """Return valid neighbor coordinates from current position."""
    neighbors = []
    directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
    for dx, dy in directions:
        neighbor = (position[0] + dx, position[1] + dy)
        if _check_if_possible_path(grid, neighbor):
            neighbors.append(neighbor)
    return neighbors


def _reconstruct_path(came_from, current):
    """Trace back the path from end to start."""
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    return path[::-1]


def a_star(grid, start, dest):
    open_set = []
    heapq.heappush(open_set, (0, start))  # (f_score, position)

    came_from = {}
    g_score = {start: 0}

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == dest:
            return _reconstruct_path(came_from, current)

        for neighbor in _get_possible_neighbors(grid, current):
            tentative_g = g_score[current] + 1  # Assume cost between nodes is 1
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f = _f_score(tentative_g, neighbor, dest)
                heapq.heappush(open_set, (f, neighbor))

    return None  # No path found


def generate_warehouse_grid(num_isles: int, num_rows: int) -> list[list[int]]:
    """
    Generates a warehouse grid based on the number of vertical isles and rows of shelves.
    Each shelf is 2 columns wide and 6 rows tall, separated by walkable aisles (1 space).

    Parameters:
    - num_isles: number of vertical shelves
    - num_rows: number of horizontal shelf blocks

    Returns:
    - grid: 2D list representing the warehouse layout (1 = walkable, 0 = shelf)
    """
    shelf_height = 6
    aisle_height = 1
    shelf_width = 2
    aisle_width = 1

    total_rows = num_rows * shelf_height + (num_rows + 1) * aisle_height
    total_cols = num_isles * shelf_width + (num_isles + 1) * aisle_width

    grid = [[1 for _ in range(total_cols)] for _ in range(total_rows + 3)]

    for row_block in range(num_rows):
        for isle in range(num_isles):
            top = row_block * (shelf_height + aisle_height) + aisle_height
            left = isle * (shelf_width + aisle_width) + aisle_width

            for y in range(top, top + shelf_height):
                for x in range(left, left + shelf_width):
                    grid[y][x] = 0  # 0 means shelf (not walkable)

    # mark the packing table as a 1
    grid[total_rows][(total_cols // 2) - 1] = 0

    return grid


def create_a_star_route(num_isles, num_rows, stock_locations):
    """
    Generates a full path through warehouse using A* between accessible tiles near stock locations.
    """
    grid = generate_warehouse_grid(num_isles, num_rows)

    full_route = []
    for i in range(len(stock_locations) - 1):
        # Original shelf coordinates (likely blocked)
        raw_start = (stock_locations[i]['x'], stock_locations[i]['y'])
        raw_end = (stock_locations[i + 1]['x'], stock_locations[i + 1]['y'])

        def _stock_loc_coordinate_to_route_loc(coordinate: tuple[int, int], is_aisle=False) -> tuple[int, int]:
            """Convert stock location coordinates to route coordinates. Coordinates are inverted as (y,x)."""
            coordinate = list(coordinate)
            y = coordinate[1]
            x = coordinate[0]

            if not is_aisle and grid[y][x]:
                raise ValueError("The given coordinate is a aisle not a location.")

            if is_aisle and grid[y][x]:
                return x, y

            if is_aisle and not grid[y][x]:
                raise ValueError(
                    "The given coordinate is expected to be a aisle however it is not. (is_aisle=False but should be true).")

            if grid[y][x + 1]:
                return x + 1, y
            return x - 1, y

        # Convert to nearest accessible (aisle) coordinates
        start = _stock_loc_coordinate_to_route_loc(raw_start, False)
        end = _stock_loc_coordinate_to_route_loc(raw_end, False)

        # Use A* to get path between these two
        path_segment = a_star(grid, start, end)

        if path_segment:
            # Avoid duplicate positions when paths overlap
            if full_route and full_route[-1] == path_segment[0]:
                full_route.extend(path_segment[1:])
            else:
                full_route.extend(path_segment)
    return full_route


def calc_nearest_neighbor_heuristic_route(locations: [dict], start_pos: dict, num_shelf_cols: int,
                                          num_shelf_rows: int) -> [int]:
    """ Calculates a path through the warehouse using the nearest neighbor heuristic. """
    route = [start_pos]
    remaining_locations = locations.copy()
    while remaining_locations:
        # Find the nearest neighbor
        route.append(_nearest_neighbor(route[-1], remaining_locations))
        remaining_locations.remove(route[-1])
    route.append(start_pos)  # Return to start position
    grid_route = create_a_star_route(num_shelf_cols, num_shelf_rows, route)
    return grid_route


def _nearest_neighbor(start_location: dict, locations: list[dict]) -> dict:
    # Todo check here if i can improve performance by experimenting with manhattan distance and a* search
    sx, sy = start_location['x'], start_location['y']
    return min(
        locations,
        key=lambda loc: manhattan_distance((sx, sy), (loc['x'], loc['y']))
    )


def manhattan_distance(a: (int, int), b: (int, int)) -> int:
    """
    Calculate the Manhattan distance between two points a and b.
    :param a: tuple of (x, y) coordinates for point a
    :param b: tuple of (x, y) coordinates for point b
    :return: Manhattan distance as an integer
    """
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def location_to_grid_tuple(location: int, shelf_columns: int):
    """
    Turns a location number into a given coordinate for the html canvas grid. This allows dynamic changes of the grid.
    Only works for location > 0.

    The following comment was created with ChatGPT
    Shelf Representation:
              1      2      3       4      5
        +----+----+  +----+----+  +----+----+
     1  |  1 |  7 |  | 13 | 19 |  | 25 | 31 |
        +----+----+  +----+----+  +----+----+
     2  |  2 |  8 |  | 14 | 20 |  | 26 | 32 |
        +----+----+  +----+----+  +----+----+
     3  |  3 |  9 |  | 15 | 21 |  | 27 | 33 |
        +----+----+  +----+----+  +----+----+
     4  |  4 | 10 |  | 16 | 22 |  | 28 | 34 |
        +----+----+  +----+----+  +----+----+
     5  |  5 | 11 |  | 17 | 23 |  | 29 | 35 |
        +----+----+  +----+----+  +----+----+
     6  |  6 | 12 |  | 18 | 24 |  | 30 | 36 |
        +----+----+  +----+----+  +----+----+

        +----+----+  +----+----+  +----+----+
     8  | 37 | 43 |  | 49 | 55 |  | 61 | 67 |
        +----+----+  +----+----+  +----+----+
     9  | 38 | 44 |  | 50 | 56 |  | 62 | 68 |
        +----+----+  +----+----+  +----+----+
    10  | 39 | 45 |  | 51 | 57 |  | 63 | 69 |
        +----+----+  +----+----+  +----+----+
    11  | 40 | 46 |  | 52 | 58 |  | 64 | 70 |
        +----+----+  +----+----+  +----+----+
    12  | 41 | 47 |  | 53 | 59 |  | 65 | 71 |
        +----+----+  +----+----+  +----+----+
    13  | 42 | 48 |  | 54 | 60 |  | 66 | 72 |
        +----+----+  +----+----+  +----+----+


    """
    if location <= 0:
        raise ValueError("Location must be greater than 0")

    # calculate the y coordinate
    shelf_number = math.ceil(location / 12)
    shelf_row = math.ceil(shelf_number / shelf_columns)

    shelf_start_coordinate = (shelf_row - 1) * 7 + 1

    offset_y = (location % 6) - 1 if location % 6 else 5
    y = shelf_start_coordinate + offset_y

    # calculate the x coordinate
    # shelf_column is the number that x would be if all the shelf's would be next to each other without any aisles to walk
    shelf_column = math.ceil(location / 6)
    x = shelf_column + shelf_number - 1
    x %= shelf_columns * 3
    return {"location_number": location, "x": x, "y": y}


@app.route('/')
def display_warehouse_floor_plan():  # put application's code here
    return render_template('index.html')


@app.route('/generate-test-locations', methods=['POST'])
def generate_test_locations() -> [(int, int)]:
    """Computes the number of locations and generates random locations"""

    info = request.get_json()
    warehouse = info.get('warehouse_floor_plan')

    number_of_shelf_columns = int(warehouse.get('numColumns', False))
    number_of_rows = int(warehouse.get('numCrossings', False))
    product_count = int(info.get('product_count', False))

    if not all([warehouse, number_of_shelf_columns, number_of_rows]):
        return jsonify([])

    # As each shelf is 6 grids high and 2 grids wide we assume that shelf has 12 stock locations
    number_of_shelves = number_of_rows * number_of_shelf_columns
    number_of_locations = number_of_shelves * 12

    if not product_count or product_count <= 0 or product_count > number_of_locations:
        return []

    random_numbers = random.sample(range(1, number_of_locations + 1), product_count)

    locations = [location_to_grid_tuple(random_number, number_of_shelf_columns) for random_number in random_numbers]
    # locations = [location_to_grid_tuple(37, number_of_shelf_columns)]

    return jsonify(locations)


def _get_mst_weights(locations, num_shelf_cols, num_shelf_rows):
    edges = []
    for location in locations:
        for other_location in locations:
            if location != other_location:
                route = (location, other_location)
                start_loc = (location.get('x'), location.get('y'))
                end_loc = (other_location.get('x'), other_location.get('y'))
                weight = len(create_a_star_route(num_shelf_cols, num_shelf_rows, route))

                # Check if the inverted edge already exists
                if (weight, start_loc, end_loc) not in edges:
                    edges.append(
                        (weight, end_loc, start_loc))
    return edges


def _get_prim_mst(edges, start_key, num_loc: int):
    mst, route = [], []
    visited = {start_key}
    while len(mst) < num_loc - 1:
        candidate_edges = [
            edge for edge in edges
            if (edge[1] in visited and edge[2] not in visited) or
               (edge[2] in visited and edge[1] not in visited)
        ]
        if not candidate_edges:
            break  # No more edges to process

        # Pick the edge with minimum weight
        next_edge = min(candidate_edges, key=lambda x: x[0])
        mst.append(next_edge)
        # Add the new node to visited
        visited.add(next_edge[1] if next_edge[2] in visited else next_edge[2])

    return mst


def _get_odd_nodes(mst):
    """Get odd degree nodes from the minimum spanning tree."""

    locs = [item for item, count in Counter(inner_tuple for _, *tuples in mst for inner_tuple in tuples).items() if
            count % 2 != 0]
    return locs


def calc_christofides_heuristic_route(locations: [dict], start_pos: dict, num_shelf_cols: int,
                                      num_shelf_rows: int) -> [int]:
    """ Calculates a path through the warehouse using the christofides heuristic. """
    locations.append(start_pos)

    edges = _get_mst_weights(locations, num_shelf_cols, num_shelf_rows)
    # use prims algorithm to get the minimum spanning tree
    mst = _get_prim_mst(edges[1:], edges[0][1], len(locations))

    # get the odd degree nodes
    odd_nodes = (0, _get_odd_nodes(mst))

    mst.append(odd_nodes)
    # todo fix this input the whole route in a* and find the way to sort the subroutes beforehand

    route = []
    for subroute in mst:
        route.append(create_a_star_route(num_shelf_cols, num_shelf_rows, [{'x': subroute[1], 'y': subroute[2]}]))

    return route


@app.route('/calculate-route', methods=['POST'])
def calculate_route():
    """Calculates the route for the given locations"""

    info = request.get_json()
    algorithms = info.get('algorithms')
    locations = info.get('locations')
    warehouse = info.get('warehouse_floor_plan')
    number_of_shelf_columns = int(warehouse.get('numColumns'))
    number_of_rows = int(warehouse.get('numCrossings'))

    shelf_height = 6
    aisle_height = 1
    shelf_width = 2
    aisle_width = 1

    total_width = number_of_shelf_columns * (shelf_width + aisle_width) + 1
    total_rows = number_of_rows * shelf_height + number_of_rows * aisle_height + 1

    packing_table = {'x': (total_width // 2) - 1,
                     'y': total_rows}

    routes = {}
    for algorithm in algorithms:
        if algorithm == 'nearestNeighbor':
            routes['nearestNeighbor'] = calc_nearest_neighbor_heuristic_route(locations, packing_table,
                                                                              number_of_shelf_columns, number_of_rows)
            routes = routes.get('nearestNeighbor')  # todo: fix this get extraction when all algorithms are implemented
        elif algorithm == 'christofides':
            routes['christofides'] = calc_christofides_heuristic_route(locations, packing_table,
                                                                       number_of_shelf_columns,
                                                                       number_of_rows)
            routes = routes = routes.get('christofides')
            # todo: fix this get extraction when all algorithms are implemented
        elif algorithm == 'fixed_parameter':
            # todo implement this algorithm
            pass

    return jsonify(routes)


if __name__ == '__main__':
    app.run()
