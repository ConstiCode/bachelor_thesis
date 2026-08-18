from .base import BaseRoute
from algorithms import ClosedFormRoute


class NearestNeighbor(BaseRoute):

    def compute_route(self):
        route = [self.start_pos]
        remaining_locations = self.locations.copy()

        while remaining_locations:
            # Find the nearest neighbor
            route.append(self._find_nearest_neighbor(route[-1], remaining_locations))
            remaining_locations.remove(route[-1])
        route.append({'x': 0, 'y': 0})

        self.compute_and_set_route_length([(d['x'], d['y']) for d in route])

        # Ergebnis des Verfahrens: Besuchsreihenfolge plus route_length. Die
        # Expansion in Gitterzellen erfolgt in expand_route und liegt damit
        # ausserhalb der Messung.
        return route

    def expand_route(self, tour):
        # Pfadexpansion in geschlossener Form (siehe ASTAR_ERSATZ.md). Nimmt die
        # WareHouseGrid selbst, nicht das rohe Gitter, weil sie die
        # Fallunterscheidung von calculate_warehouse_distance mitbenutzt.
        router = ClosedFormRoute(self.grid)
        return router.calculate_closed_form_route(tour)

    def _find_nearest_neighbor(self, current_location, locations):
        nearest_location = None
        min_distance = float('inf')
        start_tuple = (current_location.get('x'), current_location.get('y'))
        for location in locations:
            end_tuple = (location.get('x'), location.get('y'))
            distance = self.grid.calculate_warehouse_distance(start_tuple, end_tuple)
            if distance < min_distance:
                min_distance = distance
                nearest_location = location

        return nearest_location
