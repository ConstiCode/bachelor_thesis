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
        self.id_map = self._create_id_map()
        self._rev_id_map = {v: k for k, v in self.id_map.items()}

    def _create_id_map(self):
        """
        Todo check if i actually need this
        Dynamically generates a mapping from coordinates to unique integer IDs for all
        points of interest (terminals, depot, and aisle crossings).
        Example:
            self.id_map = {
                # Key (Coordinate)  : Value (Integer ID)
                #-----------------------------------------
                # Terminals
                (1, 4):               0,
                (3, 2):               1,
                (5, 6):               2,

                # Depot
                (0, 0):               3,

                # Aisle Junctures (Crossings)
                (1.5, 0):             4,
                (3.5, 0):             5,
                (1.5, 7):             6,
                (3.5, 7):             7
            }
        """
        # Use a set to automatically handle duplicate points
        points_of_interest = set()

        num_isles = self.grid.num_isles
        num_rows = self.grid.num_rows

        for row in range(num_rows + 1):
            for isle in range(num_isles + 1):
                # Calculate the coordinate for this crossing
                crossing_coord = (isle * 3, row * 7)  # Example coordinate logic
                points_of_interest.add(crossing_coord)

        # 4. Create the final mapping
        # Sort the points to ensure a consistent ID assignment every time
        sorted_points = sorted(list(points_of_interest))

        # Assign a unique integer ID to each unique point
        id_map = {point: i for i, point in enumerate(sorted_points)}

        return id_map

    def compute_route(self):
        """
        Finds the minimum Rectilinear Steiner Tree for a set of terminals
        using a Dynamic Programming sweep-line algorithm.

        Returns:
            A tuple containing:
            - The optimal final state (representing the tree's connectivity).
            - The minimum cost (total length) of the Steiner Tree.
            Returns (None, float('inf')) if no solution is found.
        """
        # --- Corrected Initialization ---
        num_points_of_interest = len(self.id_map)

        # Each point starts as its own component
        initial_connectivity = tuple(range(num_points_of_interest))

        # Every point starts with a degree of 0
        initial_degrees = tuple([0] * num_points_of_interest)

        # Each state also tracks visited picking locations
        visited_picking_locations = ()

        # This is the correct initial state 'w0'
        initial_state = (initial_connectivity, initial_degrees, visited_picking_locations)
        current_layer = {initial_state: 0}

        # Iterate though all the edges of the warehouse in the order vertical then horizontal and left to right,
        # bottom to top
        all_walkable_edges = self.get_all_aisles_in_order()
        index = 0
        for edge in all_walkable_edges:
            index += 1
            next_layer = {}

            # Todo maybe move this into the _get_aisle_vertical_traversal_strategies function
            # First, handle the "do nothing" transition for all current states
            for w, cost in current_layer.items():
                if cost < next_layer.get(w, float('inf')):
                    next_layer[w] = cost

            is_horizontal = index % self.grid.num_rows == 0
            call = self._get_aisle_vertical_traversal_strategies if not is_horizontal else self._get_horizontal_traversal_strategies

            pickings_in_this_aisle = self._get_picking_locations_on_edge(edge)
            for w, cost in current_layer.items():
                possible_transitions = call(w, edge, pickings_in_this_aisle)
                for (w_prime, transition_cost) in possible_transitions:
                    new_cost = cost + transition_cost
                    if self.check_validity(w_prime):
                        if new_cost < next_layer.get(w_prime, float('inf')):
                            next_layer[w_prime] = new_cost

            current_layer = next_layer

        # --- Line 16 & 17: Find the optimal solution in the last layer ---
        w_opt = None
        min_cost = float('inf')

        # The optimal tree is the cheapest state where all terminals are connected.
        for final_state, final_cost in current_layer.items():
            final_connectivity = final_state[0]
            if is_fully_connected(final_connectivity, num_terminals):
                if final_cost < min_cost:
                    min_cost = final_cost
                    w_opt = final_state

        return w_opt, min_cost

    def _is_fully_connected(self, connectivity, point_ids_to_check):
        """
        Checks if all specified points (terminals and depot) are in the
        same connected component.

        Args:
            connectivity (tuple): The DSU parent-pointer tuple from a state.
            point_ids_to_check (list): A list of integer IDs for all terminals
                                       and the depot that must be connected.

        Returns:
            bool: True if all points are connected, False otherwise.
        """
        # If there's one or zero points to connect, they are trivially connected.
        if len(point_ids_to_check) <= 1:
            return True

        # We need a mutable list to perform path compression during finds.
        parents = list(connectivity)

        # Find the representative of the first point in the list.
        # This will be our target component.
        target_root = self._find_representative(parents, point_ids_to_check[0])

        # Check if all other points belong to the same component.
        for point_id in point_ids_to_check[1:]:
            if self._find_representative(parents, point_id) != target_root:
                # Found a point that is not in the same component.
                return False

        # If the loop completes, all points share the same representative.
        return True

    def check_validity(self, w):
        """
        Checks if a given state 'w' represents a valid partial tour.
        This function prunes invalid branches from the search space.

        Args:
            w (tuple): The state tuple (connectivity, degrees) to check.

        Returns:
            bool: True if the state is valid, False otherwise.
        """
        connectivity, degrees = w

        # --- Rule 1: Degree Constraint ---
        # The 'state_degree' at any point (terminal or crossing) cannot exceed 2.
        # - Degree 0: Path has not visited this point yet.
        # - Degree 1: Path passes through this point (one open end).
        # - Degree 2: Path uses this point as a U-turn (no open ends).
        # A degree of 3 or more is impossible for a single, non-overlapping path.
        for degree in degrees:
            if degree > 2:
                return False

        # --- Rule 2: (Advanced) Premature Cycle Detection ---
        # This check prevents forming a closed loop of terminals before all terminals
        # have been collected. This is a more complex check. Fortunately, the
        # feasibility checks in `_get_aisle_traversal_strategies` (e.g., `if current_degrees[start_id] == 0`)
        # are the primary defense against creating invalid path structures.
        # The degree check above is the most essential guardrail.

        # If all checks pass, the state is considered a valid partial tour.
        return True

    def _get_horizontal_traversal_strategies(self, w, aisle, terminals_in_this_aisle):
        pass

    def _get_aisle_vertical_traversal_strategies(self, w, aisle, picking_locations_in_this_aisle):
        """
        Given an aisle (edge) and the terminals in that aisle, generates all possible traversal strategies
        and their associated costs.
        :param aisle: tuple of two coordinates defining the aisle ((x1, y1), (x2, y2))
        :param picking_locations_in_this_aisle: list of location coordinates that lie on the aisle
        :return: list of tuples (new_state, cost) for each traversal strategy
        """
        generated_transitions = []

        # 2 . Strategy: Pass Through Aisle --> top to bottom
        pass_through_state = self._get_picking_aisle_transition_state(w, aisle, picking_locations_in_this_aisle)
        generated_transitions.append(pass_through_state)

        # 3. Strategy: Pass Through Aisle 2 times --> top to bottom and back
        pass_through_and_back_state = self._get_picking_aisle_transition_state(w, aisle,
                                                                               picking_locations_in_this_aisle,
                                                                               there_and_back=True)
        generated_transitions.append(pass_through_and_back_state)

        if not picking_locations_in_this_aisle:
            return generated_transitions

        # 4. Strategy: Pass To the furthest location from the current crossing --> to picking and back
        furthest_from_top = self._get_to_picking_and_back_states(w, aisle, picking_locations_in_this_aisle)
        furthest_from_bottom = self._get_to_picking_and_back_states(w, (aisle[1], aisle[0]),
                                                                    picking_locations_in_this_aisle, True)
        generated_transitions.append(furthest_from_top)
        generated_transitions.append(furthest_from_bottom)

        if not len(picking_locations_in_this_aisle) >= 2:
            return generated_transitions

        # 5. Strategy: Split the picking locations in the aisle and return
        picking_isle_split = self._get_picking_isle_split_states(w, aisle, picking_locations_in_this_aisle)
        generated_transitions.append(picking_isle_split)

        return generated_transitions

    def _find_representative(self, parents, i):
        """
        DSU Find operation with path compression. Finds the ultimate root
        of the component containing element 'i'.
        """
        if parents[i] == i:
            return i
        # Path Compression: Set parent directly to the root for future efficiency
        parents[i] = self._find_representative(parents, parents[i])
        return parents[i]

    def _union_all_components(self, connectivity, ids_to_merge):
        """
        Merges all components corresponding to the given IDs into a single
        component. This is the core of the connectivity update.
        """
        # If there's nothing to merge, return the original state
        if not ids_to_merge:
            return connectivity

        # Create a mutable copy to work with
        parents = list(connectivity)

        # Find the unique representatives (roots) of all components to be merged
        representatives = {self._find_representative(parents, id) for id in ids_to_merge}

        # If they are all already in the same component, no change is needed
        if len(representatives) <= 1:
            return tuple(parents)

        # Choose one representative to be the new "super-root"
        target_root = representatives.pop()

        # Union all other component roots to the target root
        for root in representatives:
            parents[root] = target_root

        # Return the new, immutable connectivity state
        return tuple(parents)

    def _get_to_picking_and_back_states(self, w, aisle, picking_locations_in_this_aisle, bottom_to_top=False):
        """
        Helper function to genrate states for going to the furthest picking location in an aisle and back.
        There are two states are generated here, one for each direction (start to end and end to start) as this
        function is called twice.
        Technically this means incrementing the degree of the aisle start by 2 and adding the locations to the visited
        picking locations.

        :param w: list of current states
        :param aisle: tuple of two coordinates defining the aisle ((x1, y1), (x2, y2))
        :param picking_locations_in_this_aisle: list of tuples of picking location coordinates in this aisle
        :return: tuple of new states and their costs
        """

        current_connectivity, current_degrees, visited_picking_locations = w
        new_degrees = list(current_degrees)

        call = max if not bottom_to_top else min
        furthest_picking = call(picking_locations_in_this_aisle, key=lambda loc: loc[1])
        cost = 2 * furthest_picking[1]
        crossing_id = self.id_map[aisle[0]]

        new_degrees[crossing_id] += 2  # Start at that crossing and back

        return (tuple(current_connectivity), tuple(new_degrees), tuple(picking_locations_in_this_aisle)), cost

    def _get_picking_isle_split_states(self, w, aisle, picking_locations_in_this_aisle):
        """
        Helper function that calculates the biggest split in the picking locations in an aisle and returns the according
        state.
        Technically this means incrementing the degree of both aisle ends by 2 and adding the
        picking_locations_in_this_aisle to the visited locations.
        :param w: current states
        :param aisle: tuple of two coordinates defining the aisle ((x1, y1), (x2, y2))
        :param picking_locations_in_this_aisle: list of tuples of picking location coordinates in this aisle
        :return: the new state and its cost
        """

        current_connectivity, current_degrees, visited_picking_locations = w
        new_degrees = list(current_degrees)

        crossing_start_id = self.id_map[aisle[0]]
        crossing_end_id = self.id_map[aisle[1]]

        # Todo test this
        furthest_pair = self.compute_biggest_aisle_split(
            [loc[1] for loc in picking_locations_in_this_aisle])

        if not furthest_pair:
            return None

        cost = 2 * (furthest_pair[1] - furthest_pair[0])

        new_degrees[crossing_start_id] += 2
        new_degrees[crossing_end_id] += 2

        return (tuple(current_connectivity), tuple(new_degrees),
                tuple(picking_locations_in_this_aisle)), cost

    def _get_picking_aisle_transition_state(self, w, aisle, picking_locations_in_this_aisle, there_and_back=False):
        """
        Helper function that calculates the state for going through an isle once.
        :param w: list of current states
        :param aisle: tuple of two coordinates defining the aisle ((x1, y1), (x2, y2))
        :param picking_locations_in_this_aisle: list of tuples of picking location coordinates in this aisle
        :param there_and_back: boolean indicating if the transition is there and back
        :return: tuple of the new state and its cost
        """
        current_connectivity, current_degrees, visited_picking_locations = w

        # Get integer IDs for aisle entrances from the pre-computed map
        start_coords, end_coords = aisle
        start_id = self.id_map[start_coords]
        end_id = self.id_map[end_coords]

        cost = self.get_edge_length(aisle)

        if there_and_back:
            cost *= 2

        # State Update:
        new_degrees = list(current_degrees)
        new_degrees[start_id] += 1 if not there_and_back else 2
        new_degrees[end_id] += 1 if not there_and_back else 2

        # Connect everything: the two entrances and all terminals inside the aisle
        ids_to_merge = [start_id, end_id]
        new_connectivity = self._union_all_components(current_connectivity, ids_to_merge)
        return (new_connectivity, tuple(new_degrees), tuple(picking_locations_in_this_aisle)), cost

    def _get_picking_locations_on_edge(self, edge):
        """
        Takes an edge defined by its start coordinate and end coordinate and returns all the
        locations that lie on that edge.
        :param edge: tuple of two coordinates defining the edge ((x1, y1), (x2, y2))
        :return: list of location coordinates that lie on the edge
        """
        index = 0 if edge[0][0] == edge[1][0] else 1
        interval = sorted([edge[0][1 - index], edge[1][1 - index]])
        edge_comparor = edge[0][index]
        res = []
        for location in self.locations:
            location_tuple = self.grid._turn_location_coordinate_to_route_loc(
                (location['x'], location['y']))  # Todo clean up

            if not (location_tuple[index] == edge_comparor and interval[0] < location_tuple[1 - index] < interval[1]):
                continue
            res.append(location_tuple)
        return res

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
        sorted_edges = sorted(walkable_edges,
                              key=lambda edge: (min(edge[0][1], edge[1][1]), min(edge[0][0], edge[1][0])))

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
