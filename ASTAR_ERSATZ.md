# Geschlossene Pfadkonstruktion statt A*-Suche für die Frontend-Darstellung

Untersuchungsgegenstand: Lässt sich Rolle 1 von A* (Expansion einer
Besuchsreihenfolge in einen begehbaren Gitterpfad) ohne Suche lösen, also
direkt aus derselben Fallunterscheidung, die auch
`calculate_warehouse_distance` (`warehouse/grid.py:106`) benutzt?

Rolle 2 von A* (unabhängige Kontrolle der Distanzformel) bleibt unberührt.
`algorithms/a_star.py` ist vollständig erhalten und `tests/test_grid.py` ist
unverändert.

Der Bericht entstand in zwei Schritten: zuerst der Prototyp mit Belegen
(Abschnitte 1–5), dann der vollzogene Austausch in den beiden Solvern
(Abschnitt 6). `calculate_warehouse_distance` ist in beiden Schritten
unverändert geblieben.

## Ergebnis in einem Satz

Die Drei-Segment-Hypothese hält, ohne Ausnahme und ohne angeflickte
Sonderfälle. Die Konstruktion ist ein exakter, suchfreier Ersatz für Rolle 1,
auf realistischen Layouts 40- bis 110-mal schneller, und sie ist inzwischen in
`NearestNeighbor` und `Christofides` an die Stelle von A* getreten.

## Was implementiert wurde

| Datei | Inhalt |
| --- | --- |
| `warehouse/grid.py:148` | `construct_warehouse_path(loc1, loc2)` — die geschlossene Konstruktion, spiegelt die Fallunterscheidung der Distanzformel |
| `algorithms/closed_form_route.py` | `ClosedFormRoute.calculate_closed_form_route(route)` — Gegenstück zu `AStar.calculate_a_star_route`, identisches Ausgabeformat |
| `utils/path_expansion.py` | `expand_waypoints(waypoints)` — gemeinsame Stelle für die Wegpunkt-Expansion, benutzt von der Konstruktion und von `FixedParameter` |
| `tests/test_closed_form_path.py` | 13 Tests, Abnahmekriterien 1–5 |
| `tests/routes/test_route_expansion.py` | 11 Integrationstests für die Solver auf echtem Gitter |
| `benchmark_path_construction.py` | Laufzeitvergleich, reproduzierbar mit fester Saat |

Umgestellt: `routes/nearest_neighbor.py`, `routes/christofides.py`,
`routes/fixed_parameter.py` (nur die Delegation der Expansion),
`tests/routes/test_nearest_neighbor.py`. Details in Abschnitt 6.

`calculate_warehouse_distance` selbst ist unverändert.

## 1. Hält die Drei-Segment-Hypothese?

**Ja.** Der Pfad besteht aus höchstens drei Segmenten: vertikal in der
Startgangspalte zum gewählten Quergang, horizontal entlang des Quergangs zur
Zielgangspalte, vertikal in der Zielgangspalte zum Ziel.

Der Beweis ist zweiteilig, Geometrie plus Längengleichheit.

**Begehbarkeit.** Aus `_create_grid` (`warehouse/grid.py:13`) folgt: Regale
belegen `x` mit `x mod 3 ∈ {1,2}` und `y` mit `y mod 7 ∈ {1,…,6}`. Also ist

- jede Gangspalte `x ≡ 0 (mod 3)` auf ihrer **ganzen** Höhe begehbar,
- jeder Quergang `y ≡ 0 (mod 7)` auf seiner **ganzen** Breite begehbar.

Die Regal-zu-Gang-Abbildung liefert immer eine Gangspalte (`x mod 3 == 1` →
`x-1`, `x mod 3 == 2` → `x+1`, beides `≡ 0 mod 3`), und beide Exit-Kandidaten
liegen auf einem Quergang. Damit liegt jedes der drei Segmente vollständig in
einer vollständig begehbaren Zeile oder Spalte — verifiziert ✅ als
Abnahmekriterium 2 gegen das Gitter selbst.

**Länge.** Die Formel berechnet
`cost_to_exit + |x1-x2| + |y_exit-y2|` und nimmt das Minimum über beide Exits.
Genau diese drei Summanden sind die Längen der drei Segmente. Die Konstruktion
wählt das Argmin desselben Vergleichs, deshalb ist
`len(path) - 1 == calculate_warehouse_distance(loc1, loc2)` keine Näherung,
sondern algebraisch dieselbe Zahl.

Die Hypothese wurde gezielt an den im Auftrag genannten Bruchkandidaten
geprüft, alle unauffällig:

- **Mehrblockige Layouts `num_rows > 1`:** ein Pfad braucht nie zwei Quergänge.
  Der Grund ist, dass beide Gangspalten durchgehend begehbar sind — es gibt
  keinen Grund, den Quergang zu wechseln, weil kein Regal die Zielspalte
  blockiert. Geprüft bis `num_rows = 15`.
- **Paare in derselben Gangspalte:** Ein Segment, rein vertikal. Das ist keine
  Ausnahme, sondern derselbe erste Zweig, den die Distanzformel schon hat.
- **Depot `(0,0)`:** `y1 % 7 == 0`, also fällt das erste Segment auf Länge 0
  zusammen und der Pfad hat zwei Segmente. `(0,0) → (0,0)` ergibt `[(0,0)]`,
  Länge 0.

`test_at_most_three_segments` zählt die Richtungswechsel über **alle** 5 184
Paare des 3×2-Layouts, `test_all_pairs_small_layouts` prüft alle Paare inklusive
Depot in vier Layouts (1×1, 1×3, 2×2, 3×2, zusammen 9 268 Paare).

## 2. Die beiden bekannten Fallen

### 2a. Können `top_exit` oder `bottom_exit` aus dem Gitter laufen?

**Nein, das ist durch die Gittergeometrie ausgeschlossen.** ✅ Belegt analytisch
und empirisch (`test_exit_candidates_stay_inside_the_grid`).

Jede Gangzelle, die aus einem Regalplatz entsteht, hat `y mod 7 ∈ {1,…,6}` mit
`y ∈ [7k+1, 7k+6]`, `k ∈ {0,…,num_rows-1}`. Daraus:

- `bottom_exit_y = y - (y mod 7) = 7·⌊y/7⌋ ≥ 0` — nie negativ.
- `top_exit_y = y + 7 - (y mod 7) = 7·(⌊y/7⌋ + 1) ≤ 7·num_rows` — nie über dem
  obersten Quergang.

Das Depot ist der einzige Startpunkt mit `y = 0`: dort ist
`bottom_exit == (0,0)` (Kosten 0) und `top_exit == (0,7) ≤ 7·num_rows`, weil
`num_rows ≥ 1`.

Dabei ist eine Korrektur zur Aufgabenbeschreibung nötig: das Gitter ist nicht
`H = 7·num_rows + 1` hoch, sondern `7·num_rows + 4`. `_create_grid` legt
`total_rows + 3` Zeilen an (`warehouse/grid.py:33`). Unterhalb des Lagers liegen
drei zusätzliche, praktisch vollständig begehbare Zeilen; in
`y = 7·num_rows + 1` ist eine einzelne Zelle als Packtisch blockiert
(`grid[total_rows][total_cols//2 - 1] = 0`). Gemessen: 1×1 → 4×11, 3×2 → 10×18,
10×8 → 31×60, 20×15 → 61×109. Der oberste erreichbare Exit `7·num_rows` liegt
damit sogar drei Zeilen vom Rand entfernt. Die blockierte Packtischzelle liegt
immer in einer Regalspalte (`((3n+1)//2 - 1) mod 3 ∈ {1,2}`, geprüft für
`num_isles = 1…200`) und außerhalb des von Routen benutzten `y`-Bereichs `[0, 7·num_rows]`, ist
für die Konstruktion also irrelevant.

Fazit: die fehlende Grenzprüfung in der Distanzformel ist keine Lücke, sondern
durch die Geometrie abgedeckt. Sie wäre erst dann eine, wenn ein Aufrufer eine
Koordinate übergibt, die kein Regalplatz und nicht das Depot ist — siehe 2b.

### 2b. Weichen die beiden Regal-zu-Gang-Abbildungen voneinander ab?

**Nicht in der Zuordnung, nur im Fehlerverhalten.** ✅ Ich habe
`_stock_loc_coordinate_to_route_loc` (`algorithms/a_star.py:25`) gegen
`_turn_location_coordinate_to_route_loc` (`warehouse/grid.py:203`) zellenweise
über **jede** Gitterzelle der Layouts 1×1, 3×2 und 5×3 verglichen.

Ergebnis: es gibt **keine** Zelle, in der beide eine Koordinate zurückgeben und
diese Koordinaten verschieden sind. Für jeden legalen Input — Regalplatz oder
Depot — sind die Abbildungen identisch. Abweichungen gibt es nur bei
**illegalem** Input, also bei begehbaren Zellen außer dem Depot:

| Input | `a_star.py` | `grid.py` |
| --- | --- | --- |
| begehbare Zelle, z. B. `(1,0)` | `ValueError` | still `(2,0)` — eine Regalzelle |
| begehbare Zelle in Spalte 0, z. B. `(0,1)` | `ValueError` | still `(-1,1)` — negatives `x` |
| rechteste Gangspalte `x = 3·num_isles` | `ValueError` | `IndexError` |

Für diesen Auftrag heißt das: keine Abweichung, die man einer
Konstruktionsabweichung anlasten könnte. Nebenbefund außerhalb des Auftrags:
`grid.py` prüft seinen Input nicht und liefert bei Fehlbenutzung stumm eine
Regalzelle oder negatives `x` statt einer Ausnahme. Das ist eine latente
Robustheitslücke, keine Fehlberechnung — alle produktiven Aufrufe übergeben
Regalplätze oder das Depot.

### 2c. Zusatzbefund: die Distanzformel ist auch jenseits von 3×2 korrekt

Die Kreuzvergleichstests in `tests/test_grid.py` decken nur das 3×2-Layout ab.
Damit ein Bruch der Konstruktion nicht mit einem Bruch der Formel verwechselt
wird, habe ich die Formel gegen eine **BFS** geprüft — unabhängig von
`a_star.py`, es wird kein Zeilchen A*-Code benutzt. Vollständig alle Paare
inklusive Depot für 1×1 (169), 1×3 (1 369), 3×2 (5 329), 5×3 (32 761),
10×1 (14 641), 2×8 (37 249), plus 4 000 Stichproben für 10×8. **Null
Abweichungen.** Die Formel ist auf allen geprüften Layouts korrekt.

## 3. Welche Sonderfälle brauchen eigene Behandlung?

Genau zwei, und beide sind Einzeiler, kein Flickwerk:

1. **`x1 == x2`** — rein vertikaler Weg. Ohne diesen Zweig würde die
   Konstruktion einen sinnlosen Umweg über einen Quergang einlegen. Die
   Distanzformel hat denselben Zweig an derselben Stelle, es entsteht also kein
   zusätzlicher Fall, sondern eine 1:1-Spiegelung.
2. **Gleichstand zwischen `bottom_exit` und `top_exit`** — das `min()` der
   Formel muss sich nicht entscheiden, die Konstruktion muss. Gewählt ist der
   untere Ausgang; die Länge ist in beiden Fällen dieselbe.

Ausdrücklich **keine** eigene Behandlung brauchen:

- Das Depot als Start oder Ziel. `(0,0)` ist eine gewöhnliche begehbare Zelle in
  Gangspalte 0 auf Quergang 0. Der Sonderfall steckt schon in der
  Regal-zu-Gang-Abbildung, die die Konstruktion mitbenutzt.
- Entartete Segmente der Länge 0 (Start liegt schon auf dem Quergang, Start ==
  Ziel). `expand_waypoints` erzeugt dafür einen leeren Bereich, ohne Fallabfrage.
- Grenzabschneidung der Exits, siehe 2a.

## 4. Laufzeitvergleich

Messbedingungen: AMD Ryzen 7 PRO 5850U, CPython 3.12.3 (`.venv`), Linux
6.8.0-137. 200 zufällige Regalplatzpaare pro Layout, feste Saat 20260817,
bester von 3 Durchläufen. Verglichen wird jeweils der komplette Aufruf für ein
Paar, inklusive Regal-zu-Gang-Abbildung und Materialisierung der Zellenliste:
`AStar.calculate_a_star_route([a, b])` gegen
`ClosedFormRoute.calculate_closed_form_route([a, b])`. Vor der Messung prüft das
Skript für jedes Paar, dass beide Verfahren dieselbe Länge liefern — es werden
also nicht versehentlich zwei verschiedene Dinge verglichen. Reproduzierbar mit
`.venv/bin/python benchmark_path_construction.py`.

| Layout (Gänge × Reihen) | Gitter (B×H) | A* [ms] | geschlossen [ms] | Faktor | max. Distanz |
| --- | --- | --- | --- | --- | --- |
| 1 × 1 | 4 × 11 | 2,05 | 0,27 | **7,5×** | 10 |
| 3 × 2 | 10 × 18 | 3,77 | 0,34 | **11,2×** | 19 |
| 5 × 3 | 16 × 25 | 6,21 | 0,38 | **16,4×** | 29 |
| 10 × 8 | 31 × 60 | 19,45 | 0,48 | **40,2×** | 78 |
| 20 × 15 | 61 × 109 | 75,66 | 0,69 | **110,3×** | 156 |

Für 200 Paare, also 10,3 µs gegen 1,4 µs pro Paar im Testlayout 3×2 und
378 µs gegen 3,4 µs pro Paar bei 20×15.

Der Faktor wächst mit der Gittergröße, weil A* Knoten proportional zur
durchsuchten Fläche expandiert, während die Konstruktion nur die Zellen des
Pfades erzeugt, also proportional zur Distanz arbeitet. Für das im Frontend
übliche 3×2 ist der absolute Gewinn klein (Millisekunden pro Tour); relevant
wird er bei großen Layouts und bei Christofides, das für jede Tour viele
Segmente expandiert.

## 5. Verlauf der Pfade im Vergleich zu A*

Die Länge stimmt immer, der Verlauf nicht immer — beide Wege sind kürzeste Wege,
und bei Gleichstand entscheidet A* nach Heap-Reihenfolge, die Konstruktion nach
Regel. Gemessen an 400 Zufallspaaren pro Layout:

| Layout | zellengleich zu A* | gleich lang, anderer Verlauf |
| --- | --- | --- |
| 3 × 2 | 400 | 0 |
| 5 × 3 | 370 | 30 |
| 10 × 8 | 270 | 130 |

Für die Darstellung ist das kein Nachteil, eher einer der Gründe für den
Austausch: die Konstruktion wählt reproduzierbar den günstigeren und bei
Gleichstand den unteren Quergang, die gezeichneten Routen sehen dadurch
regelmäßiger aus. Im Testlayout 3×2 ist der gezeichnete Pfad ohnehin identisch.

## 6. Der Austausch — durchgeführt

**Für die Frontend-Darstellung ist der Austausch sinnvoll und ist vollzogen.**
Er ist exakt längengleich, geometrisch garantiert begehbar, deutlich schneller
und macht die gezeichnete Route reproduzierbar. Die Trennung, auf der alles
beruht, bleibt bestehen: A* verschwindet aus dem Produktionspfad, bleibt aber
die unabhängige Kontrolle im Testpfad.

Der entscheidende Punkt für die Arbeit: **keine berichtete Kennzahl ändert
sich.** `route_length` entsteht in `BaseRoute.compute_and_set_route_length`
(`routes/base.py:24`) aus `calculate_warehouse_distance` über die
Besuchsreihenfolge, nicht aus dem gezeichneten Pfad. Der Austausch betrifft
ausschließlich die Expansion für die Visualisierung. Benchmarks,
Routenlängen und Optimalitätsgaps sind davon unabhängig — `verify_optimality.py`
bestätigt weiter 182/182.

### Was geändert wurde

**`routes/nearest_neighbor.py:18-21`**

```python
# vorher
a_star = AStar(self.grid.grid)
full_route = a_star.calculate_a_star_route(route)
# nachher
router = ClosedFormRoute(self.grid)
full_route = router.calculate_closed_form_route(route)
```

**`routes/christofides.py:36-38`** — dasselbe Muster, die Umhüllung
`[{'x': x, 'y': y} for (x, y) in route]` bleibt unverändert.

Der Import wechselt in beiden Dateien von `AStar` zu `ClosedFormRoute`.
`ClosedFormRoute` bekommt die `WareHouseGrid`, nicht das rohe 2D-Gitter
`self.grid.grid`. Das ist Absicht — die Konstruktion benutzt die
Fallunterscheidung der Distanzformel mit, statt sie ein drittes Mal nachzubauen.
Das ist der Preis dafür, keine weitere Kopie der Regal-zu-Gang-Abbildung
anzulegen.

**`tests/routes/test_nearest_neighbor.py:37-61`** — an drei Stellen angepasst,
wie vorhergesagt:

- Patchziel `routes.nearest_neighbor.AStar` → `routes.nearest_neighbor.ClosedFormRoute`
- `assert_called_once_with(grid.grid)` → `assert_called_once_with(grid)`, weil
  jetzt die Grid-Instanz übergeben wird
- `calculate_a_star_route` → `calculate_closed_form_route`; die erwartete
  Besuchsreihenfolge bleibt gleich

`MockGrid` in dieser Datei brauchte **keine** `construct_warehouse_path`-Methode,
weil der Router gemockt ist. Ein künftiger Test, der ihn ungemockt benutzt,
bräuchte sie — dann besser eine echte `WareHouseGrid` verwenden.

**`routes/fixed_parameter.py:424`** — `_expand_waypoints` delegiert jetzt an
`utils.path_expansion.expand_waypoints`, statt die Logik zu wiederholen. Damit
gibt es die Expansion nur noch einmal im Repo. Belegt vor dem Umbau durch einen
Vergleich beider Funktionen auf 20 000 zufälligen Wegpunktlisten: null
Abweichungen, auch die Fehlermeldung im Verletzungsfall identisch.

**Neu: `tests/routes/test_route_expansion.py`** — Integrationstests auf einem
echten Gitter, weil der gemockte Test nur die Verdrahtung prüft. Für alle drei
Solver über drei Layouts: Pfad begehbar, 4-benachbart, Rundtour ab und bis zum
Depot, und die zentrale Invariante

```
len(full_route) - 1 == solver.route_length
```

Damit hängt die Visualisierung nachweisbar an derselben Zahl, die in die
Benchmarks eingeht. Zusätzlich wird für `NearestNeighbor` und `Christofides`
dieselbe Besuchsreihenfolge mit beiden Verfahren expandiert und die Zellenzahl
verglichen — A* bleibt also auch hier die unabhängige Kontrolle.

### Was nicht geändert wurde

**`app.py:98-100`** — keine Änderung nötig, wie vorhergesagt. `app.py` reicht nur
das Ergebnis von `compute_route()` an `jsonify` weiter. Verifiziert mit einem
Ende-zu-Ende-Aufruf des echten Endpunkts `/calculate-route` über den
Flask-Testclient: HTTP 200, keine Fehlermeldungen, für alle vier Solver ist der
Pfad begehbar, und die erste Zelle serialisiert wie vorher zu `[0, 0]`.
`static/scripts/WarehouseRenderer.js:188-191` liest `route[i][0]` und
`route[i][1]`, greift also positionsbasiert zu und merkt den Unterschied nicht.

**`algorithms/a_star.py`** — vollständig erhalten, inklusive
`tests/algorithms/test_a_star.py`.

**`tests/test_grid.py`** — unverändert. Die beiden Kreuzvergleichstests sind der
einzige unabhängige Beleg, dass die Distanzformel stimmt, und daran hängen alle
Routenlängen und Optimalitätsgaps der Arbeit. Die Formel gegen einen Pfad zu
prüfen, der aus derselben Formel gebaut ist, wäre zirkulär. Deshalb prüfen
`tests/test_closed_form_path.py` und `tests/routes/test_route_expansion.py` die
Konstruktion zusätzlich gegen A* und nicht nur gegen die Formel.

**`routes/scfs_plus.py`** — nicht angefasst, benutzte A* nie.

### Zwei Vorbefunde, die beim Umbau sichtbar wurden

Beides bestand vorher schon und ist nicht Folge des Austauschs. Beides bleibt
absichtlich stehen, weil es außerhalb dieses Auftrags liegt.

1. **Uneinheitlicher Sequenztyp.** `NearestNeighbor` und `Christofides` liefern
   `(x, y)`-Tupel, `FixedParameter` liefert `[x, y]`-Listen
   (`routes/fixed_parameter.py:330`). Praktisch irrelevant: JSON serialisiert
   beides zum selben Array, und der Renderer greift positionsbasiert zu. Der
   Integrationstest prüft deshalb das Paarformat, nicht den Sequenztyp.
2. **`scfsPlus` expandiert nicht.** Der Solver gibt Wegpunkte statt Gitterzellen
   zurück — im Testfall 14 Punkte für Länge 32. Das fällt visuell nicht auf, weil
   alle aufeinanderfolgenden Wegpunkte gangparallel liegen (geprüft: kein
   diagonales Paar) und die Canvas-Linie zwischen zwei gangparallelen Punkten
   genauso aussieht wie die expandierte Zellenfolge. Ein `expand_waypoints`-Aufruf
   würde es vereinheitlichen, jetzt wo die Funktion geteilt zur Verfügung steht.

## 7. Abnahmekriterien

| # | Kriterium | Test | Status |
| --- | --- | --- | --- |
| 1 | `len(path) - 1 == calculate_warehouse_distance` exakt | `assert_path_is_valid`, in allen Tests | ✅ |
| 2 | jede Zelle begehbar, `(y,x)`-Indizierung gegen `_create_grid` | `assert_path_is_valid` | ✅ |
| 3 | 4-Nachbarn, keine Sprünge, Diagonalen, Duplikate | `assert_path_is_valid` | ✅ |
| 4 | die 8 Paare aus `test_grid.py` plus 540 Zufallspaare über 9 Layouts (`num_isles ∈ {1,5,10} × num_rows ∈ {1,3,8}`), Länge == A* | `test_targeted_pairs_match_formula_and_a_star`, `test_random_pairs_match_a_star_across_layouts` | ✅ |
| 5 | Wege von und zu `(0,0)`, inklusive `(0,0) → (0,0)` | `test_depot_paths` (1×1, 3×2, 5×3, 10×8, alle Regalplätze in beide Richtungen) | ✅ |

Aussagekraft der Tests mit zwei Mutationen geprüft, jeweils eingebaut, gemessen
und zurückgenommen:

| Mutation | Wirkung | Ergebnis |
| --- | --- | --- |
| `exit_coord` immer `top_exit_coord`, statt das Minimum zu wählen | Pfad bleibt begehbar, wird aber länger als die Formel sagt | 8 von 13 Tests in `test_closed_form_path.py` fallen |
| Nahtstellen-Deduplizierung in `ClosedFormRoute` entfernt (`full_route.extend(path_segment)` ohne Fallabfrage) | jede Segmentgrenze taucht doppelt auf | 9 Tests fallen, davon 4 in `test_route_expansion.py` |

Die Tests greifen also, und zwar beide Ebenen: die Konstruktion selbst und die
Verkettung zur ganzen Tour.

## 8. Regressionsstand

Nach dem Prototyp (Abschnitte 1–5):

```
.venv/bin/python -m pytest tests/          →  90 passed  (77 vorher + 13 neu)
.venv/bin/python verify_optimality.py      →  182/182 Instanzen: FixedParameter == Optimum
docker run --rm oprp-bench pytest tests/   →  90 passed
```

Nach dem Austausch (Abschnitt 6):

```
.venv/bin/python -m pytest tests/          →  101 passed  (+ 11 Integrationstests)
.venv/bin/python verify_optimality.py      →  182/182 Instanzen: FixedParameter == Optimum
docker run --rm oprp-bench pytest tests/   →  101 passed
POST /calculate-route (Flask-Testclient)   →  HTTP 200, alle 4 Solver, Pfade begehbar
```

## 9. Live-Verifikation am laufenden Server

Über die Testsuite hinaus wurde der echte Flask-Server gestartet und über HTTP
angesprochen, weil der Flask-Testclient den WSGI-Stack umgeht und deshalb nicht
belegt, dass die Route im Browser ankommt.

**Startbedingung.** Port 5000, den `app.run()` per Voreinstellung nimmt, war auf
dem Entwicklungsrechner von einem fremden `node`-Prozess belegt (`ss -tlnp`:
PID 2036172, `0.0.0.0:5000`). Der Server wurde deshalb auf Port 5001 gestartet,
ohne `app.py` zu ändern:

```bash
.venv/bin/python -c "from app import app; app.run(host='127.0.0.1', port=5001)"
```

Falls das wieder auftritt: der Konflikt hat nichts mit dem Projekt zu tun, ein
anderer Port genügt. `app.py` bewusst nicht anpassen, damit die Voreinstellung
für andere Rechner erhalten bleibt.

**Ergebnis.** `GET /` liefert HTTP 200. `POST /calculate-route` mit 3 Gängen,
2 Reihen und 5 Regalplätzen liefert HTTP 200, leeres `error_message`-Array und
für alle vier Solver einen Pfad:

| Algorithmus | `length` | Zellen im Pfad | `Zellen - 1 == length` | Start → Ende |
| --- | --- | --- | --- | --- |
| nearestNeighbor | 44 | 45 | ✅ | `[0,0]` → `[0,0]` |
| christofides | 38 | 39 | ✅ | `[0,0]` → `[0,0]` |
| fixedParameter | 38 | 39 | ✅ | `[0,0]` → `[0,0]` |
| scfsPlus | 38 | 17 | — (Wegpunkte, siehe Abschnitt 6) | `[0,0]` → `[0,0]` |

Für die drei zellenexpandierenden Solver zeichnet das Frontend damit genau die
Strecke, die auch als Länge berichtet wird. Die Zellen serialisieren zu
`[x, y]`-Arrays, also im selben Format wie vor dem Austausch.

## 10. Änderungsprotokoll

Zwei Commits auf dem Branch `astar-ersatz-experiment`, nicht gepusht.

**`1f7a002` — Prototyp, rein additiv.** Keine bestehende Aufrufstelle geändert.

| Datei | Art |
| --- | --- |
| `warehouse/grid.py` | neue Methode `construct_warehouse_path`, `calculate_warehouse_distance` unberührt |
| `algorithms/closed_form_route.py` | neu |
| `algorithms/__init__.py` | Export `ClosedFormRoute` |
| `utils/path_expansion.py` | neu |
| `tests/test_closed_form_path.py` | neu, 13 Tests |
| `benchmark_path_construction.py` | neu |
| `ASTAR_ERSATZ.md` | neu |

**`fada9a0` — der Austausch.**

| Datei | Art |
| --- | --- |
| `routes/nearest_neighbor.py` | `AStar` → `ClosedFormRoute` |
| `routes/christofides.py` | `AStar` → `ClosedFormRoute` |
| `routes/fixed_parameter.py` | `_expand_waypoints` delegiert an `utils.path_expansion` |
| `tests/routes/test_nearest_neighbor.py` | Mock auf den neuen Router umgestellt |
| `tests/routes/test_route_expansion.py` | neu, 11 Integrationstests |
| `ASTAR_ERSATZ.md` | Abschnitte 6 und 8 fortgeschrieben |

**Über beide Commits unverändert:** `algorithms/a_star.py`,
`tests/algorithms/test_a_star.py`, `tests/test_grid.py`,
`WareHouseGrid.calculate_warehouse_distance`, `warehouse/grid.py::_create_grid`,
`routes/base.py`, `routes/scfs_plus.py`, `app.py`, `static/`, `templates/`.

Rücknahme, falls nötig: `git revert fada9a0` stellt den A*-Aufrufpfad wieder her
und lässt den Prototyp mit allen Belegen stehen. Nur die Delegation in
`fixed_parameter.py` zurücknehmen geht mit
`git checkout 1f7a002 -- routes/fixed_parameter.py`.
