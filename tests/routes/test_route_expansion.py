"""Integrationstests fuer die Pfadexpansion der Solver auf einem echten Gitter.

Sichert den Austausch von A* gegen die geschlossene Konstruktion ab. Der
gemockte Test in test_nearest_neighbor.py prueft nur die Verdrahtung, hier
laeuft die echte Expansion.

Zentrale Invariante: die gezeichnete Pfadlaenge stimmt mit der berichteten
Routenlaenge ueberein, also len(full_route) - 1 == solver.route_length. Damit
haengt die Visualisierung nachweisbar an derselben Zahl, die in die
Benchmarks und Optimalitaetsgaps der Arbeit eingeht.
"""
import random

import pytest

from algorithms.a_star import AStar
from routes.christofides import Christofides
from routes.fixed_parameter import FixedParameter
from routes.nearest_neighbor import NearestNeighbor
from warehouse import WareHouseGrid

SOLVERS = [NearestNeighbor, Christofides, FixedParameter]
LAYOUTS = [(1, 1), (3, 2), (5, 3)]


def assert_drawable_path(warehouse, path):
    """Begehbar, 4-benachbart, Rundtour ab und bis zum Depot.

    Geprueft wird das Paarformat, nicht der Sequenztyp: NearestNeighbor und
    Christofides liefern (x, y)-Tupel, FixedParameter [x, y]-Listen
    (fixed_parameter.py:330). Beides serialisiert JSON zum selben Array, und
    static/scripts/WarehouseRenderer.js greift positionsbasiert zu.
    """
    assert path, "leerer Pfad"

    for cell in path:
        assert len(cell) == 2, f"{cell} ist kein (x, y)-Paar"
        x, y = cell
        assert isinstance(x, int) and isinstance(y, int), f"{cell} enthaelt keine ints"
        assert 0 <= y < len(warehouse.grid) and 0 <= x < len(warehouse.grid[0]), \
            f"{cell} liegt ausserhalb des Gitters"
        assert warehouse.grid[y][x] == 1, f"{cell} ist keine begehbare Zelle"

    assert tuple(path[0]) == (0, 0), f"Tour beginnt bei {path[0]}, nicht am Depot"
    assert tuple(path[-1]) == (0, 0), f"Tour endet bei {path[-1]}, nicht am Depot"

    for a, b in zip(path, path[1:]):
        assert abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1, \
            f"Schritt {a} -> {b} ist kein 4-Nachbar-Schritt"


@pytest.mark.parametrize("solver_class", SOLVERS)
@pytest.mark.parametrize("num_isles,num_rows", LAYOUTS)
def test_path_length_matches_reported_route_length(solver_class, num_isles, num_rows):
    """len(full_route) - 1 == solver.route_length, fuer jeden Solver."""
    rng = random.Random(20260817)
    warehouse = WareHouseGrid(num_isles=num_isles, num_rows=num_rows)
    depot = {'x': 0, 'y': 0}

    for _ in range(5):
        picks = rng.sample(range(1, warehouse.total_locations + 1),
                           min(5, warehouse.total_locations))
        locations = [warehouse.location_to_coordinate(loc) for loc in picks]

        solver = solver_class(warehouse, list(locations), dict(depot))
        full_route = solver.expand_route(solver.compute_route())

        assert_drawable_path(warehouse, full_route)
        assert len(full_route) - 1 == solver.route_length, (
            f"{solver_class.__name__} isles={num_isles} rows={num_rows}: "
            f"Pfadlaenge {len(full_route) - 1} != route_length {solver.route_length}")


@pytest.mark.parametrize("solver_class", [NearestNeighbor, Christofides])
def test_swap_preserves_a_star_path_length(solver_class):
    """Die geschlossene Expansion ist genauso lang wie die A*-Expansion.

    A* bleibt als unabhaengige Kontrolle erhalten: dieselbe Besuchsreihenfolge
    wird mit beiden Verfahren expandiert und die Laengen verglichen. Die
    Reihenfolge wird abgegriffen, indem der Router protokolliert, womit er
    aufgerufen wurde.
    """
    rng = random.Random(4711)
    warehouse = WareHouseGrid(num_isles=3, num_rows=2)
    astar = AStar(warehouse.grid)
    depot = {'x': 0, 'y': 0}

    for _ in range(5):
        picks = rng.sample(range(1, warehouse.total_locations + 1), 5)
        locations = [warehouse.location_to_coordinate(loc) for loc in picks]

        solver = solver_class(warehouse, list(locations), dict(depot))
        recorded = []
        original = solver.grid.construct_warehouse_path

        # Besuchsreihenfolge mitschneiden, ohne den Solver zu veraendern
        def spy(loc1, loc2, _original=original, _recorded=recorded):
            _recorded.append((loc1, loc2))
            return _original(loc1, loc2)

        solver.grid = _GridProxy(warehouse, spy)
        full_route = solver.expand_route(solver.compute_route())

        visit_sequence = [{'x': recorded[0][0][0], 'y': recorded[0][0][1]}] + [
            {'x': end[0], 'y': end[1]} for _, end in recorded]
        a_star_route = astar.calculate_a_star_route(visit_sequence)

        assert len(full_route) == len(a_star_route), (
            f"{solver_class.__name__}: geschlossen {len(full_route)} Zellen, "
            f"A* {len(a_star_route)} Zellen")
        assert_drawable_path(warehouse, full_route)


class _GridProxy:
    """Leitet alles an die echte WareHouseGrid weiter, nur construct_warehouse_path
    laeuft ueber den uebergebenen Spion."""

    def __init__(self, warehouse, construct):
        self._warehouse = warehouse
        self.construct_warehouse_path = construct

    def __getattr__(self, name):
        return getattr(self._warehouse, name)


# ----------------------------------------------------------------------
# Messgrenze: compute_route muss ohne die Darstellung auskommen
# ----------------------------------------------------------------------

@pytest.mark.parametrize("solver_class", SOLVERS)
@pytest.mark.parametrize("num_isles,num_rows", LAYOUTS)
def test_route_length_is_final_after_compute_route(solver_class, num_isles, num_rows):
    """route_length steht nach compute_route fest und aendert sich durch die
    Expansion nicht.

    Das ist die Invariante, auf der die Messgrenze der Benchmarks beruht:
    gemessen wird von der Instanziierung bis zu Tour plus Laenge, die Expansion
    in Gitterzellen liegt ausserhalb. Wuerde die Laenge erst bei der Expansion
    entstehen, waere diese Trennung unzulaessig.
    """
    rng = random.Random(20260818)
    warehouse = WareHouseGrid(num_isles=num_isles, num_rows=num_rows)
    depot = {'x': 0, 'y': 0}

    for _ in range(5):
        picks = rng.sample(range(1, warehouse.total_locations + 1),
                           min(5, warehouse.total_locations))
        locations = [warehouse.location_to_coordinate(loc) for loc in picks]

        solver = solver_class(warehouse, list(locations), dict(depot))

        tour = solver.compute_route()
        length_after_compute = solver.route_length
        assert length_after_compute > 0

        cells = solver.expand_route(tour)
        assert solver.route_length == length_after_compute, \
            "expand_route darf route_length nicht veraendern"
        assert len(cells) - 1 == length_after_compute
