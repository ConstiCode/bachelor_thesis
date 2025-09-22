from .base import BaseRoute
from algorithms import AStar
from utils.distances import total_manhattan_distance



class NearestNeighbor(BaseRoute):

    def compute_route(self):
        route = [self.start_pos]
        remaining_locations = self.locations.copy()

        while remaining_locations:
            # Find the nearest neighbor
            route.append(self._find_nearest_neighbor(route[-1], remaining_locations))
            remaining_locations.remove(route[-1])
        route.append(self.start_pos)

        self.route_length = total_manhattan_distance([(point['x'], point['y']) for point in route])
        a_star = AStar(self.grid.grid)
        full_route = a_star.calculate_a_star_route(route)

        # Todo here the actual route can be reduced as the start coordinate of the picking table is added twice: [{'x': 5, 'y': 22}, {'x': 5, 'y': 22}, {'location_number': 78, 'x': 7, 'y': 13}, {'location_number': 18, 'x': 4, 'y': 6}, {'location_number': 10, 'x': 2, 'y': 4}, {'x': 5, 'y': 22}]
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
