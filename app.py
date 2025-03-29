from unicodedata import normalize
import math

from flask import Flask, render_template, request
import random

app = Flask(__name__)


def calculate_relative_position(location: int, shelf_start_coordinate: (int, int)) -> (int, int):
    n_th_position_in_shelf = location % 12

    if n_th_position_in_shelf > 6:
        x = 1 + shelf_start_coordinate[0]
    x = 0 + shelf_start_coordinate[0]

    y = n_th_position_in_shelf + shelf_start_coordinate[1]

    return x, y


def turn_location_into_grid_tuple(location: int, shelf_columns: int, shelf_rows: int) -> (int, int):
    """
    This works for x calculation. todo Still need to implement y.

    Shelf Representation:
    +---+----+
    | 1 |  7 |
    +---+----+
    | 2 |  8 |
    +---+----+
    | 3 |  9 |
    +---+----+
    | 4 | 10 |
    +---+----+
    | 5 | 11 |
    +---+----+
    | 6 | 12 |
    +---+----+
    """

    shelf_number = math.ceil(location / 12)
    row_length = 4 * shelf_columns

    # depending if the location is placed in the first or second column of the shelf the offset must fit
    offset = 3 if location <= ((shelf_number - 1) * 12) + 6 else 2

    x = (shelf_number * 4) - offset  # x coordinate for a layout without any shelf rows
    x %= row_length  # -1 as the coordinate system starts from 0
    return x


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

    if not product_count or product_count <= 0:
        return []

    normalized_coordinate = warehouse.get('normalizedCoordinate')

    # As each shelf is 6 grids high and 2 grids wide we assume that shelf has 12 stock locations
    number_of_shelves = number_of_rows * number_of_shelf_columns
    number_of_locations = number_of_shelves * 12

    locations = [random.randint(0, number_of_locations) for _ in range(product_count)]
    return turn_location_into_grid_tuple(37, number_of_shelf_columns, number_of_rows)

    # turn locations into grid tuples

    # Todo letzter status: versucht die locations in die grid tuples zu übertragen. Hierfür dachte ich daran im
    # frontend die obere ecke des squares für die berechnung zu nehmen. Die Koordinate der oberen ecke ist
    # (wareHouseFloorPlan.canvas.height / 2) + wareHouseFloorPlan.offset + die höhe der anderen regale und lücken

    # Todo: Überlege welche varialblen im frontend wirklich this sein müssen und welche nicht.


if __name__ == '__main__':
    app.run()
