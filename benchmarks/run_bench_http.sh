#!/usr/bin/env bash
# Benchmark ueber den laufenden /benchmark-Endpunkt.
#
# Aufruf:  benchmarks/run_bench_http.sh <name>     (z.B. b1)
#   liest:    benchmarks/payloads/<name>.json
#   schreibt: benchmarks/results/<name>_response.json
#             benchmarks/results/<name>.csv
#             benchmarks/results/<name>_run.log
#
# Voraussetzung: die Anwendung laeuft (siehe README, Abschnitt Docker).
# Die in der Arbeit berichteten Messwerte stammen aus bench_night_runner.py,
# der dieselben Schleifen ohne HTTP-Schicht ausfuehrt.
set -u

NAME="${1:?Aufruf: $0 <name>  (z.B. b1)}"
ROOT="${ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
PORT="${PORT:-5000}"
# JSON->CSV braucht nur die Standardbibliothek, deshalb genuegt System-Python.
PY="${PY:-python3}"

PAYLOAD="$ROOT/benchmarks/payloads/${NAME}.json"
OUTDIR="$ROOT/benchmarks/results"
RESP="$OUTDIR/${NAME}_response.json"
CSV="$OUTDIR/${NAME}.csv"
LOG="$OUTDIR/${NAME}_run.log"

[ -f "$PAYLOAD" ] || { echo "FEHLER: $PAYLOAD fehlt"; exit 1; }
mkdir -p "$OUTDIR"

echo "[$(date -Is)] START Benchmark '$NAME' (Payload: $PAYLOAD)" >> "$LOG"

# Kein --max-time: curl wartet, bis der synchrone Endpunkt fertig ist.
curl -s --connect-timeout 10 -X POST "http://127.0.0.1:${PORT}/benchmark" \
  -H "Content-Type: application/json" \
  -d @"$PAYLOAD" \
  -o "$RESP"
RC=$?
echo "[$(date -Is)] curl beendet (exit=$RC), Antwortgroesse=$(wc -c < "$RESP" 2>/dev/null) Bytes" >> "$LOG"

if [ "$RC" -ne 0 ]; then
  echo "[$(date -Is)] FEHLER: curl exit=$RC - keine Konvertierung." >> "$LOG"
  exit "$RC"
fi

"$PY" - "$RESP" "$CSV" >> "$LOG" 2>&1 <<'PYEOF'
import json, sys, csv
resp, out = sys.argv[1], sys.argv[2]
with open(resp) as f:
    data = json.load(f)
rows = data.get("results", [])
fields = ["algorithm", "num_columns", "num_crossings", "num_products",
          "iteration", "route_length", "computation_time_ms", "seed", "status"]
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k) for k in fields})
n_to = sum(1 for r in rows if r.get("status") == "timeout")
n_mem = sum(1 for r in rows if r.get("status") == "memory")
print(f"CSV geschrieben: {out} ({len(rows)} Zeilen, {n_to} Timeouts, "
      f"{n_mem} Memory-Abbrueche, {len(data.get('skipped', []))} uebersprungen)")
PYEOF

echo "[$(date -Is)] FERTIG -> $CSV" >> "$LOG"
