from routes.base import BaseRoute
import math
import networkx as nx


class FixedParameter(BaseRoute):
    """
    Frontier-based Dynamic Programming solver for the warehouse picking problem.

    Based on the sweep-line approach from Cambazard & Catusse / Pansart et al.
    The state tracks only the h frontier crossings (one per row on the current column),
    using parities (0=unvisited, 1=odd degree, 2=even degree) and normalized
    component labels (-1=disconnected, 0,1,2,...=connected component).
    """

    def __init__(self, grid, locations, start_pos):
        locations.append(start_pos)
        super().__init__(grid, locations, start_pos)
        self.all_walkable_edges = self.get_all_relevant_aisles_in_order()
        self.locations_on_edge = {
            edge: self._get_picking_locations_on_edge(edge)
            for edge in self.all_walkable_edges
        }
        if self.all_walkable_edges:
            max_y = max(max(e[0][1], e[1][1]) for e in self.all_walkable_edges)
            self.h = max_y // 7 + 1
        else:
            self.h = 1

        # Depot route_loc is used during route reconstruction to add the
        # walk between the actual depot and crossing (0,0).
        self._depot_route_loc = self.grid._turn_location_coordinate_to_route_loc(
            (start_pos['x'], start_pos['y']))

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    @staticmethod
    def _update_parity(old, delta):
        """Update parity after adding delta edges.
        0=unvisited, 1=odd degree, 2=even degree (and visited)."""
        if delta % 2 == 0:
            # Even delta: 0->2, 1->1, 2->2
            return 2 if old != 1 else 1
        else:
            # Odd delta: 0->1, 1->2, 2->1
            return 1 if old != 1 else 2

    @staticmethod
    def _normalize_components(components):
        """Normalize component labels so first seen -> 0, second -> 1, etc.
        -1 stays -1 (disconnected)."""
        mapping = {}
        next_label = 0
        result = []
        for c in components:
            if c == -1:
                result.append(-1)
            elif c in mapping:
                result.append(mapping[c])
            else:
                mapping[c] = next_label
                result.append(next_label)
                next_label += 1
        return tuple(result)

    @staticmethod
    def _merge_components(components, idx_a, idx_b):
        """Merge the components of two frontier indices."""
        comp_a = components[idx_a]
        comp_b = components[idx_b]
        if comp_a == -1 and comp_b == -1:
            new_label = max((c for c in components if c != -1), default=-1) + 1
            result = list(components)
            result[idx_a] = new_label
            result[idx_b] = new_label
            return tuple(result)
        elif comp_a == -1:
            result = list(components)
            result[idx_a] = comp_b
            return tuple(result)
        elif comp_b == -1:
            result = list(components)
            result[idx_b] = comp_a
            return tuple(result)
        else:
            target = min(comp_a, comp_b)
            source = max(comp_a, comp_b)
            return tuple(target if c == source else c for c in components)

    @staticmethod
    def _ensure_component(components, idx):
        """Ensure frontier slot idx has a component label (not -1)."""
        if components[idx] != -1:
            return components
        result = list(components)
        result[idx] = max((c for c in components if c != -1), default=-1) + 1
        return tuple(result)

    # ------------------------------------------------------------------
    # Transition methods
    # ------------------------------------------------------------------

    def _vertical_transitions(self, state, cost, edge, picking_locs):
        """Generate all valid transitions for a vertical sub-aisle edge.
        Returns triples (new_state, new_cost, strategy_id).
        Strategy IDs: 1=skip, 2=pass_once, 3=pass_twice,
                      4=enter_bottom, 5=enter_top, 6=split
        """
        parities, components = state
        row_bottom = edge[0][1] // 7
        row_top = edge[1][1] // 7
        edge_length = self.get_edge_length(edge)
        results = []

        # Strategy 1: Do nothing (only if no products in this sub-aisle)
        if not picking_locs:
            results.append((state, cost, 1))

        # Strategy 2: Pass through once (+1 bottom, +1 top, merge)
        new_par = list(parities)
        new_par[row_bottom] = self._update_parity(parities[row_bottom], 1)
        new_par[row_top] = self._update_parity(parities[row_top], 1)
        new_comp = self._merge_components(components, row_bottom, row_top)
        results.append(((tuple(new_par), self._normalize_components(new_comp)),
                        cost + edge_length, 2))

        # Strategy 3: Pass through twice (+2 bottom, +2 top, merge)
        new_par = list(parities)
        new_par[row_bottom] = self._update_parity(parities[row_bottom], 2)
        new_par[row_top] = self._update_parity(parities[row_top], 2)
        new_comp = self._merge_components(components, row_bottom, row_top)
        results.append(((tuple(new_par), self._normalize_components(new_comp)),
                        cost + 2 * edge_length, 3))

        if picking_locs:
            # Strategy 4: Enter from bottom, pick all, return to bottom
            furthest_from_bottom = max(picking_locs, key=lambda loc: loc[1])
            dist_bottom = furthest_from_bottom[1] - edge[0][1]
            new_par = list(parities)
            new_par[row_bottom] = self._update_parity(parities[row_bottom], 2)
            new_comp = self._ensure_component(components, row_bottom)
            results.append(((tuple(new_par), self._normalize_components(new_comp)),
                            cost + 2 * dist_bottom, 4))

            # Strategy 5: Enter from top, pick all, return to top
            furthest_from_top = min(picking_locs, key=lambda loc: loc[1])
            dist_top = edge[1][1] - furthest_from_top[1]
            new_par = list(parities)
            new_par[row_top] = self._update_parity(parities[row_top], 2)
            new_comp = self._ensure_component(components, row_top)
            results.append(((tuple(new_par), self._normalize_components(new_comp)),
                            cost + 2 * dist_top, 5))

            # Strategy 6: Split at largest gap (+2 both, NO merge)
            if len(picking_locs) >= 2:
                gap_pair = self.compute_biggest_aisle_split(
                    [loc[1] for loc in picking_locs])
                if gap_pair[0] is not None:
                    largest_gap = abs(gap_pair[1] - gap_pair[0])
                    split_cost = 2 * edge_length - 2 * largest_gap
                    new_par = list(parities)
                    new_par[row_bottom] = self._update_parity(
                        parities[row_bottom], 2)
                    new_par[row_top] = self._update_parity(
                        parities[row_top], 2)
                    new_comp = list(components)
                    max_label = max(
                        (c for c in components if c != -1), default=-1)
                    if new_comp[row_bottom] == -1:
                        max_label += 1
                        new_comp[row_bottom] = max_label
                    if new_comp[row_top] == -1:
                        max_label += 1
                        new_comp[row_top] = max_label
                    results.append((
                        (tuple(new_par),
                         self._normalize_components(tuple(new_comp))),
                        cost + split_cost, 6))

        return results

    def _horizontal_transitions(self, state, cost, edge):
        """Generate all valid transitions for a horizontal edge.
        Returns triples (new_state, new_cost, strategy_id).
        Strategy IDs: 1=disconnect, 2=single_edge, 3=double_edge

        Transitions one frontier slot (row) from the current column to the next.
        The old crossing is validated and replaced by the new crossing's state.
        """
        parities, components = state
        row = edge[0][1] // 7
        is_depot = (edge[0] == (0, 0))
        old_parity = parities[row]
        results = []

        # Option 1: No edge (disconnect this crossing from next column)
        if old_parity == 0 or old_parity == 2:
            if not is_depot or old_parity == 2:
                can_disconnect = True
                if old_parity > 0 and components[row] != -1:
                    comp = components[row]
                    if not any(components[i] == comp
                               for i in range(self.h) if i != row):
                        can_disconnect = False
                if can_disconnect:
                    new_par = list(parities)
                    new_comp = list(components)
                    new_par[row] = 0
                    new_comp[row] = -1
                    results.append((
                        (tuple(new_par),
                         self._normalize_components(tuple(new_comp))),
                        cost, 1))

        # Option 2: Single edge (cost +3)
        if old_parity == 1:
            new_par = list(parities)
            new_par[row] = 1
            results.append((
                (tuple(new_par),
                 self._normalize_components(tuple(components))),
                cost + 3, 2))

        # Option 3: Double edge (cost +6)
        if old_parity == 0 or old_parity == 2:
            new_par = list(parities)
            new_par[row] = 2
            new_comp = list(components)
            if components[row] == -1:
                max_label = max(
                    (c for c in components if c != -1), default=-1)
                new_comp[row] = max_label + 1
            results.append((
                (tuple(new_par),
                 self._normalize_components(tuple(new_comp))),
                cost + 6, 3))

        return results

    # ------------------------------------------------------------------
    # Main DP
    # ------------------------------------------------------------------

    def compute_route(self):
        initial_state = (tuple([0] * self.h), tuple([-1] * self.h))
        current_layer = {initial_state: 0}
        predecessors = []  # predecessors[edge_idx][new_state] = (prev_state, strategy_id)

        for edge_idx, edge in enumerate(self.all_walkable_edges):
            next_layer = {}
            edge_preds = {}
            is_horizontal = edge[0][1] == edge[1][1]

            if not is_horizontal:
                picking_locs = self.locations_on_edge[edge]
                for state, cost in current_layer.items():
                    for new_state, new_cost, strat_id in \
                            self._vertical_transitions(
                                state, cost, edge, picking_locs):
                        if new_cost < next_layer.get(new_state, float('inf')):
                            next_layer[new_state] = new_cost
                            edge_preds[new_state] = (state, strat_id)
            else:
                for state, cost in current_layer.items():
                    for new_state, new_cost, strat_id in \
                            self._horizontal_transitions(
                                state, cost, edge):
                        if new_cost < next_layer.get(new_state, float('inf')):
                            next_layer[new_state] = new_cost
                            edge_preds[new_state] = (state, strat_id)

            current_layer = next_layer
            predecessors.append(edge_preds)

        # End condition: all parities 0 or 2, at most one connected component
        min_cost = float('inf')
        best_final_state = None
        for state, cost in current_layer.items():
            parities, components = state
            if any(p == 1 for p in parities):
                continue
            active = {c for p, c in zip(parities, components) if p > 0}
            if len(active) > 1:
                continue
            if cost < min_cost:
                min_cost = cost
                best_final_state = state

        if best_final_state is None:
            self.route_length = float('inf')
            return []

        # Reconstruct the route
        strategy_per_edge = self._backtrack(best_final_state, predecessors)
        tour_graph = self._build_tour_multigraph(strategy_per_edge)

        # Handle degenerate case: no edges in tour (single location at depot)
        if tour_graph.number_of_edges() == 0:
            depot_rl = self._depot_route_loc
            self.route_length = 0
            return [[depot_rl[0], depot_rl[1]]]

        circuit = self._find_euler_circuit(tour_graph)
        waypoints = self._circuit_to_waypoints(tour_graph, circuit)

        # Compute route_length from waypoint Manhattan distances
        self.route_length = sum(
            abs(waypoints[i][0] - waypoints[i + 1][0])
            + abs(waypoints[i][1] - waypoints[i + 1][1])
            for i in range(len(waypoints) - 1))

        return [[p[0], p[1]] for p in waypoints]

    # ------------------------------------------------------------------
    # Route reconstruction methods
    # ------------------------------------------------------------------

    def _backtrack(self, best_final_state, predecessors):
        """Walk backwards through predecessors to recover the strategy per edge."""
        strategies = []
        state = best_final_state
        for edge_idx in range(len(predecessors) - 1, -1, -1):
            prev_state, strategy_id = predecessors[edge_idx][state]
            strategies.append((self.all_walkable_edges[edge_idx], strategy_id))
            state = prev_state
        strategies.reverse()
        return strategies

    def _build_tour_multigraph(self, strategy_per_edge):
        """Build a nx.MultiGraph from the chosen strategy per edge."""
        G = nx.MultiGraph()
        for edge, strategy_id in strategy_per_edge:
            is_horizontal = edge[0][1] == edge[1][1]

            if is_horizontal:
                if strategy_id == 1:    # disconnect
                    pass
                elif strategy_id == 2:  # single edge
                    G.add_edge(edge[0], edge[1])
                elif strategy_id == 3:  # double edge
                    G.add_edge(edge[0], edge[1])
                    G.add_edge(edge[0], edge[1])
            else:  # vertical
                if strategy_id == 1:    # skip
                    pass
                elif strategy_id == 2:  # pass_once
                    G.add_edge(edge[0], edge[1])
                elif strategy_id == 3:  # pass_twice
                    G.add_edge(edge[0], edge[1])
                    G.add_edge(edge[0], edge[1])
                elif strategy_id == 4:  # enter_bottom
                    picking_locs = self.locations_on_edge[edge]
                    turnaround_y = max(loc[1] for loc in picking_locs)
                    G.add_edge(edge[0], edge[0],
                               aisle_x=edge[0][0],
                               turnaround_y=turnaround_y)
                elif strategy_id == 5:  # enter_top
                    picking_locs = self.locations_on_edge[edge]
                    turnaround_y = min(loc[1] for loc in picking_locs)
                    G.add_edge(edge[1], edge[1],
                               aisle_x=edge[1][0],
                               turnaround_y=turnaround_y)
                elif strategy_id == 6:  # split
                    picking_locs = self.locations_on_edge[edge]
                    gap_pair = self.compute_biggest_aisle_split(
                        [loc[1] for loc in picking_locs])
                    G.add_edge(edge[0], edge[0],
                               aisle_x=edge[0][0],
                               turnaround_y=gap_pair[0])
                    G.add_edge(edge[1], edge[1],
                               aisle_x=edge[1][0],
                               turnaround_y=gap_pair[1])
        return G

    def _find_euler_circuit(self, G):
        """Find an Eulerian circuit starting from (0,0)."""
        source = (0, 0)
        if source not in G:
            source = next(iter(G.nodes()))
        return list(nx.eulerian_circuit(G, source=source, keys=True))

    def _circuit_to_waypoints(self, G, circuit):
        """Convert Euler circuit to a waypoint list starting/ending at depot.

        For regular edges: append the endpoint node.
        For self-loops: append the turnaround point, then back to the node.
        The first and last waypoints are replaced with the depot's route_loc,
        since the picker starts/ends there, not at crossing (0,0).
        """
        depot_rl = self._depot_route_loc

        # Build raw waypoint path starting at (0,0)
        raw = [(0, 0)]
        for u, v, key in circuit:
            if u == v:  # self-loop: detour to turnaround point and back
                edge_data = G.edges[u, v, key]
                turnaround = (u[0], edge_data['turnaround_y'])
                raw.append(turnaround)
                raw.append(u)
            else:
                raw.append(v)
        # raw[0] == raw[-1] == (0,0)

        # Replace start/end (0,0) with depot_rl where axis-aligned,
        # otherwise insert depot_rl to keep all segments on aisles.
        if len(raw) > 1 and (depot_rl[0] == raw[1][0] or depot_rl[1] == raw[1][1]):
            raw[0] = depot_rl
        else:
            raw.insert(0, depot_rl)

        if len(raw) > 1 and (depot_rl[0] == raw[-2][0] or depot_rl[1] == raw[-2][1]):
            raw[-1] = depot_rl
        else:
            raw.append(depot_rl)

        # Expand waypoints to step-by-step grid path so the frontend
        # can draw the route along aisles (not diagonal lines).
        return self._expand_waypoints(raw)

    @staticmethod
    def _expand_waypoints(waypoints):
        """Expand waypoints into a step-by-step grid path.

        Consecutive waypoints always share the same x or y coordinate
        (they lie on aisles or corridors), so we enumerate each grid cell
        between them. This produces a path identical in format to what
        Christofides and NearestNeighbor return.
        """
        if len(waypoints) < 2:
            return list(waypoints)

        path = [waypoints[0]]
        for i in range(1, len(waypoints)):
            ax, ay = waypoints[i - 1]
            bx, by = waypoints[i]
            if ax == bx:  # vertical segment
                step = 1 if by > ay else -1
                for y in range(ay + step, by + step, step):
                    path.append((ax, y))
            else:  # horizontal segment
                step = 1 if bx > ax else -1
                for x in range(ax + step, bx + step, step):
                    path.append((x, ay))
        return path

    # ------------------------------------------------------------------
    # Kept helper methods from original implementation
    # ------------------------------------------------------------------

    def _get_picking_locations_on_edge(self, edge):
        """Returns all picking location coordinates that lie on the given edge."""
        index = 0 if edge[0][0] == edge[1][0] else 1
        interval = sorted([edge[0][1 - index], edge[1][1 - index]])
        edge_comparor = edge[0][index]
        res = []
        for location in self.locations:
            location_tuple = self.grid._turn_location_coordinate_to_route_loc(
                (location['x'], location['y']))
            if not (location_tuple[index] == edge_comparor
                    and interval[0] < location_tuple[1 - index] < interval[1]):
                continue
            res.append(location_tuple)
        return res

    def compute_biggest_aisle_split(self, y_values):
        """Finds the largest gap between consecutive y-values."""
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
        """Manhattan distance between the two endpoints of an edge."""
        x1, y1 = edge[0]
        x2, y2 = edge[1]
        return abs(x1 - x2) + abs(y1 - y2)

    def get_all_relevant_aisles_in_order(self):
        """Generates all walkable aisle segments ordered left-to-right,
        vertical edges before horizontal edges per column."""
        # Use route_loc coordinates to determine bounds, not raw shelf coords.
        # This avoids generating extra columns/rows beyond where products are.
        max_route_x = 0
        max_route_y = 0
        for loc in self.locations:
            rl = self.grid._turn_location_coordinate_to_route_loc(
                (loc['x'], loc['y']))
            max_route_x = max(max_route_x, rl[0])
            max_route_y = max(max_route_y, rl[1])

        max_shelf_rows_to_compute_y = math.ceil(max_route_y / 7) if max_route_y > 0 else 0
        max_shelf_columns_to_compute_x = max_route_x // 3

        all_edges = []

        for isle in range(max_shelf_columns_to_compute_x + 1):
            for row in range(max_shelf_rows_to_compute_y):
                start_node = (isle * 3, row * 7)
                end_node = (isle * 3, (row + 1) * 7)
                all_edges.append((start_node, end_node))

            if isle < max_shelf_columns_to_compute_x:
                for row in range(max_shelf_rows_to_compute_y + 1):
                    start_node = (isle * 3, row * 7)
                    end_node = ((isle + 1) * 3, row * 7)
                    all_edges.append((start_node, end_node))

        return all_edges
