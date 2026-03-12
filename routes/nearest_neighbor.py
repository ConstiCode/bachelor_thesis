from .base import BaseRoute
from algorithms import AStar


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
        a_star = AStar(self.grid.grid)
        full_route = a_star.calculate_a_star_route(route)

        return full_route

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
