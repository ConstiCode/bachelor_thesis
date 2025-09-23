from abc import ABC, abstractmethod

class BaseRoute(ABC):
    def __init__(self, grid, locations, start_pos):
        self.grid = grid
        self.locations = locations
        self.start_pos = start_pos
        self.route_length = 0

    @abstractmethod
    def compute_route(self):
        """
        Compute a route through the grid from start to end. If not implemented in a subclass abc will raise an error.
        """
        pass

    def compute_route_length(self, route_sequence: list[tuple[int, int]]) -> int:
        """
        Computes the route length of the initial route. Where the route is the sequence of locations to visit.
        :return: int
        """
        return sum(self.grid.calculate_warehouse_distance(p1, p2) for p1, p2 in zip(route_sequence, route_sequence[1:]))