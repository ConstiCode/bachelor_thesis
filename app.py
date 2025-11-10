from flask import Flask, render_template, request, jsonify
import random
import time
from routes import Christofides
from routes.fixed_parameter import FixedParameter
from warehouse.grid import WareHouseGrid
from routes.nearest_neighbor import NearestNeighbor

app = Flask(__name__)

SOLVERS = {
    'nearestNeighbor': NearestNeighbor,
    'christofides': Christofides,
    'fixedParameter': FixedParameter
}
# Todo picking table richtig positionieren
# Modal zum laufen bringen
# Routenlänge anzeigen
# Zeit anzeigen

@app.route('/')
def display_warehouse_floor_plan():
    return render_template('index.html')


@app.route('/generate-test-locations', methods=['POST'])
def generate_test_locations():
    """Computes the number of locations and generates random locations"""

    info = request.get_json()
    product_count = int(info.get('product_count', 0))

    warehouse_config = info.get('warehouse_config', False)

    if not warehouse_config:
        return jsonify([])

    grid = WareHouseGrid(int(warehouse_config.get('numColumns')),int(warehouse_config.get('numCrossings')))
    number_of_locations = grid.total_locations

    random_numbers = random.sample(range(1, number_of_locations + 1), product_count)

    locations = [grid.location_to_coordinate(loc_num) for loc_num in random_numbers]

    return jsonify(locations)


@app.route('/calculate-route', methods=['POST'])
def calculate_route():
    """Calculates the route for the given locations"""

    info = request.get_json()
    algorithms = info.get('algorithms')
    locations = info.get('locations')
    warehouse = info.get('warehouse_config')
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

    grid = WareHouseGrid(int(warehouse['numColumns']), int(warehouse['numCrossings']))

    routes = {}
    for algorithm in algorithms:

        route_solver_class = SOLVERS.get(algorithm)

        if not route_solver_class:
            continue

        solver = route_solver_class(grid, locations, packing_table)

        start_time = time.perf_counter()
        route = solver.compute_route()
        end_time = time.perf_counter()

        routes[algorithm] = {
            "route": route,
            "length": solver.route_length,
            "computation_time": (end_time - start_time) * 1000
        }

    return jsonify(routes)


if __name__ == '__main__':
    app.run()
