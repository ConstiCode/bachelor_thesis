from routes.base import BaseRoute


class FixedParameter(BaseRoute):
    def __init__(self, grid, locations, start_pos):
        super().__init__(grid, locations, start_pos)
        self.id_map = self._create_id_map()
        self._rev_id_map = {v: k for k, v in self.id_map.items()}

    def _create_id_map(self):
        """
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

        for location in self.locations:
            location_coord = self.grid._turn_location_coordinate_to_route_loc(
                (location['x'], location['y']))  # Todo clean up
            points_of_interest.add(location_coord)

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

        num_points_of_interest = len(self.id_map)

        visited_locs = []

        # Each point starts as its own component
        initial_connectivity = tuple(range(num_points_of_interest))

        # Every point starts with a degree of 0
        initial_degrees = tuple([0] * num_points_of_interest)

        # This is the correct initial state 'w0'
        initial_state = (initial_connectivity, initial_degrees)
        current_layer = {initial_state: 0}

        # Iterate though all the edges of the warehouse in the order vertical then horizontal and left to right,
        # bottom to top
        all_walkable_edges = self.get_all_aisles_in_order()
        for edge in all_walkable_edges:
            next_layer = {}

            pickings_in_this_aisle = self._get_picking_locations_on_edge(edge)

            is_horizontal = edge[0][1] == edge[1][1]
            last_edge = edge == all_walkable_edges[len(all_walkable_edges) - 1]

            visited_locs += pickings_in_this_aisle

            for w, cost in current_layer.items():
                possible_transitions = self._get_aisle_traversal_strategies(w, cost, edge, pickings_in_this_aisle,
                                                                            is_horizontal)
                for (w_prime, transition_cost) in possible_transitions:
                    if self.check_validity(edge, w_prime, visited_locs, is_horizontal, last_edge):

                        if transition_cost < next_layer.get(w_prime, float('inf')):
                            next_layer[w_prime] = transition_cost

            current_layer = next_layer

        # --- Line 16 & 17: Find the optimal solution in the last layer ---
        w_opt = None
        min_cost = float('inf')

        # The optimal tree is the cheapest state where all terminals are connected.
        for final_state, final_cost in current_layer.items():
            final_connectivity = final_state[0]
            if self._is_fully_connected(final_connectivity, [self.id_map[loc] for loc in visited_locs]):
                if final_cost < min_cost:
                    min_cost = final_cost
                    w_opt = final_state

        res = w_opt, min_cost
        self.route_length = min_cost

        route = self._turn_states_into_route(res, visited_locs)

        return route

    def _turn_states_into_route(self, state_cost_tuple, visited_locs):
        """
        Converts the final state and cost into a route representation.

        Args:
            state_cost_tuple (tuple): A tuple containing the final state and its cost.

        Returns:
            list: A list representing the route.
        """
        state, cost = state_cost_tuple
        connections = state[0]

        # Get the representative int for the dummy location so we can trace all connections from there
        representation_int = connections[self.id_map[visited_locs[0]]]
        res = []
        overall_distortion = 0

        for i in range(len(connections)):
            if connections[i] != representation_int:
                continue

            current_loc = self._rev_id_map[i]

            # Calculate if there is a location existing below
            below_exists = self._rev_id_map.get(i + 1, None)

            # Calculate if there is a location existing to the right
            right_exists = None

            is_picking_location = current_loc in visited_locs
            if is_picking_location:
                overall_distortion += 1

            if not is_picking_location:
                index_jump = self.grid.num_rows * 2 + overall_distortion
                right_exists = self._rev_id_map.get(i + index_jump, None)

            if below_exists and connections[self.id_map[below_exists]] == representation_int:
                res += [current_loc, below_exists]

            if right_exists and connections[self.id_map[right_exists]] == representation_int:
                res += [current_loc, right_exists]

        return res

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

        # Quick check: If all point IDs are the same, they are trivially connected.
        # subtour_id = point_ids_to_check[0]
        # for point_id in point_ids_to_check[1:]:
        #    if subtour_id != point_id:
        #        return False

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

    def check_validity(self, current_edge, w, visited_locs, horizontal, last_edge):
        """
        Checks if a given state 'w' represents a valid partial tour.
        This function prunes invalid branches from the search space.

        Args:
            w (tuple): The state tuple (connectivity, degrees) to check.
            visited_locs (list): List of picking locations in the current aisle.
            horizontal (bool): Indicates if the current aisle is horizontal.
            current_edge: The tuple representing the current aisle being processed.
            last_edge: The tuple representing the last aisle being processed.

        Returns:
            bool: True if the state is valid, False otherwise.
        """
        connectivity, degrees = w
        if last_edge:
            if any(degree % 2 != 0 for degree in degrees):
                return False

        # 1: Location Constraint: All the locations in the current edge must be visited.
        location_ids = sorted([self.id_map[loc] for loc in visited_locs])
        for loc_id in location_ids:
            if degrees[loc_id] == 0:
                return False

        # 2: Degree Constraint: No vertex should have an odd degree
        if horizontal:
            current_frontier_crossing = current_edge[1][0] - 3, current_edge[1][1]
            current_frontier_crossing_id = self.id_map.get(current_frontier_crossing, False)
            if degrees[current_frontier_crossing_id] % 2 != 0:
                return False

        return True

    def _get_aisle_traversal_strategies(self, w, cost, aisle, picking_locations_in_this_aisle, horizontal=False):
        """
        Given an aisle (edge) and the terminals in that aisle, generates all possible traversal strategies
        and their associated costs when the aisle is vertical.
        :param aisle: tuple of two coordinates defining the aisle ((x1, y1), (x2, y2))
        :param picking_locations_in_this_aisle: list of location coordinates that lie on the aisle
        :return: list of tuples (new_state, cost) for each traversal strategy
        """
        generated_transitions = []

        # 1. Strategy: Do Nothing
        if not picking_locations_in_this_aisle:
            generated_transitions.append((w, cost))

        # 2 . Strategy: Pass Through Aisle --> top to bottom
        pass_through_state = self._get_picking_aisle_transition_state(w, cost, aisle, picking_locations_in_this_aisle)
        generated_transitions.append(pass_through_state)

        # 3. Strategy: Pass Through Aisle 2 times --> top to bottom and back
        pass_through_and_back_state = self._get_picking_aisle_transition_state(w, cost, aisle,
                                                                               picking_locations_in_this_aisle,
                                                                               there_and_back=True)
        generated_transitions.append(pass_through_and_back_state)

        # For the horizontal aisles, we only consider these two strategies
        if horizontal:
            return generated_transitions

        if not picking_locations_in_this_aisle:
            return generated_transitions

        # 4. Strategy: Pass To the furthest location from the current crossing --> to picking and back
        furthest_from_top = self._get_to_picking_and_back_states(w, cost, aisle, picking_locations_in_this_aisle)
        furthest_from_bottom = self._get_to_picking_and_back_states(w, cost, (aisle[1], aisle[0]),
                                                                    picking_locations_in_this_aisle, True)
        generated_transitions.append(furthest_from_top)
        generated_transitions.append(furthest_from_bottom)

        if not len(picking_locations_in_this_aisle) >= 2:
            return generated_transitions

        # 5. Strategy: Split the picking locations in the aisle and return
        picking_isle_split = self._get_picking_isle_split_states(w, cost, aisle, picking_locations_in_this_aisle)
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

    def _get_to_picking_and_back_states(self, w, cost, aisle, picking_locations_in_this_aisle, bottom_to_top=False):
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

        current_connectivity, current_degrees = w
        new_degrees = list(current_degrees)

        call = max if not bottom_to_top else min
        furthest_picking = call(picking_locations_in_this_aisle, key=lambda loc: loc[1])
        # Todo test the bottom top cost calculation
        extension_cost = (furthest_picking[1] - aisle[0][1]) * 2 if not bottom_to_top else 2 * (
                self.get_edge_length(aisle) - furthest_picking[1])
        cost += extension_cost
        location_ids = [self.id_map[loc] for loc in picking_locations_in_this_aisle]
        vertices_to_update = location_ids + [self.id_map[aisle[0]]]

        for vertex_id in vertices_to_update:
            new_degrees[vertex_id] += 2  # Start at that crossing to the location and back

        # Connect everything: the two entrances and all terminals inside the aisle
        new_connectivity = self._union_all_components(current_connectivity, vertices_to_update)

        return (new_connectivity, tuple(new_degrees)), cost

    def _get_picking_isle_split_states(self, w, cost, aisle, picking_locations_in_this_aisle):
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

        current_connectivity, current_degrees = w
        new_degrees = list(current_degrees)

        # Get integer IDs for aisle entrances from the pre-computed map
        location_ids = [self.id_map[loc] for loc in picking_locations_in_this_aisle]
        vertices_to_update = location_ids + [self.id_map[aisle[0]], self.id_map[aisle[1]]]

        furthest_pair = self.compute_biggest_aisle_split(
            [loc[1] for loc in picking_locations_in_this_aisle])

        if not furthest_pair:
            return None

        extension_cost = 14 - (2 * abs(furthest_pair[1] - furthest_pair[0]))
        cost += extension_cost

        for vertex_id in vertices_to_update:
            new_degrees[vertex_id] += 2

        return (current_connectivity, tuple(new_degrees)), cost

    def _get_picking_aisle_transition_state(self, w, cost, aisle, picking_locations_in_this_aisle,
                                            there_and_back=False):
        """
        Helper function that calculates the state for going through an isle once.
        :param w: list of current states
        :param aisle: tuple of two coordinates defining the aisle ((x1, y1), (x2, y2))
        :param picking_locations_in_this_aisle: list of tuples of picking location coordinates in this aisle
        :param there_and_back: boolean indicating if the transition is there and back
        :return: tuple of the new state and its cost
        """
        current_connectivity, current_degrees = w

        # Get integer IDs for aisle entrances from the pre-computed map
        start_coords, end_coords = aisle
        start_id = self.id_map[start_coords]
        end_id = self.id_map[end_coords]
        location_ids = [self.id_map[loc] for loc in picking_locations_in_this_aisle]

        vertices_in_aisle = [start_id, end_id]

        extension_cost = self.get_edge_length(aisle)

        if there_and_back:
            extension_cost *= 2

        cost += extension_cost

        # State Update:
        new_degrees = list(current_degrees)

        # Location degrees need an update of 2 as they have 2 incident edges
        for location in location_ids:
            new_degrees[location] += 2 if not there_and_back else 4

        for vertex_id in vertices_in_aisle:
            new_degrees[vertex_id] += 1 if not there_and_back else 2

        vertices_in_aisle += location_ids

        # Connect everything: the two entrances and all terminals inside the aisle
        new_connectivity = self._union_all_components(current_connectivity, vertices_in_aisle)

        return (new_connectivity, tuple(new_degrees)), cost

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

    def get_edge_length(self, edge):
        """Returns the length of an edge. Where the edge length is denoted as the Manhattan distance between its two endpoints."""
        x1, y1 = edge[0]
        x2, y2 = edge[1]
        return abs(x1 - x2) + abs(y1 - y2)

    def get_all_aisles_in_order(self):
        """
        Generates all valid walkable aisle segments for a given warehouse layout.
        Returns a list of edges, where each edge is represented by its start and end coordinates and is sorted in an
        alternating manner from left to right, bottom to top.
        """
        num_isles = self.grid.num_isles
        num_rows = self.grid.num_rows
        all_edges = []

        # Iterate through the grid from left to right, aisle by aisle.
        for isle in range(num_isles + 1):
            for row in range(num_rows):
                start_node = (isle * 3, row * 7)
                end_node = (isle * 3, (row + 1) * 7)
                all_edges.append((start_node, end_node))

            if isle < num_isles:
                for row in range(num_rows + 1):
                    start_node = (isle * 3, row * 7)
                    end_node = ((isle + 1) * 3, row * 7)
                    all_edges.append((start_node, end_node))

        return all_edges
