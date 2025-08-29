from routes.base import BaseRoute


class FixedParameter(BaseRoute):
    def __init__(self, grid, locations, start_pos):
        super().__init__(grid, locations, start_pos)
        self.vertices = []
        self.nodes = []
        self._get_loc_isle_number()
        self._create_base_nodes()

    # ================= Init Functions =================
    def _get_loc_isle_number(self):
        """
        Helper that gets the isle number for each location.
        1 --> 0
        2 --> 1
        4 --> 1
        5 --> 2
        7 --> 2
        8 --> 3
        10 --> 3
        11 --> 4
        13 --> 4
        14 --> 5

        """
        for loc in self.locations:
            x = loc.get('x')
            if x % 3 == 0:
                raise ValueError("Es kann keine Location auf einem Gang geben")
            loc["isle"] = (x - x // 3) // 2

    def _create_base_nodes(self):
        for x in range(self.grid.num_isles + 1):
            for y in range(self.grid.num_rows + 1):
                self.nodes.append(Node(x, y * 7, 0))

    # ================= Main Function =================

    def compute_route(self):
        """
        Traverse Trough each isle and create all possible vertices. One vertex has number_of_rows + 1 nodes. Create all
        possible edge combinations.
        :return:
        """
        self._compute_paths(self.nodes[0], self.nodes[1],
                                                  [d['y'] for d in self.locations if d['isle'] == 0 and d['y'] < 7])
        self._extend_paths(self.nodes[2],
                                       [d['y'] for d in self.locations if d['isle'] == 0 and d['y'] > 7])
        pass

    # ================= Helper Functions =================

    def _compute_paths(self, start_node, end_node, relevant_y_locs):
        """
            Returns six possible vertical paths between two nodes with varying degrees of traversal.

            :param start_node: First node object with attributes `degree` and methods `compute_furthest_cost` and `compute_biggest_aisle_split`.
            :param end_node: Second node object, similar requirements as node_1.
            :param relevant_y_locs: List of y-coordinates relevant for aisle computations.
        """

        vertices = []
        # First option - do nothing
        start_node.degree, end_node.degree = 0, 0
        self.vertices.append(Vertex([start_node, end_node], 0))

        # Second option - go once through the aisle
        start_node.degree, end_node.degree = 1, 1
        self.vertices.append(Vertex([start_node, end_node], 6))

        # Third option - go twice through the aisle
        start_node.degree, end_node.degree = 2, 2
        self.vertices.append(Vertex([start_node, end_node], 12))

        if not relevant_y_locs:
            return

        # Fourth and fifth option - go to the most distant location and then turn around (both ways)
        start_node.degree, end_node.degree = 2, 0
        self.vertices.append(Vertex([start_node, end_node], start_node.compute_furthest_cost(relevant_y_locs)))
        start_node.degree, end_node.degree = 0, 2
        self.vertices.append(Vertex([start_node, end_node], end_node.compute_furthest_cost(relevant_y_locs)))

        if not len(relevant_y_locs) >= 2:
            return vertices
            # Sixth option - find the biggest gap between two relevant locations and go there and back from each node
        start_node.degree, end_node.degree = 2, 2
        gap = start_node.compute_biggest_aisle_split(relevant_y_locs)
        vertices.append(Vertex([start_node, end_node], (gap[0] + (7 - gap[1])) * 2))

        self.vertices = vertices

    def _extend_paths(self, next_node, relevant_y_locs):
        """
        For each existing path, creates new, longer paths by adding all
        possible segments to the next_node.
        """
        for vertex in self.vertices:
            last_node_in_path = vertex.nodes[-1]

            new_segments = self._compute_paths(last_node_in_path, next_node, relevant_y_locs)

            for segment in new_segments:
                # Combine the old path with the new segment
                new_total_cost = vertex.cost + segment.cost
                new_node_list = vertex.nodes + [next_node]

                # Create the new, longer path
                self.vertices.append(Vertex(new_node_list, new_total_cost))

class Vertex:
    """
    A vertex describes a number of nodes in a graph, that are on a border of a split. The graph is split to find optimal
    subroutes.
    """

    def __init__(self, nodes, cost):
        self.nodes = nodes
        self.cost = cost


class Node:
    """
    A node describes a location in the warehouse. It contains the location itself and the edges to other nodes.
    """

    def __init__(self, x, y, degree):
        self.x = x
        self.y = y
        self.degree = degree

    def is_odd(self):
        return self.degree % 2 == 1

    def compute_furthest_cost(self, y_values):
        """
        Returns the cost to travel to a given y value from the current node.
        :param y_values:
        :return:
        """
        return max((abs(self.y - y) * 2 for y in y_values), default=0)

    def compute_biggest_aisle_split(self, y_values):
        # If there are fewer than 2 values, no gap can exist.
        if len(y_values) < 2:
            return None, None

        sorted_y = sorted(y_values)

        max_gap = 0
        # This tuple will store the two numbers that have the biggest gap.
        biggest_gap_pair = None, None

        for i in range(1, len(sorted_y)):
            gap = sorted_y[i] - sorted_y[i - 1]

            # If we find a new biggest gap...
            if gap > max_gap:
                max_gap = gap
                # ...store the pair of values that created it.
                biggest_gap_pair = (sorted_y[i - 1], sorted_y[i])

        return biggest_gap_pair
