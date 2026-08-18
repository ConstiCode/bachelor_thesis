"""Tests fuer die Messgrenze des Benchmark-Harness.

Zwei Zusagen werden hier festgehalten:
1. Das Aufwaermen laeuft fuer jedes Verfahren durch und veraendert das
   Messergebnis nicht.
2. Gemessen wird die Berechnung, nicht die Expansion in Gitterzellen.
"""
import pytest

from app import SOLVERS, run_solver_capped, warm_up_solver
from warehouse.grid import WareHouseGrid

ALGORITHMS = ['nearestNeighbor', 'christofides', 'fixedParameter']
DEPOT = {'x': 0, 'y': 0}


def _instance(cols=3, rows=2, count=6):
    grid = WareHouseGrid(cols, rows)
    locations = [grid.location_to_coordinate(i)
                 for i in range(1, grid.total_locations + 1)][:count]
    return grid, locations


@pytest.mark.parametrize('algorithm', ALGORITHMS)
def test_warm_up_runs_without_error(algorithm):
    warm_up_solver(SOLVERS[algorithm])


@pytest.mark.parametrize('algorithm', ALGORITHMS)
def test_warm_up_does_not_change_the_result(algorithm):
    grid, locations = _instance()
    before = run_solver_capped(SOLVERS[algorithm], grid, list(locations), dict(DEPOT), 90)
    warm_up_solver(SOLVERS[algorithm])
    after = run_solver_capped(SOLVERS[algorithm], grid, list(locations), dict(DEPOT), 90)

    assert before['status'] == after['status'] == 'ok'
    assert before['route_length'] == after['route_length']


@pytest.mark.parametrize('algorithm', ALGORITHMS)
def test_compute_route_returns_the_tour_not_the_drawn_path(algorithm):
    """compute_route endet bei Tour plus Laenge. Die Zellenfolge entsteht erst
    in expand_route und liegt damit ausserhalb der gemessenen Zeit."""
    grid, locations = _instance()
    solver = SOLVERS[algorithm](grid, list(locations), dict(DEPOT))

    tour = solver.compute_route()
    assert solver.route_length > 0

    cells = solver.expand_route(tour)
    assert len(cells) - 1 == solver.route_length
    assert len(cells) > len(tour), \
        'die Expansion muss mehr Zellen liefern als die Tour Stationen hat'
