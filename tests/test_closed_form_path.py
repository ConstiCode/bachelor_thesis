"""Tests fuer die geschlossene Pfadkonstruktion (WareHouseGrid.construct_warehouse_path).

Die Tests belegen vier Eigenschaften:
  1. Laenge == calculate_warehouse_distance (exakt, nicht ungefaehr)
  2. jede Zelle begehbar (kein Regalplatz), geprueft gegen _create_grid
  3. aufeinanderfolgende Zellen sind 4-Nachbarn, keine Duplikate
  4. Laenge stimmt mit A* ueberein (A* bleibt die unabhaengige Kontrolle)
"""
import random

import pytest

from algorithms.a_star import AStar
from algorithms.closed_form_route import ClosedFormRoute
from warehouse import WareHouseGrid

# Layouts fuer die Zufallsstichprobe: num_rows 1/3/8 x num_isles 1/5/10
RANDOM_LAYOUTS = [(isles, rows) for isles in (1, 5, 10) for rows in (1, 3, 8)]
PAIRS_PER_LAYOUT = 60  # 9 Layouts * 60 = 540 Paare

# Dieselben gezielten Paare wie tests/test_grid.py::test_warehouse_vs_a_star
TARGETED_PAIRS = [
    (40, 23),
    (21, 47),
    (45, 38),
    (13, 15),
    (1, 6),   # gleicher Gang
    (1, 13),  # gleiche Reihe, anderer Gang
    (6, 20),  # verschiedene Gaenge, Kreuzung nach unten
    (18, 2),  # verschiedene Gaenge, Kreuzung nach oben
]


@pytest.fixture
def warehouse():
    # 3 Gaenge, 2 Regalreihen - dasselbe Layout wie in tests/test_grid.py
    return WareHouseGrid(num_isles=3, num_rows=2)


def coord_tuple(warehouse, location):
    """Regalplatznummer -> (x, y)-Tupel."""
    coord = warehouse.location_to_coordinate(location)
    return coord.get('x'), coord.get('y')


def assert_path_is_valid(warehouse, path, start, end):
    """Prueft Abnahmekriterien 1 bis 3 fuer einen einzelnen Pfad."""
    grid = warehouse.grid

    assert path, f"leerer Pfad fuer {start} -> {end}"

    # Kriterium 1: exakte Laenge
    expected = warehouse.calculate_warehouse_distance(start, end)
    assert len(path) - 1 == expected, (
        f"{start} -> {end}: Pfadlaenge {len(path) - 1} != Formel {expected}")

    # Start- und Endzelle muessen die Gangzellen der beiden Lagerplaetze sein
    assert path[0] == warehouse._turn_location_coordinate_to_route_loc(start)
    assert path[-1] == warehouse._turn_location_coordinate_to_route_loc(end)

    # Kriterium 2: jede Zelle begehbar - Gitter ist (y, x)-indiziert
    for x, y in path:
        assert 0 <= y < len(grid), f"{(x, y)} liegt ausserhalb des Gitters"
        assert 0 <= x < len(grid[0]), f"{(x, y)} liegt ausserhalb des Gitters"
        assert grid[y][x] == 1, f"{(x, y)} ist keine begehbare Zelle"

    # Kriterium 3: 4-Nachbarschaft, keine Spruenge, keine Diagonalen
    for a, b in zip(path, path[1:]):
        step = abs(a[0] - b[0]) + abs(a[1] - b[1])
        assert step == 1, f"Schritt {a} -> {b} ist kein 4-Nachbar-Schritt"

    # Keine Duplikate: ein kuerzester Pfad besucht keine Zelle zweimal
    assert len(set(path)) == len(path), f"Pfad {start} -> {end} enthaelt Duplikate"


def test_targeted_pairs_match_formula_and_a_star(warehouse):
    """Die 8 Paare aus test_grid.py: Laenge == Formel == A*."""
    astar = AStar(warehouse.grid)

    for loc1, loc2 in TARGETED_PAIRS:
        start = coord_tuple(warehouse, loc1)
        end = coord_tuple(warehouse, loc2)

        path = warehouse.construct_warehouse_path(start, end)
        assert_path_is_valid(warehouse, path, start, end)

        a_star_path = astar.calculate_a_star_route([
            warehouse.location_to_coordinate(loc1),
            warehouse.location_to_coordinate(loc2)])
        assert len(path) - 1 == len(a_star_path) - 1, (
            f"{loc1} -> {loc2}: Konstruktion {len(path) - 1} != A* {len(a_star_path) - 1}")


def test_at_most_three_segments(warehouse):
    """Drei-Segment-Hypothese: der Pfad wechselt hoechstens zweimal die Richtung."""
    for loc1 in range(1, warehouse.total_locations + 1):
        for loc2 in range(1, warehouse.total_locations + 1):
            path = warehouse.construct_warehouse_path(
                coord_tuple(warehouse, loc1), coord_tuple(warehouse, loc2))
            directions = [(b[0] - a[0], b[1] - a[1]) for a, b in zip(path, path[1:])]
            segments = sum(1 for i, d in enumerate(directions)
                           if i == 0 or d != directions[i - 1])
            assert segments <= 3, (
                f"{loc1} -> {loc2}: {segments} Segmente, Pfad {path}")


def test_all_pairs_small_layouts():
    """Vollstaendige Pruefung aller Paare in kleinen Layouts, Depot eingeschlossen."""
    for num_isles, num_rows in [(1, 1), (1, 3), (2, 2), (3, 2)]:
        warehouse = WareHouseGrid(num_isles=num_isles, num_rows=num_rows)
        points = [coord_tuple(warehouse, loc)
                  for loc in range(1, warehouse.total_locations + 1)]
        points.append((0, 0))  # Depot

        for start in points:
            for end in points:
                path = warehouse.construct_warehouse_path(start, end)
                assert_path_is_valid(warehouse, path, start, end)


def test_random_pairs_match_a_star_across_layouts():
    """Mindestens 500 Zufallspaare ueber 9 Layouts, Laenge gegen A*."""
    rng = random.Random(20260817)  # feste Saat, damit Fehlschlaege reproduzierbar sind
    checked = 0

    for num_isles, num_rows in RANDOM_LAYOUTS:
        warehouse = WareHouseGrid(num_isles=num_isles, num_rows=num_rows)
        astar = AStar(warehouse.grid)
        total = warehouse.total_locations

        for _ in range(PAIRS_PER_LAYOUT):
            loc1 = rng.randint(1, total)
            loc2 = rng.randint(1, total)
            coord1 = warehouse.location_to_coordinate(loc1)
            coord2 = warehouse.location_to_coordinate(loc2)
            start = (coord1['x'], coord1['y'])
            end = (coord2['x'], coord2['y'])

            path = warehouse.construct_warehouse_path(start, end)
            assert_path_is_valid(warehouse, path, start, end)

            a_star_path = astar.calculate_a_star_route([coord1, coord2])
            assert a_star_path
            assert len(path) - 1 == len(a_star_path) - 1, (
                f"isles={num_isles} rows={num_rows} {loc1} -> {loc2}: "
                f"Konstruktion {len(path) - 1} != A* {len(a_star_path) - 1}")
            checked += 1

    assert checked >= 500


@pytest.mark.parametrize("num_isles,num_rows", [(1, 1), (3, 2), (5, 3), (10, 8)])
def test_depot_paths(num_isles, num_rows):
    """Wege von und zum Depot (0,0), inklusive (0,0) -> (0,0)."""
    warehouse = WareHouseGrid(num_isles=num_isles, num_rows=num_rows)
    depot = (0, 0)

    # Entartetes Paar: Depot auf sich selbst
    self_path = warehouse.construct_warehouse_path(depot, depot)
    assert self_path == [depot]
    assert len(self_path) - 1 == warehouse.calculate_warehouse_distance(depot, depot) == 0

    for loc in range(1, warehouse.total_locations + 1):
        target = coord_tuple(warehouse, loc)

        outbound = warehouse.construct_warehouse_path(depot, target)
        assert_path_is_valid(warehouse, outbound, depot, target)
        assert outbound[0] == depot, "Weg vom Depot muss bei (0,0) beginnen"

        inbound = warehouse.construct_warehouse_path(target, depot)
        assert_path_is_valid(warehouse, inbound, target, depot)
        assert inbound[-1] == depot, "Weg zum Depot muss bei (0,0) enden"


@pytest.mark.parametrize("num_isles,num_rows", [(1, 1), (3, 2), (5, 3)])
def test_exit_candidates_stay_inside_the_grid(num_isles, num_rows):
    """bottom_exit >= 0 und top_exit <= H-1 fuer jede erreichbare Startzelle.

    Belegt, dass die von der Distanzformel nicht geprueften Grenzen durch die
    Gittergeometrie ausgeschlossen sind: Gangzellen liegen immer in einem
    Regalband mit y % 7 in 1..6, das Depot auf y = 0.
    """
    warehouse = WareHouseGrid(num_isles=num_isles, num_rows=num_rows)
    height = len(warehouse.grid)

    points = [coord_tuple(warehouse, loc)
              for loc in range(1, warehouse.total_locations + 1)] + [(0, 0)]

    for point in points:
        x, y = warehouse._turn_location_coordinate_to_route_loc(point)
        cost_to_bottom = y % 7
        bottom_y = y - cost_to_bottom
        top_y = y + (7 - cost_to_bottom)

        assert bottom_y >= 0, f"bottom_exit {bottom_y} < 0 fuer Gangzelle {(x, y)}"
        assert top_y <= height - 1, f"top_exit {top_y} > H-1={height - 1} fuer {(x, y)}"
        assert warehouse.grid[bottom_y][x] == 1
        assert warehouse.grid[top_y][x] == 1
        # Beide Ausgaenge liegen auf einem Quergang
        assert bottom_y % 7 == 0 and top_y % 7 == 0


def test_closed_form_route_matches_a_star_on_full_tours():
    """Ganze Touren: gleiche Laenge und gleiches Ausgabeformat wie A*."""
    rng = random.Random(4711)

    for num_isles, num_rows in [(1, 1), (3, 2), (5, 3)]:
        warehouse = WareHouseGrid(num_isles=num_isles, num_rows=num_rows)
        astar = AStar(warehouse.grid)
        closed_form = ClosedFormRoute(warehouse)

        for _ in range(10):
            picks = rng.sample(range(1, warehouse.total_locations + 1),
                               min(6, warehouse.total_locations))
            tour = ([{'x': 0, 'y': 0}]
                    + [warehouse.location_to_coordinate(loc) for loc in picks]
                    + [{'x': 0, 'y': 0}])

            constructed = closed_form.calculate_closed_form_route(tour)
            from_a_star = astar.calculate_a_star_route(tour)

            assert len(constructed) == len(from_a_star)
            # Ausgabeformat: Liste von (x, y)-Tupeln, genau wie A*
            assert all(isinstance(cell, tuple) and len(cell) == 2 for cell in constructed)
            assert constructed[0] == from_a_star[0] == (0, 0)
            assert constructed[-1] == from_a_star[-1] == (0, 0)
            for x, y in constructed:
                assert warehouse.grid[y][x] == 1
            for a, b in zip(constructed, constructed[1:]):
                assert abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1


def test_closed_form_route_handles_short_input():
    """Randfaelle der Tourexpansion, gleiches Verhalten wie A*."""
    warehouse = WareHouseGrid(num_isles=3, num_rows=2)
    closed_form = ClosedFormRoute(warehouse)

    assert closed_form.calculate_closed_form_route([]) == []
    assert closed_form.calculate_closed_form_route([{'x': 0, 'y': 0}]) == []
    assert closed_form.calculate_closed_form_route(
        [{'x': 0, 'y': 0}, {'x': 0, 'y': 0}]) == [(0, 0)]
