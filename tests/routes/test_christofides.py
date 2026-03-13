from routes.christofides import Christofides


class MockGrid:
    def calculate_warehouse_distance(self, p1, p2):
        return 10


def test_get_prim_mst_finds_correct_tree():
    node_a = (0, 0)
    node_b = (1, 0)
    node_c = (1, 1)

    edges_input = [
        (1, node_a, node_b),
        (10, node_a, node_c),
        (1, node_b, node_c)
    ]

    expected_mst = [
        (1, node_a, node_b),
        (1, node_b, node_c)
    ]

    dummy_locations = [{'x': 0, 'y': 0}, {'x': 1, 'y': 0}, {'x': 1, 'y': 1}]

    christofides_instance = Christofides(grid=None, locations=dummy_locations, start_pos=None)
    actual_mst = christofides_instance._get_prim_mst(edges_input, start_node=node_a)

    actual_mst.sort()
    expected_mst.sort()
    assert actual_mst == expected_mst


def test_augment_mst_with_matching(mocker):
    node_a, node_b, node_c, node_d = (0, 0), (1, 0), (0, 1), (1, 1)

    sample_mst = [(10, node_a, node_b)]
    sample_matching = [(node_c, node_d)]

    known_weight_for_matching = 99

    expected_result = [
        (10, node_a, node_b),
        (known_weight_for_matching, node_c, node_d)
    ]

    christofides_instance = Christofides(grid=None, locations=[], start_pos=None)

    mocker.patch.object(
        christofides_instance,
        '_get_mst_weights',
        return_value=[(known_weight_for_matching, node_c, node_d)]
    )

    result_mst = christofides_instance.augment_mst_with_matching(sample_mst.copy(), sample_matching)

    assert set(result_mst) == set(expected_result)


def test_get_mst_weights_content_is_correct():
    dummy_locations = [{'x': 0, 'y': 0}, {'x': 1, 'y': 0}, {'x': 1, 'y': 1}]
    grid = MockGrid()
    christofides_instance = Christofides(grid, locations=dummy_locations, start_pos=None)

    expected_result = [(10, (1, 0), (0, 0)), (10, (1, 1), (0, 0)), (10, (1, 1), (1, 0))]

    weights = christofides_instance._get_mst_weights()

    assert set(weights) == set(expected_result)

    assert len(weights) == len(expected_result)


def test_create_round_route_from_simple_square():
    node_a, node_b, node_c, node_d = (0, 0), (1, 0), (1, 1), (0, 1)

    edges_input = [
        (node_a, node_b),
        (node_b, node_c),
        (node_c, node_d),
        (node_d, node_a)
    ]

    expected_clockwise = [node_a, node_b, node_c, node_d, node_a]
    expected_counter_clockwise = [node_a, node_d, node_c, node_b, node_a]

    christofides_instance = Christofides(grid=None, locations=[], start_pos=None)

    actual_route = christofides_instance.create_round_route_from_edges(edges_input)

    assert len(actual_route) == 5
    assert set(actual_route) == {node_a, node_b, node_c, node_d}
    assert actual_route[0] == actual_route[-1]
    assert actual_route == expected_clockwise or actual_route == expected_counter_clockwise
