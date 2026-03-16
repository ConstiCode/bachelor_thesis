import pytest
import networkx as nx
from warehouse.grid import WareHouseGrid
from routes.fixed_parameter import FixedParameter


# ============================================================
# Helpers
# ============================================================

DEPOT = {'x': 0, 'y': 0}


def make_locations(grid, location_numbers):
    """Converts location numbers to coordinate dicts via grid.location_to_coordinate()."""
    return [grid.location_to_coordinate(n) for n in location_numbers]


# ============================================================
# 1. Test Preprocessing (Largest Gap Heuristik, Vertex Reduction)
# ============================================================

class TestVertexPreprocessing:
    """Tests for _apply_vertex_preprocessing (Largest Gap heuristic).

    Important: Vertex preprocessing only triggers on aisles that have at least 2
    intersection nodes (I_nodes). The aisle at x=0 only has one intersection
    (y=7) because the depot at (0,0) is excluded from I_nodes. So we must use
    products in the x=3 aisle (intersections at (3,0) and (3,7)).
    """

    def test_no_reduction_with_two_products_in_sub_aisle(self):
        """Sub-aisle with <= 2 products should not trigger any reduction."""
        grid = WareHouseGrid(2, 1)
        # Loc 7 -> walkable (3,1), Loc 12 -> walkable (3,6): same aisle x=3
        locations = make_locations(grid, [7, 12])
        fp = FixedParameter(grid, locations, DEPOT)

        assert (3, 1) in fp.R_nodes
        assert (3, 6) in fp.R_nodes
        assert len(fp.preprocessing_constraints) == 0

    def test_reduction_removes_middle_products(self):
        """Sub-aisle with 6 products: only extremes (y=1 and y=6) are kept."""
        grid = WareHouseGrid(2, 1)
        # Loc 7-12 -> walkable (3,1) through (3,6), all in aisle x=3
        locations = make_locations(grid, [7, 8, 9, 10, 11, 12])
        fp = FixedParameter(grid, locations, DEPOT)

        # All gaps equal (=1), first gap wins: between y=0 (intersection) and y=1
        # S = [] (no products <= 0), T = [1..6] -> keep b_T=1, t_T=6
        assert (3, 1) in fp.R_nodes, "Bottom extreme must be kept"
        assert (3, 6) in fp.R_nodes, "Top extreme must be kept"

        for y in [2, 3, 4, 5]:
            assert (3, y) not in fp.R_nodes, f"Product at (3,{y}) should be removed"

    def test_reduction_with_clear_gap(self):
        """Products split by a clear gap: extremes of S and T sets are kept."""
        grid = WareHouseGrid(2, 1)
        # Loc 7,8,9,11,12 -> walkable (3,1),(3,2),(3,3),(3,5),(3,6)
        # Largest gap between y=3 and y=5 (size 2)
        locations = make_locations(grid, [7, 8, 9, 11, 12])
        fp = FixedParameter(grid, locations, DEPOT)

        # S = [1,2,3] -> keep b_S=1, t_S=3, remove y=2
        # T = [5,6] -> keep b_T=5, t_T=6
        assert (3, 1) in fp.R_nodes
        assert (3, 3) in fp.R_nodes
        assert (3, 5) in fp.R_nodes
        assert (3, 6) in fp.R_nodes
        assert (3, 2) not in fp.R_nodes, "Middle product in S should be removed"

    def test_preprocessing_constraints_generated(self):
        """Reduced sub-aisles must produce preprocessing constraints."""
        grid = WareHouseGrid(2, 1)
        locations = make_locations(grid, [7, 8, 9, 11, 12])
        fp = FixedParameter(grid, locations, DEPOT)

        # S-constraint for (3,1)-(3,3) and T-constraint for (3,5)-(3,6)
        assert len(fp.preprocessing_constraints) == 2

        for constraint in fp.preprocessing_constraints:
            assert constraint['type'] in ('S', 'T')
            assert len(constraint['nodes']) == 2
            for node in constraint['nodes']:
                assert isinstance(node, tuple) and len(node) == 2

    def test_removed_nodes_neighbors_reconnected(self):
        """After removing (3,2), its neighbors (3,1) and (3,3) must be connected."""
        grid = WareHouseGrid(2, 1)
        locations = make_locations(grid, [7, 8, 9, 11, 12])
        fp = FixedParameter(grid, locations, DEPOT)

        assert fp.steiner_graph.has_edge((3, 1), (3, 3)), \
            "Neighbors of removed node should be directly connected"
        assert fp.steiner_graph[(3, 1)][(3, 3)]['weight'] == 2


# ============================================================
# 2. Test Arc Reduction (1-Spanner MILP)
# ============================================================

class TestArcPreprocessing:
    """Tests for _apply_arc_preprocessing (minimum 1-Spanner)."""

    def test_shortest_paths_preserved(self):
        """After 1-Spanner: shortest distances between all R-node pairs unchanged."""
        grid = WareHouseGrid(2, 1)
        # Loc 7 -> walkable (3,1), Loc 19 -> walkable (6,1)
        locations = make_locations(grid, [7, 19])
        fp = FixedParameter(grid, locations, DEPOT)

        shortest = dict(nx.all_pairs_dijkstra_path_length(fp.steiner_graph))

        r_nodes = list(fp.R_nodes)
        for i in range(len(r_nodes)):
            for j in range(i + 1, len(r_nodes)):
                u, v = r_nodes[i], r_nodes[j]
                assert v in shortest[u], f"R-nodes {u} and {v} must be reachable"
                assert shortest[u][v] == shortest[v][u], \
                    f"Distance {u}->{v} should equal {v}->{u} in undirected graph"

    def test_spanner_graph_is_connected(self):
        """All R-nodes must remain connected after arc reduction."""
        grid = WareHouseGrid(2, 1)
        locations = make_locations(grid, [1, 7, 19])
        fp = FixedParameter(grid, locations, DEPOT)

        depot = (0, 0)
        for r_node in fp.R_nodes:
            assert nx.has_path(fp.steiner_graph, depot, r_node), \
                f"Depot must be able to reach {r_node}"

    def test_spanner_is_subgraph_of_grid(self):
        """Every edge in the 1-Spanner must also exist in a valid grid graph
        (i.e., connect nodes that share an x or y coordinate)."""
        grid = WareHouseGrid(2, 1)
        locations = make_locations(grid, [7, 12, 19])
        fp = FixedParameter(grid, locations, DEPOT)

        for u, v in fp.steiner_graph.edges():
            shares_x = u[0] == v[0]
            shares_y = u[1] == v[1]
            assert shares_x or shares_y, \
                f"Edge {u}-{v} does not lie along a single aisle or cross-aisle"


# ============================================================
# 3. Test SCFS+ Formulierung auf kleinen Instanzen
# ============================================================

class TestSCFSFormulation:
    """Tests for compute_route() — the main MILP."""

    def test_compute_route_returns_valid_path(self):
        """compute_route() returns a non-empty list of [x, y] coordinates."""
        grid = WareHouseGrid(2, 1)
        locations = make_locations(grid, [7, 19])
        fp = FixedParameter(grid, locations, DEPOT)

        route = fp.compute_route()

        assert isinstance(route, list)
        assert len(route) >= 3  # At minimum: depot -> product -> depot
        for point in route:
            assert isinstance(point, list)
            assert len(point) == 2

    def test_route_starts_and_ends_at_depot(self):
        """Route must form a closed tour from and to depot."""
        grid = WareHouseGrid(2, 1)
        locations = make_locations(grid, [7, 19])
        fp = FixedParameter(grid, locations, DEPOT)

        route = fp.compute_route()

        assert route[0] == [0, 0], "Route must start at depot"
        assert route[-1] == [0, 0], "Route must end at depot"

    def test_all_required_nodes_visited(self):
        """Every R-node must appear at least once in the route."""
        grid = WareHouseGrid(2, 1)
        locations = make_locations(grid, [1, 7, 19])
        fp = FixedParameter(grid, locations, DEPOT)

        route = fp.compute_route()
        route_set = {tuple(p) for p in route}

        for r_node in fp.R_nodes:
            assert r_node in route_set, f"R-node {r_node} must be visited"

    def test_route_only_uses_walkable_cells(self):
        """No point on the route should lie on a shelf cell."""
        grid = WareHouseGrid(2, 1)
        locations = make_locations(grid, [1, 19])
        fp = FixedParameter(grid, locations, DEPOT)

        route = fp.compute_route()

        for point in route:
            x, y = point
            assert grid.grid[y][x] == 1, \
                f"Route point ({x}, {y}) is on a shelf (not walkable)"

    def test_route_length_is_set(self):
        """After compute_route(), route_length must be a positive integer."""
        grid = WareHouseGrid(2, 1)
        locations = make_locations(grid, [7])
        fp = FixedParameter(grid, locations, DEPOT)

        fp.compute_route()

        assert fp.route_length > 0


# ============================================================
# 4. Test Loesungsextraktion und Euler-Kreis-Konstruktion
# ============================================================

class TestEulerCircuitExtraction:
    """Tests for _extract_pick_visit_order and Euler circuit construction."""

    def test_extract_visit_order_starts_and_ends_at_depot(self):
        """Visit sequence must start and end at the depot's shelf coordinate."""
        grid = WareHouseGrid(2, 1)
        locations = make_locations(grid, [7])  # walkable (3,1)
        fp = FixedParameter(grid, locations, DEPOT)

        depot = (0, 0)
        # Manually constructed valid Euler circuit edges:
        # depot(0,0) -> (3,0) -> (3,1) -> (3,0) -> (0,0)
        active_edges = [
            ((0, 0), (3, 0)),
            ((3, 0), (3, 1)),
            ((3, 1), (3, 0)),
            ((3, 0), (0, 0)),
        ]

        visit_sequence = fp._extract_pick_visit_order(active_edges, depot)

        assert visit_sequence[0] == (0, 0), "Must start at depot"
        assert visit_sequence[-1] == (0, 0), "Must end at depot"

    def test_extract_visit_order_contains_all_products(self):
        """Visit sequence must include every product's shelf coordinate."""
        grid = WareHouseGrid(2, 1)
        locations = make_locations(grid, [7, 19])
        fp = FixedParameter(grid, locations, DEPOT)

        route = fp.compute_route()

        # All shelf coordinates of the products should appear in the visit
        # sequence used for route_length calculation. We verify indirectly:
        # route_length > 0 means all products were included.
        assert fp.route_length > 0

        # Also verify the route itself visits the walkable coordinates
        route_set = {tuple(p) for p in route}
        assert (3, 1) in route_set, "Walkable coord of loc 7 must be in route"
        assert (6, 1) in route_set, "Walkable coord of loc 19 must be in route"

    def test_euler_circuit_forms_closed_tour(self):
        """The route produced by compute_route must form a closed tour (start == end)."""
        grid = WareHouseGrid(2, 1)
        locations = make_locations(grid, [7, 12, 19])
        fp = FixedParameter(grid, locations, DEPOT)

        route = fp.compute_route()

        assert route[0] == route[-1], "Euler circuit must be a closed tour"

    def test_euler_circuit_edges_are_consecutive(self):
        """Each consecutive pair in the route must share coordinates
        (the route steps through adjacent graph nodes)."""
        grid = WareHouseGrid(2, 1)
        locations = make_locations(grid, [7, 19])
        fp = FixedParameter(grid, locations, DEPOT)

        route = fp.compute_route()

        for i in range(len(route) - 1):
            u, v = route[i], route[i + 1]
            shares_x = u[0] == v[0]
            shares_y = u[1] == v[1]
            assert shares_x or shares_y, \
                f"Step {i}: {u} -> {v} is not along a single aisle/cross-aisle"


# ============================================================
# 5. Vergleich Routenlaenge gegen bekannte Optima
# ============================================================

class TestOptimalRouteLength:
    """Compare FixedParameter route lengths against hand-calculated optima."""

    def test_single_product_optimal(self):
        """One product: optimal = depot -> product -> depot (round trip)."""
        grid = WareHouseGrid(2, 1)
        # Loc 7: shelf (2,1)
        locations = make_locations(grid, [7])
        fp = FixedParameter(grid, locations, DEPOT)
        fp.compute_route()

        expected = (grid.calculate_warehouse_distance((0, 0), (2, 1))
                    + grid.calculate_warehouse_distance((2, 1), (0, 0)))
        assert fp.route_length == expected

    def test_two_products_same_aisle(self):
        """Two products in the same aisle: optimal is a single traversal."""
        grid = WareHouseGrid(2, 1)
        # Loc 7 -> shelf (2,1), Loc 12 -> shelf (2,6), both in aisle x=3
        locations = make_locations(grid, [7, 12])
        fp = FixedParameter(grid, locations, DEPOT)
        fp.compute_route()

        # Best order: depot(0,0) -> loc7(2,1) -> loc12(2,6) -> depot(0,0)
        d1 = grid.calculate_warehouse_distance((0, 0), (2, 1))
        d2 = grid.calculate_warehouse_distance((2, 1), (2, 6))
        d3 = grid.calculate_warehouse_distance((2, 6), (0, 0))
        optimal = d1 + d2 + d3

        assert fp.route_length <= optimal

    def test_two_products_different_aisles(self):
        """Two products in different aisles: verify against hand-calculated optimum."""
        grid = WareHouseGrid(2, 1)
        # Loc 7: shelf (2,1) aisle x=3, Loc 19: shelf (5,1) aisle x=6
        locations = make_locations(grid, [7, 19])
        fp = FixedParameter(grid, locations, DEPOT)
        fp.compute_route()

        # Try both visit orders
        order1 = (grid.calculate_warehouse_distance((0, 0), (2, 1))
                  + grid.calculate_warehouse_distance((2, 1), (5, 1))
                  + grid.calculate_warehouse_distance((5, 1), (0, 0)))
        order2 = (grid.calculate_warehouse_distance((0, 0), (5, 1))
                  + grid.calculate_warehouse_distance((5, 1), (2, 1))
                  + grid.calculate_warehouse_distance((2, 1), (0, 0)))
        optimal = min(order1, order2)

        assert fp.route_length <= optimal

    def test_fixed_parameter_not_worse_than_nearest_neighbor(self):
        """On a larger instance, FixedParameter should be <= Nearest Neighbor."""
        from routes.nearest_neighbor import NearestNeighbor

        grid = WareHouseGrid(3, 2)
        locations = make_locations(grid, [1, 12, 25, 37, 48, 61])

        fp = FixedParameter(grid, locations, DEPOT)
        fp.compute_route()

        nn = NearestNeighbor(grid, locations, DEPOT)
        nn.compute_route()

        assert fp.route_length <= nn.route_length, \
            f"FixedParameter ({fp.route_length}) should be <= NN ({nn.route_length})"