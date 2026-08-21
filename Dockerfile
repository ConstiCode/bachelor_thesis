# Reproduzierbare Benchmark-Umgebung für die OPRP-Webapp (Bachelorarbeit).
# Die Build- und Run-Befehle stehen als Kommentare am Ende dieser Datei.
FROM python:3.12-slim

WORKDIR /app

# make wird fuer die Targets aus dem Makefile benoetigt.
RUN apt-get update \
 && apt-get install -y --no-install-recommends make \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-dev.txt ./
# requirements-dev.txt enthaelt pytest; wird fuer die Validierungslaeufe
# (make test, make verify) im Container benoetigt.
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

COPY . .

EXPOSE 5000

# Der Entrypoint erklaert bei jedem Start, wie es weitergeht, und fuehrt
# danach den uebergebenen Befehl aus (Standard: die Webanwendung).
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# --host 0.0.0.0 nötig, damit der Port aus dem Container heraus erreichbar ist
CMD ["flask", "--app", "app", "run", "--host", "0.0.0.0", "--port", "5000"]

# ===================================================================
# Zum Kopieren nach  cat Dockerfile
# ===================================================================
#
# Image bauen:
#   docker build -t oprp-bench .
#
# Anwendung starten (interaktive Visualisierung auf http://localhost:5000):
#   docker run --rm -p 127.0.0.1:5000:5000 oprp-bench
#
# Uebersicht aller Targets (gelesene und erzeugte Dateien, Laufzeit, Speicher):
#   docker run --rm oprp-bench make help
#
# Tests und Optimalitaetsvalidierung:
#   docker run --rm oprp-bench make test
#   docker run --rm oprp-bench make verify
#
# Benchmark B1 (unter einer Minute), Ergebnis auf ein Host-Volume schreiben:
#   mkdir -p results
#   docker run --rm -v "$PWD/results:/data" oprp-bench make b1 BENCH_OUT_DIR=/data
#
# Benchmarks B2 und B3 (je rund 10 bis 11 Stunden, bis 12 GB RAM je
# Solverprozess). Lange Laeufe im Hintergrund:
#   docker run -d --name oprp-b2 -v "$PWD/results:/data" \
#     oprp-bench make b2 BENCH_OUT_DIR=/data
#   docker logs -f oprp-b2
#
# Alle drei Benchmarks hintereinander (rund 21 Stunden):
#   docker run -d --name oprp-all -v "$PWD/results:/data" \
#     oprp-bench make bench-all BENCH_OUT_DIR=/data
#
# Eine GPU bringt hier keinen Vorteil: alle drei Algorithmen sind
# single-threaded und rein CPU-gebunden.
