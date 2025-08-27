from abc import ABC, abstractmethod

class BaseRoute(ABC):
    def __init__(self, grid, locations, start_pos):
        self.grid = grid
        self.locations = locations
        self.start_pos = start_pos

    @abstractmethod
    def compute_route(self):
        """
        Compute a route through the grid from start to end. If not implemented in a subclass abc will raise an error.
        """
        pass