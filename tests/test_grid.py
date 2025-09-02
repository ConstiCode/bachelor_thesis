import pytest
from utils.distances import manhattan_distance
from warehouse import WareHouseGrid
from algorithms.a_star import AStar
import random


@pytest.fixture
def warehouse():
    # Create a 3-isle, 2-row warehouse grid
    return WareHouseGrid(num_isles=3, num_rows=2)

@pytest.fixture
def a_star():
    # Create a 3-isle, 2-row warehouse grid
    return WareHouseGrid(num_isles=3, num_rows=2)

def test_same_aisle_distance(warehouse):
    # Two locations in the same aisle
    dist = warehouse.calculate_warehouse_distance(1, 6)  # vertically aligned
    assert dist > 0
    # Should equal Manhattan distance since they're in the same aisle
    coord1 = warehouse._turn_location_coordinate_to_route_loc(warehouse.location_to_coordinate(1))
    coord2 = warehouse._turn_location_coordinate_to_route_loc(warehouse.location_to_coordinate(6))
    assert dist == manhattan_distance(coord1, coord2)


def test_same_row_requires_crossing(warehouse):
    # Two locations on the same row but in different aisles
    dist = warehouse.calculate_warehouse_distance(1, 13)
    assert dist > 0
    # Should be greater than pure Manhattan distance, since it must go via crossing
    coord1 = warehouse._turn_location_coordinate_to_route_loc(warehouse.location_to_coordinate(1))
    coord2 = warehouse._turn_location_coordinate_to_route_loc(warehouse.location_to_coordinate(13))
    assert dist >= manhattan_distance(coord1, coord2)


def test_different_aisles_go_up(warehouse):
    # Location below needs to go up to cross
    dist = warehouse.calculate_warehouse_distance(6, 20)
    assert dist > 0


def test_different_aisles_go_down(warehouse):
    # Location above needs to go down to cross
    dist = warehouse.calculate_warehouse_distance(18, 2)
    assert dist > 0


def test_same_location(warehouse):
    # Distance to itself must be zero
    assert warehouse.calculate_warehouse_distance(1, 1) == 0

def test_warehouse_vs_a_star(warehouse):
    test_pairs = [
        (40,23),
        (21,47),
        (45,38),
        (13, 15),
        (1, 6),   # same aisle
        (1, 13),  # same row different aisle
        (6, 20),  # different aisles, downward crossing
        (18, 2),  # different aisles, upward crossing
    ]

    astar = AStar(warehouse.grid)

    for loc1, loc2 in test_pairs:
        # Calculate warehouse distance
        warehouse_dist = warehouse.calculate_warehouse_distance(loc1, loc2)

        # Convert locations to coordinates
        coord1 = warehouse.location_to_coordinate(loc1)
        coord2 = warehouse.location_to_coordinate(loc2)

        # A* path distance
        full_path = astar.calculate_a_star_route([coord1, coord2])
        a_star_dist = len(full_path) - 1 if full_path else None

        # Basic checks
        assert a_star_dist is not None  # path exists
        assert warehouse_dist == a_star_dist  # warehouse distance should not underestimate A*

def test_warehouse_vs_a_star_random(warehouse):
    # Total locations in the warehouse
    total_locations = warehouse.total_locations

    # Initialize A* with the warehouse grid
    astar = AStar(warehouse.grid)

    # Generate 50 random location pairs
    random_pairs = [(random.randint(1, total_locations), random.randint(1, total_locations))
                    for _ in range(50)]

    for loc1, loc2 in random_pairs:
        # Calculate warehouse distance
        warehouse_dist = warehouse.calculate_warehouse_distance(loc1, loc2)

        # Convert locations to coordinates
        coord1 = warehouse.location_to_coordinate(loc1)
        coord2 = warehouse.location_to_coordinate(loc2)

        # Calculate A* path
        full_path = astar.calculate_a_star_route([coord1, coord2])
        a_star_dist = len(full_path) - 1 if full_path else None

        # Assertions
        assert a_star_dist is not None  # path must exist
        assert warehouse_dist == a_star_dist  # warehouse distance should match A* exactly