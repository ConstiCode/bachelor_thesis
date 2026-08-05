"""Regressionstests fuer die Frontier-DP in routes/fixed_parameter.py.

Diese Klasse erzeugt die Benchmark-Daten der Arbeit. test_fixed_parameter.py
testet dagegen ScfsPlus, also die alte MILP-Variante.

Kern der Tests ist ein von der Implementierung unabhaengiger Referenzloeser:
BFS-Distanzen auf dem Gitter (metrischer Abschluss) plus Held-Karp. Damit ist
die Optimalitaetsaussage der Arbeit pruefbar und nicht bloss behauptet.
"""
import random
from collections import deque

import pytest

from warehouse.grid import WareHouseGrid
from routes.fixed_parameter import FixedParameter
from routes.nearest_neighbor import NearestNeighbor
from routes import Christofides

DEPOT = {'x': 0, 'y': 0}


# ============================================================
# Unabhaengiger Referenzloeser
# ============================================================

def bfs_distances(grid, source):
    """Kuerzeste Wege von source zu allen begehbaren Zellen (Vier-Nachbarschaft)."""
    cells = grid.grid
    height, width = len(cells), len(cells[0])
    dist = {source: 0}
    queue = deque([source])
    while queue:
        x, y = queue.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx_, ny_ = x + dx, y + dy
            if (0 <= nx_ < width and 0 <= ny_ < height
                    and cells[ny_][nx_] == 1 and (nx_, ny_) not in dist):
                dist[(nx_, ny_)] = dist[(x, y)] + 1
                queue.append((nx_, ny_))
    return dist


def held_karp(distance_matrix):
    """Exakte Rundreise durch alle Knoten, Start und Ziel ist Index 0."""
    n = len(distance_matrix)
    if n == 1:
        return 0
    inf = float('inf')
    dp = [[inf] * n for _ in range(1 << n)]
    dp[1][0] = 0
    for mask in range(1 << n):
        if not mask & 1:
            continue
        for j in range(n):
            if dp[mask][j] == inf:
                continue
            for k in range(n):
                if mask & (1 << k):
                    continue
                candidate = dp[mask][j] + distance_matrix[j][k]
                if candidate < dp[mask | (1 << k)][k]:
                    dp[mask | (1 << k)][k] = candidate
    full = (1 << n) - 1
    return min(dp[full][j] + distance_matrix[j][0] for j in range(n))


def optimal_route_length(grid, locations):
    """Exaktes Optimum der Instanz, unabhaengig von den Solvern berechnet."""
    stands = {grid._turn_location_coordinate_to_route_loc((loc['x'], loc['y']))
              for loc in locations}
    nodes = [(0, 0)] + sorted(stands - {(0, 0)})
    dist = {node: bfs_distances(grid, node) for node in nodes}
    matrix = [[dist[a][b] for b in nodes] for a in nodes]
    return held_karp(matrix)


def make_locations(grid, location_numbers):
    return [grid.location_to_coordinate(n) for n in location_numbers]


def sample_instance(cols, rows, product_count, seed):
    grid = WareHouseGrid(cols, rows)
    numbers = random.Random(seed).sample(
        range(1, grid.total_locations + 1), product_count)
    return grid, make_locations(grid, numbers)


def path_length(path):
    return sum(abs(path[i][0] - path[i - 1][0]) + abs(path[i][1] - path[i - 1][1])
               for i in range(1, len(path)))


# ============================================================
# 1. Depot-Konvention
# ============================================================

class TestDepotConvention:
    """Das Depot (0,0) liegt selbst auf einem Quergang und ist begehbar.

    Es darf nicht wie ein Regalplatz auf die Nachbarzelle (1,0) abgebildet
    werden. Sonst messen die Solver unterschiedliche Touren und die
    Heuristiken erscheinen um 2 Einheiten kuerzer als das Optimum.
    """

    def test_depot_is_walkable(self):
        grid = WareHouseGrid(2, 1)
        assert grid.grid[0][0] == 1

    def test_depot_maps_to_itself(self):
        grid = WareHouseGrid(2, 1)
        assert grid._turn_location_coordinate_to_route_loc((0, 0)) == (0, 0)

    @pytest.mark.parametrize('cols,rows,products,seed', [
        (2, 1, 10, 54), (4, 1, 15, 55), (2, 2, 10, 55), (3, 2, 8, 7),
    ])
    def test_reported_length_matches_own_path(self, cols, rows, products, seed):
        """Die gemeldete route_length muss die Laenge des gelieferten Pfades sein."""
        grid, locations = sample_instance(cols, rows, products, seed)
        for solver_class in (FixedParameter, NearestNeighbor, Christofides):
            solver = solver_class(grid, list(locations), dict(DEPOT))
            path = [tuple(p) for p in solver.compute_route()]
            assert solver.route_length == path_length(path), (
                f"{solver_class.__name__}: gemeldet {solver.route_length}, "
                f"Pfad {path_length(path)}")

    @pytest.mark.parametrize('cols,rows,products,seed', [
        (2, 1, 10, 54), (4, 1, 15, 55), (2, 2, 10, 55),
    ])
    def test_all_solvers_start_and_end_at_depot(self, cols, rows, products, seed):
        grid, locations = sample_instance(cols, rows, products, seed)
        for solver_class in (FixedParameter, NearestNeighbor, Christofides):
            solver = solver_class(grid, list(locations), dict(DEPOT))
            path = [tuple(p) for p in solver.compute_route()]
            assert path[0] == (0, 0), f"{solver_class.__name__} startet bei {path[0]}"
            assert path[-1] == (0, 0), f"{solver_class.__name__} endet bei {path[-1]}"


# ============================================================
# 2. Optimalitaet gegen den Referenzloeser
# ============================================================

class TestOptimality:

    @pytest.mark.parametrize('cols,rows,products,seed', [
        (1, 1, 2, 75366),   # nur ein Gang: frueher offener Pfad statt Rundtour
        (1, 1, 4, 11),
        (2, 1, 6, 73795),
        (2, 1, 10, 54),     # ROAST-Instanz B1
        (3, 1, 5, 88698),
        (4, 1, 8, 10756),
        (2, 2, 10, 55),     # ROAST-Instanz B3
        (3, 2, 7, 4566),
        (5, 1, 9, 64334),
        (2, 3, 6, 999),
    ])
    def test_fp_matches_exact_optimum(self, cols, rows, products, seed):
        grid, locations = sample_instance(cols, rows, products, seed)
        expected = optimal_route_length(grid, locations)

        fp = FixedParameter(grid, list(locations), dict(DEPOT))
        fp.compute_route()

        assert fp.route_length == expected

    @pytest.mark.parametrize('cols,rows,products,seed', [
        (2, 1, 10, 54), (4, 1, 8, 10756), (2, 2, 10, 55), (3, 2, 7, 4566),
    ])
    def test_heuristics_never_beat_the_optimum(self, cols, rows, products, seed):
        """Keine Heuristik darf unter dem Optimum liegen - das waere ein Messfehler."""
        grid, locations = sample_instance(cols, rows, products, seed)
        expected = optimal_route_length(grid, locations)

        for solver_class in (NearestNeighbor, Christofides):
            solver = solver_class(grid, list(locations), dict(DEPOT))
            solver.compute_route()
            assert solver.route_length >= expected, (
                f"{solver_class.__name__} meldet {solver.route_length} < "
                f"Optimum {expected}")


class TestRoastInstances:
    """Die fuenf Instanzen, in denen Nearest Neighbor die angeblich optimale
    FP-Route um 2 Einheiten unterbot. Ursache war die Depot-Konvention,
    nicht die DP."""

    CASES = [
        (2, 1, 10, 54), (4, 1, 15, 55), (4, 1, 20, 55),
        (10, 3, 25, 42), (2, 2, 10, 55),
    ]

    @pytest.mark.parametrize('cols,rows,products,seed', CASES)
    def test_fp_is_not_beaten(self, cols, rows, products, seed):
        grid, locations = sample_instance(cols, rows, products, seed)

        fp = FixedParameter(grid, list(locations), dict(DEPOT))
        fp.compute_route()
        nn = NearestNeighbor(grid, list(locations), dict(DEPOT))
        nn.compute_route()
        ch = Christofides(grid, list(locations), dict(DEPOT))
        ch.compute_route()

        assert nn.route_length >= fp.route_length
        assert ch.route_length >= fp.route_length


# ============================================================
# 3. Struktur der gelieferten Route
# ============================================================

class TestRouteStructure:

    @pytest.mark.parametrize('cols,rows,products,seed', [
        (1, 1, 2, 75366), (2, 1, 10, 54), (4, 2, 12, 3), (10, 3, 25, 42),
    ])
    def test_route_is_a_closed_walk_of_unit_steps(self, cols, rows, products, seed):
        grid, locations = sample_instance(cols, rows, products, seed)
        fp = FixedParameter(grid, list(locations), dict(DEPOT))
        path = [tuple(p) for p in fp.compute_route()]

        assert path[0] == path[-1] == (0, 0)
        for i in range(1, len(path)):
            step = (abs(path[i][0] - path[i - 1][0])
                    + abs(path[i][1] - path[i - 1][1]))
            assert step == 1, f"Schritt {path[i-1]} -> {path[i]} ist kein Einheitsschritt"
            x, y = path[i]
            assert grid.grid[y][x] == 1, f"Zelle {(x, y)} ist nicht begehbar"

    @pytest.mark.parametrize('cols,rows,products,seed', [
        (1, 1, 2, 75366), (2, 1, 10, 54), (4, 2, 12, 3),
    ])
    def test_every_pick_location_is_served(self, cols, rows, products, seed):
        grid, locations = sample_instance(cols, rows, products, seed)
        fp = FixedParameter(grid, list(locations), dict(DEPOT))
        visited = {tuple(p) for p in fp.compute_route()}

        for loc in locations:
            stand = grid._turn_location_coordinate_to_route_loc((loc['x'], loc['y']))
            assert stand in visited, f"Lagerort {loc['location_number']} @{stand} fehlt"

    def test_closed_walk_has_even_length(self):
        """Das Gittergraph ist bipartit, jede Rundtour hat also gerade Laenge.
        Eine ungerade Laenge bedeutet einen offenen Pfad."""
        for seed in (75366, 54, 55, 4566, 11):
            grid, locations = sample_instance(2, 1, 6, seed)
            fp = FixedParameter(grid, list(locations), dict(DEPOT))
            fp.compute_route()
            assert fp.route_length % 2 == 0, f"seed={seed}: {fp.route_length} ist ungerade"


class TestWaypointExpansion:

    def test_diagonal_waypoint_pair_raises(self):
        """Nicht achsenparallele Wegpunkte wurden frueher stillschweigend als
        horizontales Segment expandiert - der Pfad endete an der falschen Zelle."""
        with pytest.raises(AssertionError):
            FixedParameter._expand_waypoints([(0, 0), (3, 7)])

    def test_axis_aligned_pairs_expand(self):
        assert FixedParameter._expand_waypoints([(0, 0), (0, 3)]) == [
            (0, 0), (0, 1), (0, 2), (0, 3)]
        assert FixedParameter._expand_waypoints([(3, 7), (0, 7)]) == [
            (3, 7), (2, 7), (1, 7), (0, 7)]
