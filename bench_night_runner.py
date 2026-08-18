"""Direkter Benchmark-Runner ohne HTTP-Schicht.

Spiegelt die Schleifen des /benchmark-Endpunkts aus app.py, ruft die Solver
aber unmittelbar ueber run_solver_capped auf. Mit diesem Runner wurden die in
der Arbeit berichteten Messwerte erhoben.

Aufruf:
    python bench_night_runner.py b1

Gelesen wird benchmarks/payloads/<name>.json, geschrieben
benchmarks/results/<name>.csv. Beide Verzeichnisse lassen sich ueber die
Umgebungsvariablen BENCH_PAYLOAD_DIR und BENCH_OUT_DIR umlenken.

Geschrieben wird nach JEDER Konfiguration, gefolgt von fsync. Ein Abbruch
kostet damit nur die angebrochene Stufe, alle fertigen Stufen bleiben
verwertbar. Ein erneuter Aufruf haengt an eine vorhandene Datei an.
"""
import csv
import json
import os
import random
import sys
import time

from app import SOLVERS, run_solver_capped
from warehouse.grid import WareHouseGrid

HERE = os.path.dirname(os.path.abspath(__file__))
PAYLOAD_DIR = os.environ.get("BENCH_PAYLOAD_DIR",
                             os.path.join(HERE, "benchmarks", "payloads"))
OUT_DIR = os.environ.get("BENCH_OUT_DIR",
                         os.path.join(HERE, "benchmarks", "results"))

FIELDS = ["algorithm", "num_columns", "num_crossings", "num_products",
          "iteration", "route_length", "computation_time_ms", "seed", "status"]

if len(sys.argv) != 2:
    sys.exit("Aufruf: python bench_night_runner.py <name>   (z.B. b1)")
name = sys.argv[1]

cfg = json.load(open(os.path.join(PAYLOAD_DIR, "%s.json" % name)))
os.makedirs(OUT_DIR, exist_ok=True)
out = os.path.join(OUT_DIR, "%s.csv" % name)

fresh = not os.path.exists(out)
fh = open(out, "a", newline="")
w = csv.DictWriter(fh, fieldnames=FIELDS)
if fresh:
    w.writeheader()
    fh.flush()

pt = {"x": 0, "y": 0}
t0 = time.time()
total = 0
print("=== %s gestartet, %d Konfigurationen ==="
      % (name, len(cfg["warehouse_configs"])), flush=True)

for wc in cfg["warehouse_configs"]:
    cols, rows = int(wc["numColumns"]), int(wc["numCrossings"])
    tg = time.perf_counter()
    grid = WareHouseGrid(cols, rows)
    grid_ms = (time.perf_counter() - tg) * 1000
    tl = grid.total_locations
    batch = []
    ts = time.time()
    for pc in cfg["product_counts"]:
        if pc > tl:
            continue
        for it in range(cfg["iterations"]):
            seed = cfg["base_seed"] + it
            rnd = random.Random(seed)
            locs = [grid.location_to_coordinate(x)
                    for x in rnd.sample(range(1, tl + 1), pc)]
            for alg in cfg["algorithms"]:
                o = run_solver_capped(SOLVERS[alg], grid, locs, pt,
                                      cfg["timeout_seconds"])
                ok = o["status"] == "ok"
                batch.append({
                    "algorithm": alg,
                    "num_columns": cols,
                    "num_crossings": rows,
                    "num_products": pc,
                    "iteration": it + 1,
                    "route_length": o.get("route_length") if ok else None,
                    "computation_time_ms": round(o["elapsed_ms"], 3) if ok else None,
                    "seed": seed,
                    "status": o["status"],
                })
    w.writerows(batch)
    fh.flush()
    os.fsync(fh.fileno())
    total += len(batch)
    print("  STUFE FERTIG %s cols=%d r=%d (h=%d) | %d Zeilen | Stufe %.0f s "
          "| gesamt %.2f h | Gitteraufbau %.3f ms"
          % (name, cols, rows, rows + 1, len(batch), time.time() - ts,
             (time.time() - t0) / 3600, grid_ms), flush=True)

fh.close()
print("=== %s KOMPLETT: %d Zeilen in %.2f h ==="
      % (name, total, (time.time() - t0) / 3600), flush=True)
