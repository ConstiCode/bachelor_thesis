# Geschlossene Pfadkonstruktion statt A*-Suche für die Frontend-Darstellung

Untersuchungsgegenstand: Lässt sich Rolle 1 von A* (Expansion einer
Besuchsreihenfolge in einen begehbaren Gitterpfad) ohne Suche lösen, also
direkt aus derselben Fallunterscheidung, die auch
`calculate_warehouse_distance` (`warehouse/grid.py:106`) benutzt?

Rolle 2 von A* (unabhängige Kontrolle der Distanzformel) bleibt unberührt.
`algorithms/a_star.py` ist vollständig erhalten, `tests/test_grid.py` ist
unverändert, `routes/fixed_parameter.py` wurde nicht angefasst, die bestehenden
A*-Aufrufe in `routes/nearest_neighbor.py` und `routes/christofides.py` stehen
weiter.

## Ergebnis in einem Satz

Die Drei-Segment-Hypothese hält, ohne Ausnahme und ohne angeflickte
Sonderfälle. Die Konstruktion ist ein exakter, suchfreier Ersatz für Rolle 1
und auf realistischen Layouts 40- bis 110-mal schneller.

## Was implementiert wurde

| Datei | Inhalt |
| --- | --- |
| `warehouse/grid.py:148` | `construct_warehouse_path(loc1, loc2)` — die geschlossene Konstruktion, spiegelt die Fallunterscheidung der Distanzformel |
| `algorithms/closed_form_route.py` | `ClosedFormRoute.calculate_closed_form_route(route)` — additives Gegenstück zu `AStar.calculate_a_star_route`, identisches Ausgabeformat |
| `utils/path_expansion.py` | `expand_waypoints(waypoints)` — gemeinsame Stelle für die Wegpunkt-Expansion |
| `tests/test_closed_form_path.py` | 13 Tests, Abnahmekriterien 1–5 |
| `benchmark_path_construction.py` | Laufzeitvergleich, reproduzierbar mit fester Saat |

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

## 6. Empfehlung

**Für die Frontend-Darstellung ja, der Austausch ist sinnvoll.** Er ist exakt
längengleich, geometrisch garantiert begehbar, deutlich schneller und macht die
gezeichnete Route reproduzierbar. Voraussetzung ist die Trennung, die dieser
Auftrag ohnehin fordert: A* verschwindet aus dem Produktionspfad, bleibt aber
die unabhängige Kontrolle im Testpfad.

Der Austausch wird in diesem Auftrag **nicht** durchgeführt. Konkret wäre zu
ändern:

**`routes/nearest_neighbor.py:18-19`**

```python
# vorher
a_star = AStar(self.grid.grid)
full_route = a_star.calculate_a_star_route(route)
# nachher
router = ClosedFormRoute(self.grid)
full_route = router.calculate_closed_form_route(route)
```

Wichtig: `ClosedFormRoute` bekommt die `WareHouseGrid`, nicht das rohe
2D-Gitter `self.grid.grid`. Der Grund ist Absicht — die Konstruktion benutzt die
Fallunterscheidung der Distanzformel mit, statt sie ein drittes Mal nachzubauen.
Das ist der Preis dafür, keine weitere Kopie der Regal-zu-Gang-Abbildung
anzulegen.

**`routes/christofides.py:36-37`** — dasselbe Muster, die Umhüllung
`[{'x': x, 'y': y} for (x, y) in route]` bleibt unverändert.

**`tests/routes/test_nearest_neighbor.py:39`** — bricht wie erwartet, an drei
Stellen:

- `mocker.patch('routes.nearest_neighbor.AStar')` → Patchziel wird
  `routes.nearest_neighbor.ClosedFormRoute`.
- `mock_astar_class.assert_called_once_with(grid.grid)` → `…with(grid)`, weil
  jetzt die Grid-Instanz übergeben wird, nicht deren `.grid`-Attribut.
- `…calculate_a_star_route.assert_called_once_with(…)` →
  `…calculate_closed_form_route.assert_called_once_with(…)`; die erwartete
  Besuchsreihenfolge bleibt gleich.

Nebenbedingung für diese Testdatei: `MockGrid` (Zeile 4) implementiert nur
`calculate_warehouse_distance`. Solange der Router gemockt ist, genügt das. Ein
künftiger Test, der ihn ungemockt benutzt, bräuchte auch
`construct_warehouse_path` — dann besser eine echte `WareHouseGrid` verwenden.

**`app.py:98-100`** — **keine Änderung nötig.** `app.py` reicht nur das Ergebnis
von `compute_route()` an `jsonify` weiter. Das Ausgabeformat bleibt identisch:
beide Verfahren liefern eine Liste von `(x, y)`-Tupeln, die JSON als Liste
zweielementiger Arrays serialisiert.
`static/scripts/WarehouseRenderer.js:188-191` liest `route[i][0]` und
`route[i][1]`, greift also positionsbasiert zu und merkt den Unterschied nicht.

**`tests/test_grid.py`** — bleibt unverändert. Die beiden Kreuzvergleichstests
sind der einzige unabhängige Beleg, dass die Distanzformel stimmt, und daran
hängen alle Routenlängen und Optimalitätsgaps der Arbeit. Die Formel gegen einen
Pfad zu prüfen, der aus derselben Formel gebaut ist, wäre zirkulär. Deshalb
prüft `tests/test_closed_form_path.py` die Konstruktion zusätzlich gegen A*
(Abnahmekriterium 4) und nicht nur gegen die Formel.

### Zur gemeinsamen Wegpunkt-Expansion

Die Expansionslogik liegt jetzt in `utils/path_expansion.py`.
`FixedParameter._expand_waypoints` (`routes/fixed_parameter.py:426`) behält
seine Kopie, weil der Auftrag ausdrücklich verbietet, diese Datei anzufassen.
Ich habe beide Funktionen auf 20 000 zufälligen Wegpunktlisten verglichen: **null
Abweichungen**, auch die Fehlermeldung im Verletzungsfall ist identisch. Der
empfohlene Folgeschritt ist deshalb trivial und risikolos — `_expand_waypoints`
durch eine Delegation an `expand_waypoints` ersetzen.

## 7. Abnahmekriterien

| # | Kriterium | Test | Status |
| --- | --- | --- | --- |
| 1 | `len(path) - 1 == calculate_warehouse_distance` exakt | `assert_path_is_valid`, in allen Tests | ✅ |
| 2 | jede Zelle begehbar, `(y,x)`-Indizierung gegen `_create_grid` | `assert_path_is_valid` | ✅ |
| 3 | 4-Nachbarn, keine Sprünge, Diagonalen, Duplikate | `assert_path_is_valid` | ✅ |
| 4 | die 8 Paare aus `test_grid.py` plus 540 Zufallspaare über 9 Layouts (`num_isles ∈ {1,5,10} × num_rows ∈ {1,3,8}`), Länge == A* | `test_targeted_pairs_match_formula_and_a_star`, `test_random_pairs_match_a_star_across_layouts` | ✅ |
| 5 | Wege von und zu `(0,0)`, inklusive `(0,0) → (0,0)` | `test_depot_paths` (1×1, 3×2, 5×3, 10×8, alle Regalplätze in beide Richtungen) | ✅ |

Aussagekraft geprüft: mit einer Mutation, die immer den oberen Ausgang wählt,
schlagen 8 der 13 Tests fehl. Die Tests greifen also.

## 8. Regressionsstand

```
.venv/bin/python -m pytest tests/          →  90 passed  (77 vorher + 13 neu)
.venv/bin/python verify_optimality.py      →  182/182 Instanzen: FixedParameter == Optimum
docker run --rm oprp-bench pytest tests/   →  90 passed
```
