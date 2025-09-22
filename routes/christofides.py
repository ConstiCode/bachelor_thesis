from .base import BaseRoute
from algorithms import AStar
import heapq
from collections import Counter
from collections import defaultdict



class Christofides(BaseRoute):

    def compute_route(self):
        self.locations.append(self.start_pos)

        # Todo this does not work for 1 location
        # Todo refactor this
        edges = self._get_mst_weights(self.locations, self.grid.num_isles, self.grid.num_rows)
        # use prims algorithm to get the minimum spanning tree
        mst = self._get_prim_mst(edges[1:], edges[0][1])

        # get the odd degree nodes
        odd_nodes =  self._get_odd_nodes(mst)

        # Todo find a proper way to refactor this
        matched_nodes = self.minimum_weight_perfect_matching(odd_nodes, self.grid.num_rows, self.grid.num_isles)

        all_nodes =  self.augment_mst_with_matching(mst, matched_nodes)
        route = []
        for triple in mst:
            route.append(((triple[1][1], triple[1][0]), (triple[2][1], triple[2][0])))

        route =  self.create_round_route_from_edges(route)

        self.route_length = sum(self.grid.calculate_warehouse_distance(p1, p2) for p1, p2 in zip(route, route[1:]))

        a_star = AStar(self.grid.grid)
        full_route = a_star.calculate_a_star_route([{'x': x, 'y': y} for (x, y) in route])


        return full_route

    def _get_mst_weights(self, locations, num_shelf_cols, num_shelf_rows):
        edges = []
        for location in locations:
            for other_location in locations:
                if location != other_location:
                    route = (location, other_location)
                    start_loc = (location.get('y'), location.get('x'))
                    end_loc = (other_location.get('y'), other_location.get('x'))

                    a_star = AStar(self.grid.grid)
                    # Todo check if i can use the optimised version here distance calc !!!!!!!!!!!!!!!!!!
                    # Todo check if the weight is correct here. Could it be that the weight should be len(full_route) -1
                    #  as the start position is included in the full route?
                    full_route = a_star.calculate_a_star_route(route)

                    weight = len(full_route)

                    # Check if the inverted edge already exists
                    if (weight, start_loc, end_loc) not in edges:
                        edges.append(
                            (weight, end_loc, start_loc))
        return edges


    def _get_prim_mst(self, edges, start_node):
        """
        Computes the Minimum Spanning Tree (MST) of a graph using Prim's algorithm.

        Args:
            edges: A list of edges, where each edge is a tuple (weight, node1, node2).
            start_node: The starting node for Prim's algorithm.

        Returns:
            A list of edges in the MST, or None if the graph is disconnected.
        """

        mst = []
        visited = {start_node}
        priority_queue = []  # Use a min-heap

        # Add initial edges from the start node to the priority queue
        for weight, u, v in edges:
            if u == start_node or v == start_node:
                heapq.heappush(priority_queue, (weight, u, v))

        num_nodes = len(self.locations)

        while len(mst) < num_nodes - 1:
            if not priority_queue:
                return None  # Graph is disconnected

            weight, u, v = heapq.heappop(priority_queue)

            # Only proceed if this edge connects visited -> unvisited
            if u in visited and v not in visited:
                next_node = v
            elif v in visited and u not in visited:
                next_node = u
            else:
                continue  # Edge would form a cycle

            mst.append((weight, u, v))
            visited.add(next_node)

            # Add new edges from newly visited node
            for next_weight, next_u, next_v in edges:
                if next_u == next_node or next_v == next_node:
                    if (next_u in visited and next_v not in visited) or \
                            (next_v in visited and next_u not in visited):
                        heapq.heappush(priority_queue, (next_weight, next_u, next_v))
        return mst

    def _get_odd_nodes(self, mst):
        """ Get odd degree nodes from the minimum spanning tree. """

        locs = [item for item, count in Counter(inner_tuple for _, *tuples in mst for inner_tuple in tuples).items() if
                count % 2 != 0]
        return locs

    def minimum_weight_perfect_matching(self, odd_nodes, num_shelf_rows, num_shelf_cols):
        matched = set()
        matching = []

        for i in range(len(odd_nodes)):
            if odd_nodes[i] in matched:
                continue
            best_dist = float('inf')
            best_match = None
            for j in range(i + 1, len(odd_nodes)):
                if odd_nodes[j] in matched:
                    continue
                d = self._get_mst_weights(
                    [{'x': odd_nodes[i][1], 'y': odd_nodes[i][0]}, {'x': odd_nodes[j][1], 'y': odd_nodes[j][0]}],
                    num_shelf_cols, num_shelf_rows)[0][0]
                if d < best_dist:
                    best_dist = d
                    best_match = odd_nodes[j]
            if best_match:
                matching.append((odd_nodes[i], best_match))
                matched.add(odd_nodes[i])
                matched.add(best_match)

        return matching

    def augment_mst_with_matching(self, mst, matching):
        for node1, node2 in matching:
            weight = self._get_mst_weights([{'x': node1[1], 'y': node1[0]}, {'x': node2[1], 'y': node2[0]}], self.grid.num_isles,
                                      self.grid.num_rows)[0][0]
            mst.append((weight, node1, node2))
        return mst

    def create_round_route_from_edges(self, edges):
        """
        Creates a Hamiltonian cycle approximation from the Eulerian multigraph.
        Uses Hierholzer's algorithm for Eulerian tour, then shortcuts repeats.
        :param edges: List of edges as ((x1, y1), (x2, y2))
        :return: List of coordinates in order
        """
        if not edges:
            return []

        # Build adjacency list
        graph = defaultdict(list)
        for u, v in edges:
            graph[u].append(v)
            graph[v].append(u)

        # Hierholzer's algorithm for Eulerian circuit
        start = edges[0][0]
        stack = [start]
        circuit = []

        while stack:
            u = stack[-1]
            if graph[u]:
                v = graph[u].pop()
                graph[v].remove(u)
                stack.append(v)
            else:
                circuit.append(stack.pop())

        # Remove duplicates to create Hamiltonian cycle
        visited = set()
        route = []
        for node in circuit[::-1]:  # reverse because Hierholzer gives reverse order
            if node not in visited:
                route.append(node)
                visited.add(node)

        # Make it a round trip by returning to start
        route.append(route[0])

        return route
