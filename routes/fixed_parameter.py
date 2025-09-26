from routes.base import BaseRoute
from collections import namedtuple

from collections import namedtuple

# A state is a tuple of parities and a tuple of component labels.
# e.g., State(parities=('E', 'U', 'U', '0'), components=(1, 2, 2, None))
State = namedtuple('State', ['parities', 'components'])


class FixedParameter(BaseRoute):
    def __init__(self, grid, locations, start_pos):
        super().__init__(grid, locations, start_pos)
        self.vertices = []
        self.nodes = []
        self._get_loc_isle_number()
        self._create_base_nodes()
        self.required_nodes = set()
        for loc in self.locations:
            # Convert location coordinates to grid indices
            grid_x = loc["isle"]
            grid_y = loc['y'] // 7  # Assuming row height is 7
            self.required_nodes.add((grid_x, grid_y))

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
        Todo zeichne den scheiß auf und mache dir mal einen richtigen plan du opfer
        """
        h = self.grid.num_rows + 1
        v = self.grid.num_isles + 1

        # 1. Initialization
        initial_parities = tuple('0' for _ in range(h))
        initial_components = tuple(None for _ in range(h))
        initial_state = State(parities=initial_parities, components=initial_components)

        dp_layers = [{initial_state: 0}]

        # 2. Define Edge Processing Order
        edges = self._get_edges_in_processing_order(h, v)

        # 3. Main Loop
        for l, edge in enumerate(edges):
            current_layer_states = dp_layers[l]
            next_layer_states = {}

            for state, cost in current_layer_states.items():
                # Consider all possible transitions for this edge
                # Transition 1: Add 0 edges
                self._update_next_layer(next_layer_states, state, cost, edge, num_added=0)

                # Transition 2: Add 1 edge
                self._update_next_layer(next_layer_states, state, cost, edge, num_added=1)

                # Transition 3: Add 2 edges
                self._update_next_layer(next_layer_states, state, cost, edge, num_added=2)

            dp_layers.append(next_layer_states)

        # 4. Find the Optimal Final Tour
        final_layer = dp_layers[-1]
        min_cost = float('inf')

        for state, cost in final_layer.items():
            # A valid final tour must have one connected component and all even degrees
            # (or be empty if a point is not on the tour) [cite: 286, 289]
            if self._is_valid_final_state(state):
                if cost < min_cost:
                    min_cost = cost

        return min_cost

    # ================= Helper Functions =================

    def _is_valid_final_state(self, state):
        """
        Checks if a state in the final layer represents a valid, complete tour.
        """
        # 1. Check for even degrees: No 'U' (uneven/odd) parities allowed.
        if 'U' in state.parities:
            return False

        # 2. Check for connectedness: There should be at most one component.
        # We find the first valid component ID and ensure no other component IDs exist.
        first_component_id = None
        for comp_id in state.components:
            if comp_id is not None:
                if first_component_id is None:
                    first_component_id = comp_id
                elif first_component_id != comp_id:
                    return False  # Found more than one component, so not connected

        return True

    def _is_state_valid(self, state):
        """
        Checks if a state is valid, primarily by checking for non-crossing partitions.
        """
        components = state.components
        h = len(components)

        # Check for non-crossing partitions
        for a in range(h):
            for b in range(a + 1, h):
                for c in range(b + 1, h):
                    for d in range(c + 1, h):
                        comp_a = components[a]
                        comp_b = components[b]
                        comp_c = components[c]
                        comp_d = components[d]

                        # Condition for a crossing partition
                        if comp_a is not None and comp_b is not None and \
                                comp_a == comp_c and comp_b == comp_d and comp_a != comp_b:
                            return False  # Found a crossing, state is invalid

        return True  # State is valid

    def _get_edges_in_processing_order(self, h, v):
        """
        Generates the list of all grid edges in the correct processing order.
        h: number of horizontal lines (rows)
        v: number of vertical lines (columns)
        """
        edges = []
        for j in range(v - 1):  # Iterate through columns
            # Add vertical edges in the current column j
            for i in range(h - 1):
                # The frontier is always a single column of h nodes.
                # An edge connects node i and node i+1 in that column.
                edges.append(
                    {'type': 'vertical', 'col': j, 'idx1': i, 'idx2': i + 1, 'length': 7})  # Assuming row height is 7

            # Add horizontal edges connecting column j to j+1
            for i in range(h):
                # This transition moves the frontier from column j to j+1.
                # The edge connects node i in the old frontier to node i in the new one.
                edges.append(
                    {'type': 'horizontal', 'col': j, 'idx1': i, 'idx2': i, 'length': 3})  # Assuming isle width is 3

        # Add the last column of vertical edges
        for i in range(h - 1):
            edges.append({'type': 'vertical', 'col': v - 1, 'idx1': i, 'idx2': i + 1, 'length': 7})

        return edges

    def _update_next_layer(self, next_layer, old_state, old_cost, edge, num_added):
        """Applies a transition and updates the next DP layer."""

        # edge = (node_idx_1, node_idx_2, length)

        # 1. Calculate the new state based on old_state and the transition
        new_state = self._apply_transition(old_state, edge, num_added)

        # 2. Check if the new state is valid (e.g., non-crossing, etc.) [cite: 292]
        if not self._is_state_valid(new_state):
            return

        # 3. Calculate the new cost
        transition_cost = num_added * edge['length']
        new_cost = old_cost + transition_cost

        # 4. Update the DP table for the next layer
        if new_state not in next_layer or new_cost < next_layer[new_state]:
            next_layer[new_state] = new_cost

    def _apply_transition(self, state, edge, num_added):
        if num_added == 0:
            return state  # No change for any edge type

        parities = list(state.parities)
        components = list(state.components)

        # --- Logic for Vertical Edges (within the same frontier) ---
        if edge['type'] == 'vertical':
            idx1, idx2 = edge['idx1'], edge['idx2']
            # This part of your existing code is correct!
            if num_added == 1:
                for idx in [idx1, idx2]:
                    if parities[idx] == '0':
                        parities[idx] = 'U'
                    elif parities[idx] == 'U':
                        parities[idx] = 'E'
                    else:
                        parities[idx] = 'U'

            comp1, comp2 = components[idx1], components[idx2]
            if comp1 is None and comp2 is None:
                new_comp_id = max((c for c in components if c is not None), default=0) + 1
                components[idx1] = components[idx2] = new_comp_id
            elif comp1 is not None and comp2 is None:
                components[idx2] = comp1
            elif comp1 is None and comp2 is not None:
                components[idx1] = comp2
            elif comp1 != comp2:
                for i, c in enumerate(components):
                    if c == comp2: components[i] = comp1

            return State(parities=tuple(parities), components=tuple(components))

        # --- Logic for Horizontal Edges (shifting to a new frontier) ---
        elif edge['type'] == 'horizontal':
            # A horizontal transition creates a state for the *next* frontier.
            # It's simpler: it just carries over the state of a single node.
            # We start with a blank state for the new frontier.
            new_parities = ['0'] * len(parities)
            new_components = [None] * len(components)
            idx = edge['idx1']  # idx1 and idx2 are the same for horizontal edges

            # The node `idx` on the new frontier inherits the state.
            # Parity update is the same as before.
            if num_added == 1:
                new_parities[idx] = 'U'
            else:  # num_added == 2
                new_parities[idx] = 'E'

            new_components[idx] = 1  # Each horizontal connection starts its own new component

            # NOTE: This is a simplified view. A more robust implementation would merge
            # these new single-node components after all horizontal edges for a column are processed.
            # For now, this structure is a good starting point.

            # A horizontal edge "consumes" the old state and produces a state for the next frontier.
            # This means the main loop needs to be slightly adjusted to handle this transition
            # from a full frontier state to the next. Let's refine the main loop below.
            pass  # We will adjust the main loop to handle this properly.

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
