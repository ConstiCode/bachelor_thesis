import math
from utils.distances import manhattan_distance


class WareHouseGrid:
    def __init__(self, num_isles, num_rows):
        self.num_isles = num_isles
        self.num_rows = num_rows
        self.grid = self._create_grid()
        self.total_locations = num_isles * num_rows * 12  # Each shelf has 12 locations

    def _create_grid(self):
        """
            Generates a warehouse grid based on the number of vertical isles and rows of shelves.
            Each shelf is 2 columns wide and 6 rows tall, separated by walkable aisles (1 space).

            Parameters:
            - num_isles: number of vertical shelves
            - num_rows: number of horizontal shelf blocks

            Returns:
            - grid: 2D list representing the warehouse layout (1 = walkable, 0 = shelf)
        """
        shelf_height = 6
        aisle_height = 1
        shelf_width = 2
        aisle_width = 1

        total_rows = self.num_rows * shelf_height + (self.num_rows + 1) * aisle_height
        total_cols = self.num_isles * shelf_width + (self.num_isles + 1) * aisle_width

        grid = [[1 for _ in range(total_cols)] for _ in range(total_rows + 3)]

        for row_block in range(self.num_rows):
            for isle in range(self.num_isles):
                top = row_block * (shelf_height + aisle_height) + aisle_height
                left = isle * (shelf_width + aisle_width) + aisle_width

                for y in range(top, top + shelf_height):
                    for x in range(left, left + shelf_width):
                        grid[y][x] = 0  # 0 means shelf (not walkable)

        # mark the packing table as a 1
        grid[total_rows][(total_cols // 2) - 1] = 0

        return grid

    def location_to_coordinate(self, location: int):
        """
        Turns a location number into a given coordinate for the html canvas grid. This allows dynamic changes of the grid.
        Only works for location > 0.

        The following comment was created with ChatGPT
        Shelf Representation:
                  1      2      3       4      5
            +----+----+  +----+----+  +----+----+
         1  |  1 |  7 |  | 13 | 19 |  | 25 | 31 |
            +----+----+  +----+----+  +----+----+
         2  |  2 |  8 |  | 14 | 20 |  | 26 | 32 |
            +----+----+  +----+----+  +----+----+
         3  |  3 |  9 |  | 15 | 21 |  | 27 | 33 |
            +----+----+  +----+----+  +----+----+
         4  |  4 | 10 |  | 16 | 22 |  | 28 | 34 |
            +----+----+  +----+----+  +----+----+
         5  |  5 | 11 |  | 17 | 23 |  | 29 | 35 |
            +----+----+  +----+----+  +----+----+
         6  |  6 | 12 |  | 18 | 24 |  | 30 | 36 |
            +----+----+  +----+----+  +----+----+

            +----+----+  +----+----+  +----+----+
         8  | 37 | 43 |  | 49 | 55 |  | 61 | 67 |
            +----+----+  +----+----+  +----+----+
         9  | 38 | 44 |  | 50 | 56 |  | 62 | 68 |
            +----+----+  +----+----+  +----+----+
        10  | 39 | 45 |  | 51 | 57 |  | 63 | 69 |
            +----+----+  +----+----+  +----+----+
        11  | 40 | 46 |  | 52 | 58 |  | 64 | 70 |
            +----+----+  +----+----+  +----+----+
        12  | 41 | 47 |  | 53 | 59 |  | 65 | 71 |
            +----+----+  +----+----+  +----+----+
        13  | 42 | 48 |  | 54 | 60 |  | 66 | 72 |
            +----+----+  +----+----+  +----+----+


        """
        if location <= 0:
            raise ValueError("Location must be greater than 0")

        # calculate the y coordinate
        shelf_number = math.ceil(location / 12)
        shelf_row = math.ceil(shelf_number / self.num_isles)

        shelf_start_coordinate = (shelf_row - 1) * 7 + 1

        offset_y = (location % 6) - 1 if location % 6 else 5
        y = shelf_start_coordinate + offset_y

        # calculate the x coordinate
        # shelf_column is the number that x would be if all the shelf's would be next to each other without any aisles to walk
        shelf_column = math.ceil(location / 6)
        x = shelf_column + shelf_number - 1
        x %= self.num_isles * 3
        return {"location_number": location, "x": x, "y": y}

    def calculate_warehouse_distance(self, location_1, location_2):
        """
        Calculates the warehouse distance between two locations in the warehouse grid.
        :param location_1:
        :param location_2:
        :return:
        """
        coord_1 = self.location_to_coordinate(location_1)
        coord_2 = self.location_to_coordinate(location_2)

        route_cord_1 = self._turn_location_coordinate_to_route_loc(coord_1)
        route_cord_2 = self._turn_location_coordinate_to_route_loc(coord_2)

        # case 1 - same isle x values are the same
        if route_cord_1[0] == route_cord_2[0] :
            return manhattan_distance(route_cord_1, route_cord_2)

        elif route_cord_1[1] == route_cord_2[1]:
            around_top = (7 - route_cord_1[1] % 7)
            around_bottom = route_cord_1[1] % 7
            if around_top <= around_bottom:
                cost = around_top
                new_start_coordinate = route_cord_1[0], route_cord_1[1] + cost,
                return manhattan_distance(new_start_coordinate, route_cord_2) + cost
            else:
                cost = around_bottom
                new_start_coordinate = route_cord_1[0], route_cord_1[1] - cost,
                return manhattan_distance(new_start_coordinate, route_cord_2) + cost

        shelf_row_1 = math.ceil(route_cord_1[1] / 7)
        shelf_row_2 = math.ceil(route_cord_2[1] / 7)

        if shelf_row_1 == shelf_row_2:
            cost_around_top = (route_cord_1[1] % 7) + (route_cord_2[1] % 7)
            cost_around_bottom = (7 - route_cord_1[1] % 7) + (7 - route_cord_2[1] % 7)
            around_top = cost_around_top <= cost_around_bottom
            around_bottom = cost_around_top > cost_around_bottom
        else:
            around_bottom = shelf_row_1 < shelf_row_2
            around_top = shelf_row_1 > shelf_row_2

        # case 2 - different isle
        # move down from location 1
        if around_top:
            cost = route_cord_1[1] % 7
            new_start_coordinate = route_cord_1[0], route_cord_1[1] - cost,
            return manhattan_distance(new_start_coordinate, route_cord_2) + cost

        # move up from location 1
        elif around_bottom:
            cost = (7 - route_cord_1[1] % 7)
            new_start_coordinate = route_cord_1[0], route_cord_1[1] + cost,
            return manhattan_distance(new_start_coordinate, route_cord_2) + cost







    def _turn_location_coordinate_to_route_loc(self, coordinate) -> tuple[int, int]:
        x = coordinate.get('x', False)
        y = coordinate.get('y', False)

        if self.grid[y][x + 1]:
            return x + 1, y
        else:
            return x - 1, y
