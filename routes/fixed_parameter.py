from routes.base import BaseRoute
from collections import namedtuple
from algorithms import AStar
from collections import defaultdict

# A state is a tuple of parities and a tuple of component labels.
# e.g., State(parities=('E', 'U', 'U', '0'), components=(1, 2, 2, None))
State = namedtuple('State', ['parities', 'components', 'visited_mask'])


class FixedParameter(BaseRoute):
    def __init__(self, grid, locations, start_pos):
        super().__init__(grid, locations, start_pos)

    def compute_route(self):
        pass

    def solve_rectilinear_steiner_tree(self):
        """
        Gemini Output:
        Start (Empty State): The algorithm begins with a single state representing no travel, with a cost of 0. All potential aisle entrances have a degree of 0.

        Sweep: The algorithm processes every single walkable segment (horizontal and vertical) in a fixed order.

        Expand and Evaluate: For each segment it encounters, it looks at every valid partial solution (state) found so far and asks: "What happens if we incorporate this new segment?"

        If the segment is HORIZONTAL (a cross-aisle): The expansion is simple. It connects two aisle entrances. The cost is the length of the segment, and the degrees of the connected entrances are updated (typically increased by 1).

        If the segment is VERTICAL (a picking aisle): The expansion is complex. This is where your six strategies come into play. For each existing state, the algorithm generates up to six new potential states, one for each valid traversal strategy. Each new state has:

        A new cost, calculated based on the specific strategy (e.g., partial travel cost vs. full travel cost).

        A new connectivity map.

        Updated degrees at the top and bottom entrances of that aisle, reflecting how the strategy was executed (e.g., a "there-and-back" strategy results in a degree of 2 at one entrance).

        Prune (The DP Magic 💡): After generating all these new states, the algorithm prunes them. If it finds two different ways to create the exact same state (same connectivity, same degrees), it keeps the one with the lower total cost and discards the more expensive one.

        Repeat: This process of expanding and pruning continues until every single segment in the warehouse has been considered.

        Find the Best: In the final layer of states, the algorithm looks for all states that represent a valid, complete tour (e.g., all items collected, starting and ending at the depot). It then returns the one with the overall lowest cost.

        Finds the minimum Rectilinear Steiner Tree for a set of terminals
        using a Dynamic Programming sweep-line algorithm.

        Returns:
            A tuple containing:
            - The optimal final state (representing the tree's connectivity).
            - The minimum cost (total length) of the Steiner Tree.
            Returns (None, float('inf')) if no solution is found.
        """
        initial_state = tuple(range(self.locations))
        current_layer = {initial_state: 0}

        # Iterate though all the edges of the warehouse in the order vertical then horizontal and left to right,
        # bottom to top
        all_aisles = self.get_all_aisles_in_order()

        for aisle in all_aisles:
            next_layer = {}

            terminals_in_this_aisle = self._get_terminals_in_aisle(aisle)

            for w, cost in current_layer.items():

                possible_transitions = self._get_aisle_traversal_strategies(w, aisle, terminals_in_this_aisle)

                # This is where your six options are generated!
                for (w_prime, transition_cost) in possible_transitions:
                    new_cost = cost + transition_cost

                    # The check_validity and update logic remains the same
                    if self.check_validity(w_prime):  # Simplified check
                        if new_cost < next_layer.get(w_prime, float('inf')):
                            next_layer[w_prime] = new_cost

                # We also need a "do nothing in this aisle" transition
                # This is equivalent to the "zero edge" transition
                if cost < next_layer.get(w, float('inf')):
                    next_layer[w] = cost

            current_layer = next_layer

        # --- Line 16 & 17: Find the optimal solution in the last layer ---
        w_opt = None
        min_cost = float('inf')

        # The optimal tree is the cheapest state where all terminals are connected.
        for final_state, final_cost in current_layer.items():
            if is_fully_connected(final_state, num_terminals):
                if final_cost < min_cost:
                    min_cost = final_cost
                    w_opt = final_state

        return w_opt, min_cost

    def _get_aisle_traversal_strategies(self, w, aisle, terminals_in_aisle):
        """
        Given an aisle (edge) and the terminals in that aisle, generates all possible traversal strategies
        and their associated costs.
        :param aisle: tuple of two coordinates defining the aisle ((x1, y1), (x2, y2))
        :param terminals_in_aisle: list of location coordinates that lie on the aisle
        :return: list of tuples (new_state, cost) for each traversal strategy
        """
        # A complete state 'w'
        current_connectivity, current_degrees = w

        # 1. Strategy Possible outcomes initialized with the "do nothing" option
        generated_transitions = [(w, 0)]

        start_of_aisle, end_of_aisle = aisle[0], aisle[1]

        # 2. Strategy: Go once through the aisle
        cost = 8
        new_degrees = list(current_degrees)
        new_connectivity = list(current_connectivity)
        # Update the degrees of the aisle entrances
        new_degrees[start_of_aisle] += 1
        new_degrees[end_of_aisle] += 1

        new_connectivity[start_of_aisle] = new_connectivity[end_of_aisle]

        w_prime = (tuple(new_connectivity), tuple(new_degrees))
        generated_transitions.append((w_prime, cost))

        # 3. Strategy: Go twice through the aisle
        cost = 16
        new_degrees = list(current_degrees)
        new_connectivity = list(current_connectivity)
        # Update the degrees of the aisle entrances
        new_degrees[start_of_aisle] += 2
        new_degrees[end_of_aisle] += 2
        new_connectivity[start_of_aisle] = new_connectivity[end_of_aisle]

        if terminals_in_aisle:
            # Todo debug
            # 4. Strategy: Go to the most distant terminal and back (from start)
            furthest_terminal = max(terminals_in_aisle, key=lambda loc: abs(loc[1] - start_of_aisle[1]))
            closest_terminal = min(terminals_in_aisle, key=lambda loc: abs(loc[1] - start_of_aisle[1]))
            cost = 2 * abs(furthest_terminal[1] - start_of_aisle[1])
            new_degrees = list(current_degrees)
            new_connectivity = list(current_connectivity)
            new_degrees[start_of_aisle] += 2
            w_prime = (tuple(new_connectivity), tuple(new_degrees))
            generated_transitions.append((w_prime, cost))

            if furthest_terminal != closest_terminal:
                # 5. Strategy: Go to the closest terminal and back (from end)


        # Example:
        # connectivity_tuple = (0, 0, 2, 3)  # DSU parent pointers for terminals
        # degrees_tuple = (1, 1, 0, 0, 2, 0)  # Degrees for aisle entrances 1, 2, 3, 4, 5, 6...

        # Traversal strategies that can always be applied
        # 1. Do nothing
        res = [(w, 0)]

        # 2. Go once through the aisle
        res.append((w, 8))

        # 3. Go twice through the aisle
        res.append((, 16))
        # Traversal strategies that depend on terminals in the aisle
        # 4. Go to the most distant terminal and back (from start)
        # 5. Split the aisle at the biggest gap between terminals and go to both ends and back










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

    def _get_terminals_in_aisle(self, edge):
        """
        Takes an edge defined by its start coordinate and end coordinate and a list of locations and returns all the
        locations that lie on that edge.
        :param edge: tuple of two coordinates defining the edge ((x1, y1), (x2, y2))
        :return: list of location coordinates that lie on the edge
        """
        index = 0 if edge[0][0] == edge[1][0] else 1
        interval = sorted([edge[0][1 - index], edge[1][1 - index]])
        edge_comparor = edge[0][index]
        res = []
        for location in self.locations:
            self.grid._turn_location_coordinate_to_route_loc((location['x'], location['y'])) # Todo clean up
            if location[index] != edge_comparor and location[1 - index] not in interval:
               continue
            res.append(location)
        return res



    def apply_transition(self, state, edge):
        """
        Takes a state (connectivity tuple) and an edge, performs a union
        operation on the components of the edge's endpoints, and returns
        the new state tuple.
        """

        return state

    def get_edge_length(self, edge):
        """Returns the length of an edge. Where the edge length is denoted as the Manhattan distance between its two endpoints."""
        x1, y1 = edge[0]
        x2, y2 = edge[1]
        return abs(x1 - x2) + abs(y1 - y2)

    def get_all_aisles_in_order(self):
        """
        Generates all valid walkable aisle segments for a given warehouse layout.
        Returns a list of edges, where each edge is represented by its start and end coordinates and is sorted in a
        alternating manner from left to right, bottom to top.
        """
        num_isles = self.grid.num_isles
        num_rows = self.grid.num_rows

        walkable_edges = []

        # 1. Generate Vertical Aisle Edges
        for isle in range(num_isles):
            for row in range(num_rows - 1):
                coordinate = isle * 3, row * 7
                coordinate_2 = isle * 3, (row + 1) * 7
                walkable_edges.append((coordinate, coordinate_2))

        # 2. Generate Horizontal Cross-Aisle Edges
        for row in range(num_rows):
            for isle in range(num_isles - 1):
                coordinate = isle * 3, row * 7
                coordinate_2 = (isle + 1) * 3, row * 7
                walkable_edges.append((coordinate, coordinate_2))
        sorted_edges = sorted(walkable_edges, key=lambda edge: (min(edge[0][1], edge[1][1]), min(edge[0][0], edge[1][0])))

        return sorted_edges


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
        if len(y_values) < 2:
            return None, None

        sorted_y = sorted(y_values)

        max_gap = 0
        biggest_gap_pair = None, None

        for i in range(1, len(sorted_y)):
            gap = sorted_y[i] - sorted_y[i - 1]

            if gap > max_gap:
                max_gap = gap
                biggest_gap_pair = (sorted_y[i - 1], sorted_y[i])

        return biggest_gap_pair


# =====================================================================================================================

# ASSUMED HELPER FUNCTIONS (You would need to implement these)
# -----------------------------------------------------------------
def get_warehouse_walkable_edges(self, layout_info):
    """
    Generates all valid walkable aisle segments for a given warehouse layout.
    Returns a list of edges, where each edge is represented by its start and end coordinates.
    """
    num_isles = self.grid.num_isles
    num_rows = self.grid.num_rows

    walkable_edges = []

    # 1. Generate Vertical Aisle Edges
    aisle_columns = [(1, 2), (3, 4), (5, 6)]  # Example based on your layout
    shelf_rows_top = range(1, 7)
    shelf_rows_bottom = range(8, 14)

    for col1, col2 in aisle_columns:
        # Create edges for the top shelf block
        for row in shelf_rows_top:
            # Add the edge representing the path between shelves at this row
            # e.g., walkable_edges.append( ((col1_x, row_y), (col2_x, row_y)) )
            pass
        # Create edges for the bottom shelf block
        for row in shelf_rows_bottom:
            # Add the edge
            pass

    # 2. Generate Horizontal Cross-Aisle Edges
    cross_aisle_rows = [0, 7, 14]  # Representing top, middle, and bottom

    for row_y in cross_aisle_rows:
        # Create edges connecting the entrances of the vertical aisles
        # e.g., walkable_edges.append( ((aisle1_x, row_y), (aisle2_x, row_y)) )
        pass

    # The list should be sorted, as required by the sweep-line algorithm
    # (e.g., from bottom to top, left to right)
    sorted_edges = sorted(walkable_edges, key=lambda edge: (min(edge[0][1], edge[1][1]), min(edge[0][0], edge[1][0])))

    return sorted_edges
