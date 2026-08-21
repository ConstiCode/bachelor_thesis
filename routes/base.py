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

    def expand_route(self, tour):
        """
        Expandiert die Tour in eine begehbare Zellenfolge fuer die Darstellung im
        Frontend. Diese Expansion liegt bewusst AUSSERHALB von compute_route und
        damit ausserhalb der gemessenen Berechnungszeit, weil sie nichts zum
        Ergebnis beitraegt: die Routenlaenge steht nach compute_route bereits fest.

        Standardfall: die Tour ist schon eine Zellenfolge (FixedParameter,
        ScfsPlus). Dort ist der Pfad das Ergebnis, nicht seine Darstellung.
        """
        return tour

    def compute_and_set_route_length(self, visit_sequence: list[tuple[int, int]]):
        """
        Unified route length calculation for all algorithms.
        Takes an ordered sequence of (x, y) location coordinates (in shelf/grid coordinate space)
        representing the visit order, computes the total warehouse distance using
        calculate_warehouse_distance, and sets self.route_length.
        :param visit_sequence: Ordered list of (x, y) tuples in shelf coordinate space.
        """
        self.route_length = sum(
            self.grid.calculate_warehouse_distance(p1, p2)
            for p1, p2 in zip(visit_sequence, visit_sequence[1:])
        )