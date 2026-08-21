"""Expansion von Wegpunkten in einen schrittweisen Gitterpfad.

Gemeinsame Stelle fuer die Logik, die bisher nur als
``FixedParameter._expand_waypoints`` (routes/fixed_parameter.py) existierte.
Die dortige Kopie ist verhaltensgleich und bleibt absichtlich unangetastet.
Neuer Code soll diese Funktion verwenden.
"""


def expand_waypoints(waypoints: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Expandiert Wegpunkte in einen schrittweisen Gitterpfad.

    Aufeinanderfolgende Wegpunkte teilen immer dieselbe x- oder y-Koordinate
    (sie liegen auf Gaengen oder Quergaengen), deshalb wird jede Gitterzelle
    zwischen ihnen aufgezaehlt. Gleiche aufeinanderfolgende Wegpunkte
    erzeugen kein zusaetzliches Segment.

    :param waypoints: Liste von (x, y)-Wegpunkten
    :return: Liste von (x, y)-Zellen, 4-benachbart und ohne Duplikate
    """
    if len(waypoints) < 2:
        return list(waypoints)

    path = [waypoints[0]]
    for i in range(1, len(waypoints)):
        ax, ay = waypoints[i - 1]
        bx, by = waypoints[i]
        if ax != bx and ay != by:
            # Darf nicht vorkommen: zwei aufeinanderfolgende Wegpunkte liegen
            # immer auf demselben Gang oder Quergang. Ein solches Paar
            # stillschweigend als horizontales Segment zu expandieren wuerde
            # den Pfad an der falschen Zelle enden lassen und die Laenge
            # verfaelschen.
            raise AssertionError(
                f"Wegpunkte {(ax, ay)} und {(bx, by)} liegen weder auf "
                f"derselben Spalte noch auf derselben Zeile.")
        if ax == bx:  # vertikales Segment
            step = 1 if by > ay else -1
            for y in range(ay + step, by + step, step):
                path.append((ax, y))
        else:  # horizontales Segment
            step = 1 if bx > ax else -1
            for x in range(ax + step, bx + step, step):
                path.append((x, ay))
    return path
