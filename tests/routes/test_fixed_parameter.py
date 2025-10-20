from routes.fixed_parameter import FixedParameter
from warehouse.grid import WareHouseGrid


def test_get_warehouse_walkable_edges():
    grid = WareHouseGrid(num_isles=4, num_rows=3)
    fixed_param_route = FixedParameter(grid, locations=[], start_pos={'x': 0, 'y': 0})

    walkable_edges = fixed_param_route.get_warehouse_walkable_edges()

    expected_edges = [
        # Vertical edges
        ((0, 0), (0, 7)),
        ((3, 0), (3, 7)),
        ((6, 0), (6, 7)),
        ((9, 0), (9, 7)),

        ((0, 7), (0, 14)),
        ((3, 7), (3, 14)),
        ((6, 7), (6, 14)),
        ((9, 7), (9, 14)),

        # Horizontal edges
        ((0,0), (3,0)),
        ((3,0), (6,0)),
        ((6,0), (9,0)),
        ((0,7), (3,7)),
        ((3,7), (6,7)),
        ((6,7), (9,7)),
        ((0,14), (3,14)),
        ((3,14), (6,14)),
        ((6,14), (9,14))]

    assert sorted(walkable_edges) == sorted(expected_edges)

def test_get_edge_length():
    grid = WareHouseGrid(num_isles=4, num_rows=3)
    fixed_param_route = FixedParameter(grid, locations=[], start_pos={'x': 0, 'y': 0})

    edge_length = fixed_param_route.get_edge_length(((0, 0), (0, 7)))
    assert edge_length == 7

    edge_length = fixed_param_route.get_edge_length(((0, 0), (3, 0)))
    assert edge_length == 3

    edge_length = fixed_param_route.get_edge_length(((3, 7), (6, 7)))
    assert edge_length == 3