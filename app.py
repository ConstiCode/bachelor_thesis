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
    'fixedParameter': FixedParameter,
}


@app.route('/')
def display_warehouse_floor_plan():
    return render_template('index.html')


@app.route('/generate-test-locations', methods=['POST'])
def generate_test_locations():
    """Computes the number of locations and generates random locations"""

    info = request.get_json()
    product_count = int(info.get('product_count', 0))
    location_generation_seed = info.get('location_generation_seed', False)

    warehouse_config = info.get('warehouse_config', False)

    if not warehouse_config:
        return jsonify({"error_message": "There is no warehouse config! Please choose a valid warehouse config."}), 400

    grid = WareHouseGrid(int(warehouse_config.get('numColumns')), int(warehouse_config.get('numCrossings')))
    number_of_locations = grid.total_locations

    if product_count > number_of_locations:
        return jsonify(
            {
                "error_message": "You are trying to generate more stock locations than the warehouse layout you generated."}), 400

    if not location_generation_seed:
        random_numbers = random.sample(range(1, number_of_locations + 1), product_count)
    else:
        seeded_random = random.Random(location_generation_seed)
        random_numbers = seeded_random.sample(range(1, number_of_locations + 1), product_count)

    locations = [grid.location_to_coordinate(loc_num) for loc_num in random_numbers]

    return jsonify(locations), 200


@app.route('/calculate-route', methods=['POST'])
def calculate_route():
    """Calculates the route for the given locations"""

    info = request.get_json()
    algorithms = info.get('algorithms')
    locations = info.get('locations')
    warehouse = info.get('warehouse_config')
    number_of_shelf_columns = int(warehouse.get('numColumns'))
    number_of_rows = int(warehouse.get('numCrossings'))

    packing_table = {'x': 0, 'y': 0}

    if not all([algorithms, locations, warehouse, number_of_shelf_columns, number_of_rows]):
        return jsonify({
            "error_message": "Some of the variables are not set please ensure you have everything configured correctly."}), 400

    grid = WareHouseGrid(number_of_shelf_columns, number_of_rows)

    routes = {}
    error_messages = []
    for algorithm in algorithms:
        route_solver_class = SOLVERS.get(algorithm)

        if not route_solver_class:
            continue

        solver = route_solver_class(grid, locations, packing_table)
        try:
            start_time = time.perf_counter()
            route = solver.compute_route()
            end_time = time.perf_counter()

            routes[algorithm] = {
                "route": route,
                "length": solver.route_length,
                "computation_time": (end_time - start_time) * 1000
            }

        except:
            error_messages.append(f"In the calculation of the route for algorithm {algorithm} failed.")

    return jsonify({"routes": routes,
                    "error_message": error_messages}), 200


if __name__ == '__main__':
    app.run()
