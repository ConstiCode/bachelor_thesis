from unicodedata import normalize
import math

from flask import Flask, render_template, request, jsonify
import random
import heapq

app = Flask(__name__)


class StockLocation:
    def __init__(self, location_number: int, x: int, y: int):
        self.location_number = location_number
        self.x = x
        self.y = y

    def __repr__(self):
        return f"StockLocation(location_number={self.location_number}, x={self.x}, y={self.y})"

    def __eq__(self, other):
        return (self.location_number, self.x, self.y) == (other.location_number, other.x, other.y)


# Todo check if this is needed
def calculate_relative_position(location: int, shelf_start_coordinate: (int, int)) -> (int, int):
    n_th_position_in_shelf = location % 12

    if n_th_position_in_shelf > 6:
        x = 1 + shelf_start_coordinate[0]
    x = 0 + shelf_start_coordinate[0]

    y = n_th_position_in_shelf + shelf_start_coordinate[1]

    return x, y


def calc_nearest_neighbor_heuristic_route(locations: [dict], start_pos: dict) -> [int]:
    """ Calculates a path through the warehouse using the nearest neighbor heuristic. """
    route = [start_pos]
    remaining_locations = locations.copy()
    while remaining_locations:
        # Find the nearest neighbor
        route.append(_nearest_neighbor(route[-1], remaining_locations))
        remaining_locations.remove(route[-1])

    return route


def _nearest_neighbor(start_location: dict, locations: [tuple[int, int]]) -> (int, int):
    priority_queue = []
    for location in locations:
        dis = manhattan_distance((start_location.get('x'), start_location.get('y')),
                                 (location.get('x'), location.get('y')))
        heapq.heappush(priority_queue, (dis, location))
    return heapq.heappop(priority_queue)[1]


def manhattan_distance(a: (int, int), b: (int, int)) -> int:
    """
    Calculate the Manhattan distance between two points a and b.
    :param a: tuple of (x, y) coordinates for point a
    :param b: tuple of (x, y) coordinates for point b
    :return: Manhattan distance as an integer
    """
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def location_to_grid_tuple(location: int, shelf_columns: int) -> (int, int):
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

    # calculate the x coordinates
    row_length = 4 * shelf_columns

    # if the location is placed in the first or second column of the shelf the offset must fit
    offset_x = 3 if location <= ((shelf_number - 1) * 12) + 6 else 2

    x = (shelf_number * 4) - offset_x  # x coordinate for a layout without any shelf rows
    x %= row_length

    return {"location_number": location, "x": x - 1, "y": y - 1}


@app.route('/')
def display_warehouse_floor_plan():  # put application's code here
    return render_template('index.html')


@app.route('/generate-test-locations', methods=['POST'])
def generate_test_locations() -> [(int, int)]:
    """Computes the number of locations and generates random locations"""

    info = request.get_json()
    warehouse = info.get('warehouse_floor_plan')

    number_of_shelf_columns = int(warehouse.get('numAisles'))  # todo fix this naming issue
    number_of_rows = int(warehouse.get('numCrossings'))
    product_count = int(info.get('product_count'))  # Todo fix possible conversion error here

    # As each shelf is 6 grids high and 2 grids wide we assume that shelf has 12 stock locations
    number_of_shelves = number_of_rows * number_of_shelf_columns
    number_of_locations = number_of_shelves * 12

    if not product_count or product_count <= 0 or product_count > number_of_locations:
        return []

    random_numbers = random.sample(range(1, number_of_locations + 1), product_count)

    locations = [location_to_grid_tuple(random_number, number_of_shelf_columns) for random_number in random_numbers]
    # locations = [location_to_grid_tuple(37, number_of_shelf_columns)]

    return jsonify(locations)

    # todo check why x = 0 when it actually should be 1 in the table in the frontend


@app.route('/calculate-route', methods=['POST'])
def calculate_route():
    """Calculates the route for the given locations"""

    info = request.get_json()
    algorithms = info.get('algorithms')
    locations = info.get('locations')
    packing_table = {'x': 0,
                     'y': 0} # Todo fix this and have actual coordinates

    routes = {}
    for algorithm in algorithms:
        if algorithm == 'nearestNeighbor':
            routes['nearestNeighbor'] = calc_nearest_neighbor_heuristic_route(locations, packing_table)
            routes = routes.get('nearestNeighbor')[1:]
        elif algorithm == 'greedy':
            # todo implement this algorithm
            pass
        elif algorithm == 'fixed_parameter':
            # todo implement this algorithm
            pass

    return jsonify(routes)


if __name__ == '__main__':
    app.run()
