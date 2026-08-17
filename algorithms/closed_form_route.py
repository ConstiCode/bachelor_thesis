class ClosedFormRoute:
    """Erzeugt Gitterpfade in geschlossener Form statt per A*-Suche.

    Gegenstueck zu :class:`algorithms.a_star.AStar` mit identischem
    Ausgabeformat (Liste von (x, y)-Tupeln). Steht additiv daneben: A* bleibt
    die unabhaengige Kontrolle der Distanzformel in tests/test_grid.py und
    wird von dieser Klasse nicht ersetzt.

    Unterschied in der Konstruktion: A* wird mit dem rohen Gitter
    (``grid.grid``) initialisiert, diese Klasse mit der ``WareHouseGrid``
    selbst, weil sie die Fallunterscheidung der Distanzformel
    (``construct_warehouse_path``) mitbenutzt statt sie ein zweites Mal
    nachzubauen.
    """

    def __init__(self, warehouse_grid):
        self.warehouse_grid = warehouse_grid

    def calculate_closed_form_route(self, route):
        """Expandiert eine Besuchsreihenfolge in einen begehbaren Gitterpfad.

        :param route: Liste von Dicts mit 'x'/'y' (Regalplaetze bzw. Depot),
            in Besuchsreihenfolge
        :return: Liste von (x, y)-Zellen des durchgehenden Pfades
        """
        full_route = []
        for i in range(len(route) - 1):
            # Rohe Regalkoordinaten, in der Regel selbst nicht begehbar
            raw_start = (route[i]['x'], route[i]['y'])
            raw_end = (route[i + 1]['x'], route[i + 1]['y'])

            path_segment = self.warehouse_grid.construct_warehouse_path(raw_start, raw_end)

            if path_segment:
                # Doppelte Positionen an den Nahtstellen vermeiden
                if full_route and full_route[-1] == path_segment[0]:
                    full_route.extend(path_segment[1:])
                else:
                    full_route.extend(path_segment)
        return full_route
