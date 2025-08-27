from .base import BaseRoute
from algorithms import AStar
from utils.distances import manhattan_distance

class NearestNeighbor(BaseRoute):

    def compute_route(self):
        route = [self.start_pos]
        remaining_locations = self.locations.copy()

        while remaining_locations:
            # Find the nearest neighbor
            route.append(self._nearest_neighbor(route[-1], remaining_locations))
            remaining_locations.remove(route[-1])

        route.append(self.start_pos) # Return to start position

        a_star = AStar(self.grid.grid)
        full_route = a_star.calculate_a_star_route(route)

        # Todo here the actual route can be reduced as the start coordinate of the picking table is added twice: [{'x': 5, 'y': 22}, {'x': 5, 'y': 22}, {'location_number': 78, 'x': 7, 'y': 13}, {'location_number': 18, 'x': 4, 'y': 6}, {'location_number': 10, 'x': 2, 'y': 4}, {'x': 5, 'y': 22}]
        return full_route

    def _nearest_neighbor(self, start_location: dict, locations: list[dict]) -> dict:
        # Todo check here if i can improve performance by experimenting with manhattan distance and a* search
        sx, sy = start_location['x'], start_location['y']
        return min(
            locations,
            key=lambda loc: manhattan_distance((sx, sy), (loc['x'], loc['y']))
        )