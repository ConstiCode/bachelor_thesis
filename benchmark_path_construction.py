"""Laufzeitvergleich: geschlossene Pfadkonstruktion gegen A*.

Vergleicht WareHouseGrid.construct_warehouse_path (geschlossene Form, keine
Suche) mit AStar.calculate_a_star_route (Suche) auf denselben Paaren und ueber
mehrere Layoutgroessen. Beide Verfahren erzeugen denselben Pfad-Typ
(Liste von (x, y)-Tupeln) und dieselbe Pfadlaenge.

Aufruf:
    python benchmark_path_construction.py
"""
import random
import time

from algorithms.a_star import AStar
from algorithms.closed_form_route import ClosedFormRoute
from warehouse import WareHouseGrid

LAYOUTS = [(1, 1), (3, 2), (5, 3), (10, 8), (20, 15)]
PAIRS_PER_LAYOUT = 200
REPEATS = 3
SEED = 20260817


def measure(fn, pairs):
    """Kleinster Durchlauf von REPEATS, um Ausreisser zu daempfen."""
    best = float("inf")
    for _ in range(REPEATS):
        start = time.perf_counter()
        for a, b in pairs:
            fn(a, b)
        best = min(best, time.perf_counter() - start)
    return best


def main():
    rng = random.Random(SEED)
    print(f"{PAIRS_PER_LAYOUT} Paare pro Layout, bester von {REPEATS} Durchlaeufen, "
          f"Saat {SEED}\n")
    header = (f"{'Layout':>16} {'Gitter':>10} {'A* [ms]':>10} "
              f"{'geschl. [ms]':>13} {'Faktor':>8} {'max. Dist':>10}")
    print(header)
    print("-" * len(header))

    for num_isles, num_rows in LAYOUTS:
        warehouse = WareHouseGrid(num_isles=num_isles, num_rows=num_rows)
        astar = AStar(warehouse.grid)
        closed_form = ClosedFormRoute(warehouse)
        height, width = len(warehouse.grid), len(warehouse.grid[0])

        coords = [warehouse.location_to_coordinate(loc)
                  for loc in rng.sample(range(1, warehouse.total_locations + 1),
                                        min(2 * PAIRS_PER_LAYOUT,
                                            warehouse.total_locations))]
        pairs = [(coords[rng.randrange(len(coords))], coords[rng.randrange(len(coords))])
                 for _ in range(PAIRS_PER_LAYOUT)]

        # Gleichheit der Laengen mitprotokollieren, damit die Messung nicht
        # versehentlich zwei verschiedene Dinge vergleicht.
        max_dist = 0
        for a, b in pairs:
            len_astar = len(astar.calculate_a_star_route([a, b])) - 1
            len_closed = len(closed_form.calculate_closed_form_route([a, b])) - 1
            assert len_astar == len_closed, (a, b, len_astar, len_closed)
            max_dist = max(max_dist, len_astar)

        t_astar = measure(lambda a, b: astar.calculate_a_star_route([a, b]), pairs)
        t_closed = measure(
            lambda a, b: closed_form.calculate_closed_form_route([a, b]), pairs)

        print(f"{f'{num_isles}x{num_rows}':>16} {f'{width}x{height}':>10} "
              f"{t_astar * 1000:10.2f} {t_closed * 1000:13.2f} "
              f"{t_astar / t_closed:7.1f}x {max_dist:10d}")


if __name__ == "__main__":
    main()
