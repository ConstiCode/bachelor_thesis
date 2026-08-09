"""Reproduzierbare Optimalitaets-Validierung des Fixed-Parameter-Algorithmus.

Erzeugt deterministisch 182 Zufallsinstanzen (fester Basis-Seed) und prueft
fuer jede Instanz:
  1. FixedParameter liefert exakt das Optimum eines unabhaengigen
     Referenzloesers (BFS-Distanzen auf dem Gitter = metrischer Abschluss,
     darauf Held-Karp).
  2. NearestNeighbor und Christofides liegen nie UNTER dem Optimum
     (Regressionswache gegen den Depot-Messfehler, vgl. Commit afc9e28).

Die Referenz-Komponenten werden aus tests/routes/test_fixed_parameter_dp.py
wiederverwendet; deshalb werden die Dev-Abhaengigkeiten benoetigt:

    pip install -r requirements.txt -r requirements-dev.txt
    python verify_optimality.py

Erwartete Ausgabe: "182/182 Instanzen: FixedParameter == Optimum."
Exit-Code 0 nur, wenn alle Pruefungen bestehen.

Referenziert in Abschnitt 4.8 (Validierung und Reproduzierbarkeit) der
Bachelorarbeit.
"""
import importlib.util
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

# Referenzloeser und Instanzgenerator aus der Testsuite laden (keine Duplikate).
_spec = importlib.util.spec_from_file_location(
    "fp_dp_tests", REPO_ROOT / "tests" / "routes" / "test_fixed_parameter_dp.py")
_ref = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ref)

from routes.fixed_parameter import FixedParameter          # noqa: E402
from routes.nearest_neighbor import NearestNeighbor        # noqa: E402
from routes import Christofides                            # noqa: E402

BASE_SEED = 20260805   # Datum der urspruenglichen Validierung (05.08.2026)
INSTANCE_COUNT = 182   # Stichprobenumfang aus Abschnitt 4.8 der Arbeit
MAX_COLS = 5           # kleine Layouts, damit Held-Karp exakt rechnen kann
MAX_ROWS = 3
MAX_PRODUCTS = 10

DEPOT = {'x': 0, 'y': 0}


def generate_instances():
    """182 deterministische (cols, rows, products, seed)-Tupel."""
    rng = random.Random(BASE_SEED)
    for _ in range(INSTANCE_COUNT):
        cols = rng.randint(1, MAX_COLS)
        rows = rng.randint(1, MAX_ROWS)
        products = rng.randint(2, MAX_PRODUCTS)
        yield cols, rows, products, rng.randrange(1_000_000)


def main():
    failures = []
    for index, (cols, rows, products, seed) in enumerate(generate_instances(), 1):
        grid, locations = _ref.sample_instance(cols, rows, products, seed)
        optimum = _ref.optimal_route_length(grid, locations)

        fp = FixedParameter(grid, list(locations), dict(DEPOT))
        fp.compute_route()
        if fp.route_length != optimum:
            failures.append((index, cols, rows, products, seed,
                             f"FP {fp.route_length} != Optimum {optimum}"))

        for solver_class in (NearestNeighbor, Christofides):
            solver = solver_class(grid, list(locations), dict(DEPOT))
            solver.compute_route()
            if solver.route_length < optimum:
                failures.append((index, cols, rows, products, seed,
                                 f"{solver_class.__name__} {solver.route_length}"
                                 f" < Optimum {optimum}"))

        if index % 26 == 0:
            print(f"  ... {index}/{INSTANCE_COUNT} geprueft")

    if failures:
        print(f"\nFEHLGESCHLAGEN: {len(failures)} Verstoesse")
        for index, cols, rows, products, seed, message in failures:
            print(f"  Instanz {index} (cols={cols}, rows={rows}, "
                  f"products={products}, seed={seed}): {message}")
        return 1

    print(f"\n{INSTANCE_COUNT}/{INSTANCE_COUNT} Instanzen: "
          f"FixedParameter == Optimum.")
    print("Keine Heuristik unterschreitet das Optimum.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
