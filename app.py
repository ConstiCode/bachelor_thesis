from unicodedata import normalize
import math

from flask import Flask, render_template, request, jsonify
import random

app = Flask(__name__)


def calculate_relative_position(location: int, shelf_start_coordinate: (int, int)) -> (int, int):
    n_th_position_in_shelf = location % 12

    if n_th_position_in_shelf > 6:
        x = 1 + shelf_start_coordinate[0]
    x = 0 + shelf_start_coordinate[0]

    y = n_th_position_in_shelf + shelf_start_coordinate[1]

    return x, y


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

if __name__ == '__main__':
    app.run()
