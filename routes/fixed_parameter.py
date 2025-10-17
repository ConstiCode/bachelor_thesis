from routes.base import BaseRoute
from collections import namedtuple
from algorithms import AStar
from collections import defaultdict

# A state is a tuple of parities and a tuple of component labels.
# e.g., State(parities=('E', 'U', 'U', '0'), components=(1, 2, 2, None))
State = namedtuple('State', ['parities', 'components', 'visited_mask'])


class FixedParameter(BaseRoute):
    def __init__(self, grid, locations, start_pos):
        all_locations = locations.copy()
        all_locations.append(start_pos)
        super().__init__(grid, all_locations, start_pos)
        self.vertices = []
        self.nodes = []
        self._get_loc_isle_number()
        self._create_base_nodes()
        self.required_nodes = set()
        self.cell_to_location_map = {}
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
        h = self.grid.num_rows + 1
        v = self.grid.num_isles + 1

        # Map grid cells to the index of the required node they contain
        self.required_locations_map = {loc: i for i, loc in enumerate(self.required_nodes)}
        num_required = len(self.required_nodes)

        # 1. Initialization
        initial_parities = tuple('0' for _ in range(h))
        initial_components = tuple(None for _ in range(h))
        initial_mask = 0  # 000...0 in binary
        initial_state = State(parities=initial_parities, components=initial_components, visited_mask=initial_mask)

        # In compute_route function, initialization (Step 1)
        dp_layers = [{initial_state: {'cost': 0, 'parent': None, 'edge': None, 'num_added': 0}}]
        # 2. Define Edge Processing Order
        edges = self._get_edges_in_processing_order(h, v)

        # 3. Main Loop
        # In compute_route function, the main loop (Step 3)

        # ... inside the main loop ...
        for l, edge in enumerate(edges):
            current_layer_states = dp_layers[l]
            next_layer_states = {}

            for state, data in current_layer_states.items():
                cost = data['cost']  # <-- Change here
                # Consider all possible transitions for this edge
                self._update_next_layer(next_layer_states, state, cost, edge, num_added=0)
                self._update_next_layer(next_layer_states, state, cost, edge, num_added=1)
                self._update_next_layer(next_layer_states, state, cost, edge, num_added=2)

            dp_layers.append(next_layer_states)

        # 4. Find the Optimal Final Tour
        final_layer = dp_layers[-1]
        min_cost = float('inf')
        best_final_state = None

        for state, data in final_layer.items():
            if self._is_valid_final_state(state):
                if data['cost'] < min_cost:
                    min_cost = data['cost']
                    best_final_state = state

        if best_final_state is None:
            return None  # Or raise an error if no solution was found

        # Reconstruct the path of edges by backtracking
        edge_path = self._reconstruct_edge_path(best_final_state, dp_layers)

        # Convert the unordered edges into an ordered list of (x, y) waypoints
        ordered_locations = self._convert_edges_to_final_route(edge_path)

        # Format for A* and calculate the final detailed path
        # This now matches the output style of your other algorithms
        route_for_astar = [{'x': loc['x'], 'y': loc['y']} for loc in ordered_locations]

        a_star = AStar(self.grid.grid)
        full_route = a_star.calculate_a_star_route(route_for_astar)

        return full_route

    # ================= Helper Functions =================

    def _convert_edges_to_final_route(self, edge_path):
        """
        Converts the raw edge path from the DP into an ordered list of the
        original required location objects.
        """
        if not edge_path:
            return []

        # (This part is the same as before)
        # First, build the detailed tour of (x, y) waypoints
        # ...
        coord_edges = []
        for edge in edge_path:
            y1, y2 = edge['idx1'] * 7, edge['idx2'] * 7
            if edge['type'] == 'horizontal':
                x1, x2 = edge['col'] * 3, (edge['col'] + 1) * 3
            else:
                x1, x2 = edge['col'] * 3, edge['col'] * 3
            coord_edges.append(((x1, y1), (x2, y2)))

        graph = defaultdict(list)
        for u, v in coord_edges:
            graph[u].append(v)
            graph[v].append(u)

        start_node = coord_edges[0][0]
        stack, circuit = [start_node], []
        while stack:
            u = stack[-1]
            if graph[u]:
                v = graph[u].pop()
                graph[v].remove(u)
                stack.append(v)
            else:
                circuit.append(stack.pop())
        ordered_waypoints = circuit[::-1]

        # ✅ NEW LOGIC STARTS HERE
        # Now, walk the detailed tour and pick up locations in order
        ordered_locations = []
        visited_cells = set()

        for waypoint in ordered_waypoints:
            x, y = waypoint
            col, row = x // 3, y // 7

            for dx in [-1, 0]:
                for dy in [-1, 0]:
                    cell = (col + dx, row + dy)
                    if cell in self.cell_to_location_map and cell not in visited_cells:
                        location = self.cell_to_location_map[cell]
                        ordered_locations.append(location)
                        visited_cells.add(cell)

        # Find the start_pos in the generated tour and rotate the list
        # so that the tour starts and ends at the start_pos.
        if self.start_pos in ordered_locations:
            start_index = ordered_locations.index(self.start_pos)
            # Rotate the list to make start_pos the first element
            final_ordered_route = ordered_locations[start_index:] + ordered_locations[:start_index]
            # Add start_pos at the end to complete the loop
            final_ordered_route.append(self.start_pos)
            return final_ordered_route

        # Fallback if start_pos wasn't found (should not happen with the __init__ change)
        return [self.start_pos] + ordered_locations + [self.start_pos]

    def _reconstruct_edge_path(self, final_state, dp_layers):
        """
        Backtracks from the final state to reconstruct the list of edges used.
        """
        edge_path = []
        current_state = final_state

        # Iterate backwards through the layers and edges
        for i in range(len(dp_layers) - 1, 0, -1):
            layer_data = dp_layers[i][current_state]

            num_added = layer_data['num_added']
            if num_added > 0:
                # Add the edge 'num_added' times
                for _ in range(num_added):
                    edge_path.append(layer_data['edge'])

            # Move to the parent state in the previous layer
            current_state = layer_data['parent']

        edge_path.reverse()  # The path is built backwards, so reverse it
        return edge_path

    def _is_valid_final_state(self, state):
        num_required = len(self.required_nodes)

        # Case 1: No locations were required. The only valid state is the empty one.
        if num_required == 0:
            return state.visited_mask == 0 and \
                all(p == '0' for p in state.parities) and \
                all(c is None for c in state.components)

        # Case 2: Locations were required. First, check if all were visited.
        all_visited_mask = (1 << num_required) - 1
        if state.visited_mask != all_visited_mask:
            return False

        # Now, check the graph properties for the valid tour.
        # 1. No dead ends (all even parities).
        if 'U' in state.parities:
            return False

        # 2. Must be a single connected tour (exactly one component).
        first_component_id = None
        for comp_id in state.components:
            if comp_id is not None:
                if first_component_id is None:
                    first_component_id = comp_id
                elif first_component_id != comp_id:
                    return False  # More than one component found.

        # If all checks passed and we found a component, it's a valid tour.
        return first_component_id is not None

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

        new_state_tuple = self._apply_transition(old_state, edge, num_added)
        if new_state_tuple is None:
            return

        # Unpack the new parities and components
        new_parities, new_components = new_state_tuple

        # --- UPDATE THE MASK ---
        # In _update_next_layer function

        # --- UPDATE THE MASK ---
        new_mask = old_state.visited_mask
        if num_added > 0:
            col, row = edge['col'], edge['idx1']

            if edge['type'] == 'horizontal':
                # A horizontal edge can cover locations in cells above or below it
                for y_offset in [-1, 0]:
                    cell = (col, row + y_offset)
                    if cell in self.required_locations_map:
                        loc_index = self.required_locations_map[cell]
                        new_mask |= (1 << loc_index)

            elif edge['type'] == 'vertical':
                # A vertical edge can cover locations in cells to its left or right
                for x_offset in [-1, 0]:
                    cell = (col + x_offset, row)
                    if cell in self.required_locations_map:
                        loc_index = self.required_locations_map[cell]
                        new_mask |= (1 << loc_index)

        new_state = State(parities=new_parities, components=new_components, visited_mask=new_mask)

        # 2. Check if the new state is valid (e.g., non-crossing, etc.) [cite: 292]
        if not self._is_state_valid(new_state):
            return

        # 3. Calculate the new cost
        transition_cost = num_added * edge['length']
        new_cost = old_cost + transition_cost

        # 4. Update the DP table for the next layer
        if new_state not in next_layer or new_cost < next_layer[new_state]['cost']:
            next_layer[new_state] = {
                'cost': new_cost,
                'parent': old_state,
                'edge': edge,
                'num_added': num_added
            }

    def _apply_transition(self, state, edge, num_added):
        if num_added == 0:
            return state.parities, state.components  # No change for any edge type

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

            return tuple(parities), tuple(components)

        # --- Logic for Horizontal Edges (shifting to a new frontier) ---

        elif edge['type'] == 'horizontal':
            new_parities = ['0'] * len(parities)
            new_components = [None] * len(components)
            idx = edge['idx1']

            if num_added == 1:
                new_parities[idx] = 'U'
            else:  # num_added == 2
                new_parities[idx] = 'E'

            # This logic might need refinement, but for now, let's assign a component
            if num_added > 0:
                new_components[idx] = 1  # Simplified component assignment

            # Replace 'pass' with the return statement
            return tuple(new_parities), tuple(new_components)

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
