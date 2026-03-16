from flask import Flask, render_template, request, jsonify, Response
import random
import time
import csv
import io
import signal
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

# Stores the last benchmark result for CSV export
_last_benchmark_results = []


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


class TimeoutError(Exception):
    pass


def _run_with_timeout(func, timeout_seconds):
    """Runs a function with a timeout. Returns (result, elapsed_ms) or raises TimeoutError."""
    def handler(signum, frame):
        raise TimeoutError()

    old_handler = signal.signal(signal.SIGALRM, handler)
    signal.alarm(timeout_seconds)
    try:
        start = time.perf_counter()
        result = func()
        elapsed_ms = (time.perf_counter() - start) * 1000
        signal.alarm(0)
        return result, elapsed_ms
    except TimeoutError:
        raise
    finally:
        signal.signal(signal.SIGALRM, old_handler)


@app.route('/benchmark', methods=['POST'])
def run_benchmark():
    """
    Full-factorial benchmark endpoint.

    Expects JSON:
    {
        "product_counts": [5, 10, 15, ...],
        "warehouse_configs": [{"numColumns": 2, "numCrossings": 1}, ...],
        "algorithms": ["nearestNeighbor", "christofides", "fixedParameter"],
        "iterations": 30,
        "base_seed": 42,
        "timeout_seconds": 300
    }

    Returns JSON with a flat list of results, one entry per (config, product_count, iteration, algorithm).
    """
    global _last_benchmark_results

    info = request.get_json()
    if not info:
        return jsonify({"error": "Request body must be valid JSON."}), 400

    # --- Extract and validate inputs ---
    product_counts = info.get('product_counts')
    warehouse_configs = info.get('warehouse_configs')
    algorithms = info.get('algorithms')
    iterations = info.get('iterations')
    base_seed = info.get('base_seed')
    timeout_seconds = info.get('timeout_seconds', 300)

    # Required fields
    if product_counts is None:
        return jsonify({"error": "Missing required field: product_counts"}), 400
    if warehouse_configs is None:
        return jsonify({"error": "Missing required field: warehouse_configs"}), 400
    if algorithms is None:
        return jsonify({"error": "Missing required field: algorithms"}), 400
    if iterations is None:
        return jsonify({"error": "Missing required field: iterations"}), 400
    if base_seed is None:
        return jsonify({"error": "Missing required field: base_seed"}), 400

    # Type validation
    if not isinstance(product_counts, list) or len(product_counts) == 0:
        return jsonify({"error": "product_counts must be a non-empty list of integers."}), 400
    if not isinstance(warehouse_configs, list) or len(warehouse_configs) == 0:
        return jsonify({"error": "warehouse_configs must be a non-empty list of objects."}), 400
    if not isinstance(algorithms, list) or len(algorithms) == 0:
        return jsonify({"error": "algorithms must be a non-empty list."}), 400

    try:
        product_counts = [int(p) for p in product_counts]
        iterations = int(iterations)
        base_seed = int(base_seed)
        timeout_seconds = int(timeout_seconds)
    except (ValueError, TypeError):
        return jsonify({"error": "product_counts, iterations, base_seed, and timeout_seconds must be integers."}), 400

    if iterations < 1:
        return jsonify({"error": "iterations must be at least 1."}), 400
    if timeout_seconds < 1:
        return jsonify({"error": "timeout_seconds must be at least 1."}), 400
    if any(p < 1 for p in product_counts):
        return jsonify({"error": "All product_counts must be at least 1."}), 400

    # Validate algorithms
    invalid_algos = [a for a in algorithms if a not in SOLVERS]
    if invalid_algos:
        return jsonify({"error": f"Unknown algorithms: {invalid_algos}. Valid: {list(SOLVERS.keys())}"}), 400

    # Validate warehouse configs
    parsed_configs = []
    for i, wc in enumerate(warehouse_configs):
        try:
            cols = int(wc.get('numColumns', 0))
            rows = int(wc.get('numCrossings', 0))
        except (ValueError, TypeError, AttributeError):
            return jsonify({"error": f"warehouse_configs[{i}] must have integer numColumns and numCrossings."}), 400
        if cols < 1 or rows < 1:
            return jsonify({"error": f"warehouse_configs[{i}]: numColumns and numCrossings must be at least 1."}), 400
        parsed_configs.append((cols, rows))

    # Validate product counts against each warehouse config
    for cols, rows in parsed_configs:
        total_locations = cols * rows * 12
        for pc in product_counts:
            if pc > total_locations:
                return jsonify({
                    "error": f"product_count {pc} exceeds total locations ({total_locations}) "
                             f"for warehouse {cols}x{rows}."
                }), 400

    # --- Run benchmark ---
    results = []
    packing_table = {'x': 0, 'y': 0}
    total_combinations = len(parsed_configs) * len(product_counts) * iterations
    completed = 0

    for cols, rows in parsed_configs:
        grid = WareHouseGrid(cols, rows)
        total_locations = grid.total_locations

        for product_count in product_counts:
            for iteration in range(iterations):
                seed = base_seed + iteration
                seeded_random = random.Random(seed)
                random_numbers = seeded_random.sample(range(1, total_locations + 1), product_count)
                locations = [grid.location_to_coordinate(loc_num) for loc_num in random_numbers]

                for algorithm in algorithms:
                    solver_class = SOLVERS[algorithm]
                    solver = solver_class(grid, locations, packing_table)

                    try:
                        route, elapsed_ms = _run_with_timeout(solver.compute_route, timeout_seconds)
                        results.append({
                            "algorithm": algorithm,
                            "num_columns": cols,
                            "num_crossings": rows,
                            "num_products": product_count,
                            "iteration": iteration + 1,
                            "route_length": solver.route_length,
                            "computation_time_ms": round(elapsed_ms, 3),
                            "seed": seed,
                            "status": "ok"
                        })
                    except TimeoutError:
                        results.append({
                            "algorithm": algorithm,
                            "num_columns": cols,
                            "num_crossings": rows,
                            "num_products": product_count,
                            "iteration": iteration + 1,
                            "route_length": None,
                            "computation_time_ms": None,
                            "seed": seed,
                            "status": "timeout"
                        })
                    except Exception as e:
                        results.append({
                            "algorithm": algorithm,
                            "num_columns": cols,
                            "num_crossings": rows,
                            "num_products": product_count,
                            "iteration": iteration + 1,
                            "route_length": None,
                            "computation_time_ms": None,
                            "seed": seed,
                            "status": f"error: {str(e)}"
                        })

                completed += 1

    _last_benchmark_results = results

    return jsonify({
        "results": results,
        "total_combinations": total_combinations,
        "total_runs": len(results)
    }), 200


@app.route('/benchmark/export', methods=['GET'])
def export_benchmark_csv():
    """Exports the last benchmark results as a CSV file."""
    if not _last_benchmark_results:
        return jsonify({"error": "No benchmark results available. Run a benchmark first."}), 404

    output = io.StringIO()
    fieldnames = [
        "algorithm", "num_columns", "num_crossings", "num_products",
        "iteration", "route_length", "computation_time_ms", "seed", "status"
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(_last_benchmark_results)

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=benchmark_results.csv"}
    )


if __name__ == '__main__':
    app.run()
