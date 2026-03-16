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
    # Two locations in the same aisle vertically aligned
    coord_1 = warehouse.location_to_coordinate(1)
    coord_2 = warehouse.location_to_coordinate(6)

    coord_1_tuple = (coord_1.get('x'), coord_1.get('y'))
    coord_2_tuple = (coord_2.get('x'), coord_2.get('y'))

    dist = warehouse.calculate_warehouse_distance(coord_1_tuple, coord_2_tuple)

    assert dist > 0
    # Should equal Manhattan distance since they're in the same aisle



def test_same_row_requires_crossing(warehouse):
    # Two locations on the same row but in different aisles
    coord_1 = warehouse.location_to_coordinate(1)
    coord_2 = warehouse.location_to_coordinate(13)

    coord_1_tuple = (coord_1.get('x'), coord_1.get('y'))
    coord_2_tuple = (coord_2.get('x'), coord_2.get('y'))

    dist = warehouse.calculate_warehouse_distance(coord_1_tuple, coord_2_tuple)
    assert dist > 0
    # Should be greater than pure Manhattan distance, since it must go via crossing
    assert dist >= manhattan_distance(coord_1_tuple, coord_2_tuple)


def test_different_aisles_go_up(warehouse):
    # Location below needs to go up to cross
    coord_1 = warehouse.location_to_coordinate(6)
    coord_2 = warehouse.location_to_coordinate(20)

    coord_1_tuple = (coord_1.get('x'), coord_1.get('y'))
    coord_2_tuple = (coord_2.get('x'), coord_2.get('y'))

    dist = warehouse.calculate_warehouse_distance(coord_1_tuple, coord_2_tuple)
    assert dist > 0


def test_different_aisles_go_down(warehouse):
    # Location above needs to go down to cross
    coord_1 = warehouse.location_to_coordinate(18)
    coord_2 = warehouse.location_to_coordinate(2)

    coord_1_tuple = (coord_1.get('x'), coord_1.get('y'))
    coord_2_tuple = (coord_2.get('x'), coord_2.get('y'))

    dist = warehouse.calculate_warehouse_distance(coord_1_tuple, coord_2_tuple)
    assert dist > 0


def test_same_location(warehouse):
    # Distance to itself must be zero
    coord_1 = warehouse.location_to_coordinate(1)
    coord_1_tuple = (coord_1.get('x'), coord_1.get('y'))

    assert warehouse.calculate_warehouse_distance(coord_1_tuple, coord_1_tuple) == 0

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
        # Convert locations to coordinates
        coord1 = warehouse.location_to_coordinate(loc1)
        coord2 = warehouse.location_to_coordinate(loc2)

        coord1_tuple = (coord1.get('x'), coord1.get('y'))
        coord2_tuple = (coord2.get('x'), coord2.get('y'))

        # Calculate warehouse distance
        warehouse_dist = warehouse.calculate_warehouse_distance(coord1_tuple, coord2_tuple)

        # A* path distance (A* expects dicts with 'x'/'y' keys)
        full_path = astar.calculate_a_star_route([coord1, coord2])
        a_star_dist = len(full_path) - 1 if full_path else None

        # Basic checks
        assert a_star_dist is not None  # path exists
        assert warehouse_dist == a_star_dist  # warehouse distance should match A*

def test_warehouse_vs_a_star_random(warehouse):
    # Total locations in the warehouse
    total_locations = warehouse.total_locations

    # Initialize A* with the warehouse grid
    astar = AStar(warehouse.grid)

    # Generate 50 random location pairs
    random_pairs = [(random.randint(1, total_locations), random.randint(1, total_locations))
                    for _ in range(50)]

    for loc1, loc2 in random_pairs:
        # Convert locations to coordinates
        coord1 = warehouse.location_to_coordinate(loc1)
        coord2 = warehouse.location_to_coordinate(loc2)

        coord1_tuple = (coord1.get('x'), coord1.get('y'))
        coord2_tuple = (coord2.get('x'), coord2.get('y'))

        # Calculate warehouse distance
        warehouse_dist = warehouse.calculate_warehouse_distance(coord1_tuple, coord2_tuple)

        # Calculate A* path (A* expects dicts with 'x'/'y' keys)
        full_path = astar.calculate_a_star_route([coord1, coord2])
        a_star_dist = len(full_path) - 1 if full_path else None

        # Assertions
        assert a_star_dist is not None  # path must exist
        assert warehouse_dist == a_star_dist  # warehouse distance should match A* exactly