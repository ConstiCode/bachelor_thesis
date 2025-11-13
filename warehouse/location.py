"""
import math

# Todo do I even need this class? Or can I just use the function in the WareHouseGrid class?
class Location:
    def __init__(self, location_number, shelf_columns):
        if location_number <= 0:
            raise ValueError("Location number must be a positive integer.")

        self.location_number = location_number
        self.shelf_columns = shelf_columns
        self.x, self.y = self._calculate_coordinates()

    def _calculate_coordinates(self):


        # calculate the y coordinate
        shelf_number = math.ceil(self.location_number / 12)
        shelf_row = math.ceil(shelf_number / self.shelf_columns)

        shelf_start_coordinate = (shelf_row - 1) * 7 + 1

        offset_y = (self.location_number % 6) - 1 if self.location_number % 6 else 5
        y = shelf_start_coordinate + offset_y

        # calculate the x coordinate
        # shelf_column is the number that x would be if all the shelf's would be next to each other without any aisles to walk
        shelf_column = math.ceil(self.location_number / 6)
        x = shelf_column + shelf_number - 1
        x %= self.shelf_columns * 3
        return x, y

    def as_dict(self):
        return {
            'location_number': self.location_number,
            'x': self.x,
            'y': self.y
        }

    def as_tuple(self):
        return self.x, self.y
"""

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