import networkx as nx
from itertools import combinations
from routes.base import BaseRoute
from warehouse.grid import WareHouseGrid


class ScfsPlus(BaseRoute):
    def __init__(self, grid: WareHouseGrid, locations: list[dict], start_pos: dict):
        super().__init__(grid, locations, start_pos)

        # 1. Die Mengen R (Required) und I (Intersections) definieren
        self.R_nodes = self._get_required_routing_nodes()
        self.I_nodes = self._get_intersection_nodes()

        # 2. Den Graphen D=(V,A) aufbauen
        self.steiner_graph = self._build_steiner_graph()

        # 3. Preprocessing: Graphen verkleinern
        self._apply_vertex_preprocessing()
        self._apply_arc_preprocessing()

    # Init Methods
    # ==================================================================================================================
    def _get_required_routing_nodes(self) -> set[tuple[int, int]]:
        """
        Sammelt alle R-Knoten (Produkte + Depot) als begehbare (x,y) Koordinaten.
        """
        required_nodes = set()

        # Reverse mapping: walkable coordinate -> original shelf coordinate
        self._walkable_to_shelf = {}

        # Depot hinzufügen
        depot_coord = (self.start_pos['x'], self.start_pos['y'])
        required_nodes.add(depot_coord)
        self._walkable_to_shelf[depot_coord] = depot_coord

        # Produkte aus der Pickliste in Routing-Koordinaten übersetzen
        for loc in self.locations:
            # Deine Methode gibt ein Dict zurück, wir brauchen (x,y)
            coord_tuple = loc['x'], loc['y']

            # Finde die begehbare Zelle neben dem Regal
            route_coord = self.grid._turn_location_coordinate_to_route_loc(coord_tuple)
            required_nodes.add(route_coord)
            self._walkable_to_shelf[route_coord] = coord_tuple

        return required_nodes

    def _get_intersection_nodes(self) -> set[tuple[int, int]]:
        """
        Berechnet alle I-Knoten (Kreuzungen zwischen vertikalen und horizontalen Gängen).
        """
        intersections = set()

        # Basierend auf deiner Grid-Dimensionierung in _create_grid:
        # Vertikale Gänge (x-Koordinaten)
        aisle_width = 1
        shelf_width = 2
        x_aisles = [i * (shelf_width + aisle_width) for i in range(self.grid.num_isles + 1)]

        # Horizontale Quergänge (y-Koordinaten)
        shelf_height = 6
        aisle_height = 1
        y_cross_aisles = [r * (shelf_height + aisle_height) for r in range(self.grid.num_rows + 1)]

        # Das kartesische Produkt aus x und y ergibt die Kreuzungen
        for x in x_aisles:
            for y in y_cross_aisles:
                # Depot ausschließen, falls es genau auf einer Kreuzung liegt (wird in R behandelt)
                if (x, y) != (self.start_pos['x'], self.start_pos['y']):
                    intersections.add((x, y))

        return intersections

    def _build_steiner_graph(self) -> nx.Graph:
        """
        Baut den Graphen auf. Kanten werden nur nach den Vorgaben des Papers gezogen.
        """
        G = nx.Graph()

        # Alle Knoten V = I ∪ R hinzufügen
        for node in self.R_nodes:
            G.add_node(node, type='required')
        for node in self.I_nodes:
            G.add_node(node, type='steiner')

        all_nodes = self.R_nodes.union(self.I_nodes)

        # 1. Horizontale Kanten (Kreuzungen verbinden)
        # Wir gruppieren nach y-Koordinate (Quergang) und sortieren nach x
        cross_aisle_y_coords = set(y for x, y in self.I_nodes)

        nodes_by_y = {}
        for x, y in all_nodes:
            # Nur Knoten gruppieren, deren y-Koordinate auf einem Quergang liegt
            if y in cross_aisle_y_coords:
                nodes_by_y.setdefault(y, []).append((x, y))

        for y, nodes in nodes_by_y.items():
            nodes.sort(key=lambda n: n[0])
            for i in range(len(nodes) - 1):
                # Verbinde horizontal benachbarte Knoten
                u, v = nodes[i], nodes[i + 1]
                dist = abs(u[0] - v[0])
                G.add_edge(u, v, weight=dist)

        # 2. Vertikale Kanten (Sub-Gassen verbinden)
        # Wir gruppieren nach x-Koordinate (vertikaler Gang) und sortieren nach y
        nodes_by_x = {}
        for x, y in all_nodes:
            nodes_by_x.setdefault(x, []).append((x, y))

        for x, nodes in nodes_by_x.items():
            nodes.sort(key=lambda n: n[1])
            for i in range(len(nodes) - 1):
                # Verbinde vertikal benachbarte Knoten (Kreuzung-Kreuzung, Kreuzung-Produkt, Produkt-Produkt)
                u, v = nodes[i], nodes[i + 1]

                # Wir stellen sicher, dass wir nicht versehentlich über Regalreihen hinweg verbinden,
                # falls ein vertikaler Gang unterbrochen sein sollte (in deinem Standard-Grid sind sie durchgehend).
                dist = abs(u[1] - v[1])
                G.add_edge(u, v, weight=dist)

        return G

    def _apply_vertex_preprocessing(self):
        """
        Reduziert die Produkte pro Teilgasse (Sub-Aisle) auf maximal vier,
        basierend auf der "Largest Gap"-Heuristik aus Ratliff und Rosenthal.
        """
        nodes_to_remove = set()

        # Hier speichern wir die Extrempunkte für Phase 3 (MILP Constraints)
        self.preprocessing_constraints = []

        # 1. Alle vertikalen x-Koordinaten finden, auf denen Gassen liegen
        x_aisles = set(x for x, y in self.I_nodes)

        for x in x_aisles:
            # Alle Kreuzungen (I) auf dieser x-Koordinate, sortiert nach y
            i_nodes_y = sorted([y for ix, y in self.I_nodes if ix == x])

            # Alle Produkte (R) auf dieser x-Koordinate
            r_nodes_y = sorted([y for rx, y in self.R_nodes if rx == x and (rx, y) not in self.I_nodes])

            # Iteriere über jede Sub-Gasse (zwischen zwei benachbarten Kreuzungen)
            for i in range(len(i_nodes_y) - 1):
                y_bottom = i_nodes_y[i]
                y_top = i_nodes_y[i + 1]

                # Finde alle Produkte, die exakt in dieser Sub-Gasse liegen
                products_in_sub = [y for y in r_nodes_y if y_bottom < y < y_top]

                # Wenn 2 oder weniger Produkte in der Gasse sind, gibt es nichts zu streichen
                if len(products_in_sub) <= 2:
                    continue

                # Berechne die Lücken zwischen ALLEN Knoten in dieser Sub-Gasse (inkl. Kreuzungen)
                all_sub_nodes = [y_bottom] + products_in_sub + [y_top]

                max_gap = -1
                gap_index = -1

                # Finde die größte Lücke (Largest Gap)
                for j in range(len(all_sub_nodes) - 1):
                    gap = all_sub_nodes[j + 1] - all_sub_nodes[j]
                    if gap > max_gap:
                        max_gap = gap
                        gap_index = j

                # Die Lücke befindet sich zwischen Index gap_index und gap_index + 1
                split_y_bottom = all_sub_nodes[gap_index]
                split_y_top = all_sub_nodes[gap_index + 1]

                # Teile die Produkte in Menge S (unterhalb) und Menge T (oberhalb)
                S = [y for y in products_in_sub if y <= split_y_bottom]
                T = [y for y in products_in_sub if y >= split_y_top]

                keep_y = set()

                # Behalte in S nur das unterste (b_S) und oberste (t_S) Produkt
                if S:
                    b_S, t_S = min(S), max(S)
                    keep_y.update([b_S, t_S])
                    # Speichere die Info für die Constraints: x_{t_S, b_S} + x_{b_S, t_S} >= 1
                    self.preprocessing_constraints.append(
                        {'type': 'S', 'nodes': [(x, b_S), (x, t_S)]}
                    )

                # Behalte in T nur das unterste (b_T) und oberste (t_T) Produkt
                if T:
                    b_T, t_T = min(T), max(T)
                    keep_y.update([b_T, t_T])
                    self.preprocessing_constraints.append(
                        {'type': 'T', 'nodes': [(x, b_T), (x, t_T)]}
                    )

                # Alle anderen Produkte markieren wir zum Löschen
                for y in products_in_sub:
                    if y not in keep_y:
                        nodes_to_remove.add((x, y))

        # 2. Graph bereinigen und Kanten neu verdrahten
        for node in nodes_to_remove:
            self.R_nodes.remove(node)

            # Da die Produkte in einer geraden Linie liegen, hat der Knoten exakt 2 Nachbarn im Graph
            neighbors = list(self.steiner_graph.neighbors(node))
            if len(neighbors) == 2:
                u, v = neighbors[0], neighbors[1]
                # Die neue Kante überbrückt den gelöschten Knoten (Manhattan-Distanz bleibt erhalten)
                dist = abs(u[1] - v[1]) + abs(u[0] - v[0])
                self.steiner_graph.add_edge(u, v, weight=dist)

            self.steiner_graph.remove_node(node)

    def _apply_arc_preprocessing(self):
        """
        Berechnet einen minimalen 1-Spanner mithilfe eines MILPs (Minimum Manhattan Network),
        um irrelevante Kanten aus dem Graphen zu entfernen.
        """
        import pulp

        # 1. Alle kürzesten Distanzen im aktuellen Graphen vorberechnen
        # Das garantiert, dass wir das exakte d(i,j) aus dem Paper verwenden
        shortest_paths = dict(nx.all_pairs_dijkstra_path_length(self.steiner_graph))

        # 2. Das MILP Modell aufsetzen
        prob = pulp.LpProblem("Minimum_1_Spanner", pulp.LpMinimize)

        # Entscheidungsvariablen: x_e = 1, wenn die ungerichtete Kante im 1-Spanner bleibt
        edges = list(self.steiner_graph.edges())
        edge_vars = {}
        for u, v in edges:
            # Kanten normieren, da der Graph ungerichtet ist
            e = tuple(sorted((u, v)))
            edge_vars[e] = pulp.LpVariable(f"x_{e[0]}_{e[1]}", cat='Binary')

        # Zielfunktion: Minimiere die Gesamtanzahl der genutzten Kanten im Spanner
        prob += pulp.lpSum(edge_vars.values())

        # 3. Kürzeste Pfade zwischen allen Paaren von REQUIRED Knoten (R) garantieren
        required_nodes = list(self.R_nodes)

        for i in range(len(required_nodes)):
            for j in range(i + 1, len(required_nodes)):
                s = required_nodes[i]
                t = required_nodes[j]
                target_dist = shortest_paths[s][t]

                # Finde alle Kanten, die auf einem kürzesten Pfad zwischen s und t liegen können.
                # Eine Kante (u,v) liegt auf einem kürzesten Pfad, wenn gilt:
                # Distanz(s,u) + Kantengewicht(u,v) + Distanz(v,t) == Gesamtdistanz(s,t)
                valid_directed_edges = []
                for u, v, data in self.steiner_graph.edges(data=True):
                    w = data['weight']
                    e_sorted = tuple(sorted((u, v)))

                    # Fluss-Richtung u -> v prüfen
                    if shortest_paths[s][u] + w + shortest_paths[v][t] == target_dist:
                        valid_directed_edges.append((u, v, e_sorted))
                    # Fluss-Richtung v -> u prüfen
                    elif shortest_paths[s][v] + w + shortest_paths[u][t] == target_dist:
                        valid_directed_edges.append((v, u, e_sorted))

                if not valid_directed_edges:
                    continue

                # Fluss-Variablen für dieses spezifische Paar (s,t) erstellen
                flow_vars = {}
                for u, v, e_sorted in valid_directed_edges:
                    flow_vars[(u, v)] = pulp.LpVariable(f"f_{s}_{t}_{u}_{v}", lowBound=0, cat='Continuous')
                    # Kapazitätsbedingung: Fluss darf nur existieren, wenn die Kante ausgewählt (x_e=1) ist
                    prob += flow_vars[(u, v)] <= edge_vars[e_sorted]

                # Fluss-Erhaltungsbedingungen für jeden Knoten in diesem Sub-Netzwerk
                involved_nodes = set()
                for u, v, _ in valid_directed_edges:
                    involved_nodes.add(u)
                    involved_nodes.add(v)

                for node in involved_nodes:
                    flow_in = pulp.lpSum([flow_vars[(u, v)] for u, v, _ in valid_directed_edges if v == node])
                    flow_out = pulp.lpSum([flow_vars[(u, v)] for u, v, _ in valid_directed_edges if u == node])

                    # 1 Einheit fließt aus s heraus, 1 Einheit fließt in t hinein, Rest ist Transit (0)
                    if node == s:
                        prob += flow_out - flow_in == 1
                    elif node == t:
                        prob += flow_in - flow_out == 1
                    else:
                        prob += flow_in - flow_out == 0

        # 4. Modell über den Standard-Solver lösen
        prob.solve(pulp.PULP_CBC_CMD(msg=0))

        # 5. Graph bereinigen: Alle Kanten, die der Solver verworfen hat (x_e = 0), entfernen
        edges_to_remove = []
        for e, var in edge_vars.items():
            if pulp.value(var) < 0.5:
                edges_to_remove.append(e)

        self.steiner_graph.remove_edges_from(edges_to_remove)

    # Main Methods
    def compute_route(self):
        """
        Berechnet die optimale Route durch das Lager mithilfe der SCFS+ Formulierung.
        """
        import pulp

        # 1. Gerichteten Graphen D=(V,A) erstellen (jede ungerichtete Kante wird zu zwei gerichteten)
        D = self.steiner_graph.to_directed()

        # Depot-Knoten identifizieren
        depot = (self.start_pos['x'], self.start_pos['y'])
        n_products = len(self.R_nodes) - 1  # Anzahl der zu pickenden Produkte

        # 2. MILP Modell aufsetzen
        prob = pulp.LpProblem("OrderPicking_SCFS_Plus", pulp.LpMinimize)

        # Variablen definieren
        x = {}  # x_ij: Wie oft wird Kante (i,j) genutzt? (Integer)
        y = {}  # y_ij: Wieviel Waren-Fluss fließt über (i,j)? (Continuous)

        for i, j, data in D.edges(data=True):
            # Gemäß Paper ist x_ij ein Integer (Kanten können mehrfach besucht werden)
            x[(i, j)] = pulp.LpVariable(f"x_{i[0]}_{i[1]}_{j[0]}_{j[1]}", lowBound=0, cat='Integer')
            y[(i, j)] = pulp.LpVariable(f"y_{i[0]}_{i[1]}_{j[0]}_{j[1]}", lowBound=0, cat='Continuous')

        # 3. Zielfunktion: Minimiere die Gesamtdistanz
        prob += pulp.lpSum(D[i][j]['weight'] * x[(i, j)] for i, j in D.edges())

        # 4. Nebenbedingungen (Constraints)
        for i in D.nodes():
            # Constraint (2): Jeder Required-Knoten muss mindestens einmal besucht werden
            if i in self.R_nodes:
                prob += pulp.lpSum(x[(i, j)] for j in D.successors(i)) >= 1

            # Constraint (3): Flusserhaltung für die Route (was reingeht, muss rausgehen)
            prob += pulp.lpSum(x[(i, j)] for j in D.successors(i)) == \
                    pulp.lpSum(x[(j, i)] for j in D.predecessors(i))

            # Constraints (4) & (5): Waren-Flusserhaltung
            flow_in = pulp.lpSum(y[(j, i)] for j in D.predecessors(i))
            flow_out = pulp.lpSum(y[(i, j)] for j in D.successors(i))

            if i == depot:
                # Am Depot startet der Picker mit n Einheiten
                prob += flow_out - flow_in == n_products
            elif i in self.R_nodes:
                # Bei jedem Produkt fällt der Fluss um genau 1
                prob += flow_in - flow_out == 1
            else:
                # Bei Kreuzungen (Steiner Nodes) bleibt der Fluss konstant
                prob += flow_in - flow_out == 0

        # Constraint (6/20): Big-M Verknüpfung von Fluss und Route
        # Der Einfachheit halber nutzen wir n_products als Big-M (Basis SCFS)
        for i, j in D.edges():
            prob += y[(i, j)] <= n_products * x[(i, j)]

        # 5. Preprocessing Constraints hinzufügen (aus Phase 2.1)
        for constraint in self.preprocessing_constraints:
            u, v = constraint['nodes']
            # Der Picker muss zwingend (u->v) oder (v->u) durchlaufen
            if (u, v) in x and (v, u) in x:
                prob += x[(u, v)] + x[(v, u)] >= 1

        # 6. Lösen des Modells
        print("Starte MILP Solver für finale Route...")
        prob.solve(pulp.PULP_CBC_CMD(msg=0))

        if pulp.LpStatus[prob.status] != 'Optimal':
            raise ValueError("Keine optimale Route gefunden!")

        # 7. Aktive Kanten extrahieren
        active_edges = []
        for i, j in D.edges():
            val = round(pulp.value(x[(i, j)]))
            for _ in range(val):  # Kante kann >1 mal genutzt werden
                active_edges.append((i, j))

        # Extract the visit order of picking locations from the Euler tour for unified route length
        # calculation. Map walkable coordinates back to shelf coordinates via _walkable_to_shelf.
        visit_sequence = self._extract_pick_visit_order(active_edges, depot)
        self.compute_and_set_route_length(visit_sequence)
        print(f"Route gefunden! Gesamtdistanz: {self.route_length}")

        # ==========================================================
        # 8. Euler-Tour berechnen und für das Frontend formatieren
        # ==========================================================

        # Wir bauen einen gerichteten MultiGraph aus unseren Lösungs-Kanten
        tour_graph = nx.MultiDiGraph()
        tour_graph.add_edges_from(active_edges)

        depot = (self.start_pos['x'], self.start_pos['y'])

        try:
            # networkx berechnet uns die perfekte durchgehende Route ab dem Depot
            euler_circuit = list(nx.eulerian_circuit(tour_graph, source=depot))
        except nx.NetworkXError as e:
            print("Fehler bei der Euler-Tour:", e)
            euler_circuit = active_edges  # Fallback

        # 9. Umwandlung in eine durchgehende Standard-Route (Array von Arrays)
        frontend_route = []
        if euler_circuit:
            # Wir gehen die Kanten der Euler-Tour ab und speichern jeweils den Startpunkt als Liste [x, y]
            for u, v in euler_circuit:
                frontend_route.append([u[0], u[1]])

            # Am Ende fügen wir noch den allerletzten Zielpunkt an, um den Kreis zum Depot zu schließen
            last_v = euler_circuit[-1][1]
            frontend_route.append([last_v[0], last_v[1]])

        # WICHTIG: Nur das flache Array zurückgeben!
        # BaseRoute / der API-Handler kümmert sich um den Rest.
        return frontend_route

    def _extract_pick_visit_order(self, active_edges, depot):
        """
        Extracts the ordered sequence of picking location visits from the MILP solution edges.
        Builds a temporary Euler circuit and collects the R_nodes in visit order,
        then maps them back to their original shelf coordinates for use with calculate_warehouse_distance.
        """
        tour_graph = nx.MultiDiGraph()
        tour_graph.add_edges_from(active_edges)

        try:
            euler_circuit = list(nx.eulerian_circuit(tour_graph, source=depot))
        except nx.NetworkXError:
            euler_circuit = active_edges

        visited = set()
        visit_sequence = []

        for u, v in euler_circuit:
            if u in self.R_nodes and u not in visited:
                visited.add(u)
                visit_sequence.append(self._walkable_to_shelf[u])

        # Close the tour by returning to the depot
        visit_sequence.append(self._walkable_to_shelf[depot])

        return visit_sequence

        return visit_sequence
