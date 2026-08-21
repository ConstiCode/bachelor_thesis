# Makefile fuer die OPRP-Algorithmenvergleich-Webapp (Bachelorarbeit).
#
# Erstes Target ist absichtlich "help": ein blankes "make" erklaert, was
# moeglich ist. Fuer jedes Target sind gelesene Dateien, erzeugte Dateien,
# ungefaehre Laufzeit und ungefaehrer RAM-/Plattenbedarf angegeben.
#
# Aufruf im Container (siehe Kommentare am Ende des Dockerfiles):
#   docker run --rm -it -p 127.0.0.1:5000:5000 oprp-bench make help

PYTHON ?= python
TIMEOUT_SECONDS ?= 90
BENCH_OUT_DIR ?= benchmarks/results

.PHONY: help app test verify b1 b2 b3 bench-all clean

help:
	@echo ""
	@echo "OPRP-Algorithmenvergleich -- verfuegbare Targets"
	@echo "==============================================="
	@echo ""
	@echo "make app         Webanwendung starten (interaktive Visualisierung)"
	@echo "                   liest:     app.py, routes/, warehouse/, templates/, static/"
	@echo "                   erzeugt:   nichts auf der Platte"
	@echo "                   Dauer:     laeuft bis zum Abbruch (Strg-C)"
	@echo "                   Speicher:  ca. 100 MB RAM, kein zusaetzlicher Plattenbedarf"
	@echo ""
	@echo "make test        Testsuite ausfuehren (pytest)"
	@echo "                   liest:     tests/, algorithms/, routes/, warehouse/, utils/"
	@echo "                   erzeugt:   .pytest_cache/ (wenige MB)"
	@echo "                   Dauer:     wenige Sekunden (126 Tests in 2,5 s)"
	@echo "                   Speicher:  unter 1 GB RAM, wenige MB Platte"
	@echo ""
	@echo "make verify      Optimalitaet des Fixed-Parameter-Algorithmus pruefen"
	@echo "                   liest:     verify_optimality.py, routes/, warehouse/,"
	@echo "                              tests/routes/test_fixed_parameter_dp.py"
	@echo "                   erzeugt:   nur Konsolenausgabe (182 Instanzen)"
	@echo "                   Dauer:     wenige Sekunden (Referenzlauf: 1,2 s)"
	@echo "                   Speicher:  unter 2 GB RAM, kein zusaetzlicher Plattenbedarf"
	@echo ""
	@echo "make b1          Benchmark B1 -- Lagerbreite 1 bis 10 bei r=1"
	@echo "                   liest:     benchmarks/payloads/b1.json"
	@echo "                   erzeugt:   $(BENCH_OUT_DIR)/b1.csv (3240 Zeilen, ca. 130 KB)"
	@echo "                   Dauer:     unter einer Minute (Referenzlauf: 25 s)"
	@echo "                   Speicher:  unter 1 GB RAM, wenige 100 KB Platte"
	@echo ""
	@echo "make b2          Benchmark B2 -- Regalreihen 1 bis 10 bei Breite 10"
	@echo "                   liest:     benchmarks/payloads/b2.json"
	@echo "                   erzeugt:   $(BENCH_OUT_DIR)/b2.csv (3600 Zeilen, ca. 150 KB)"
	@echo "                   Dauer:     rund 11 Stunden (Referenzlauf: 10,91 h)"
	@echo "                   Speicher:  bis 12 GB RAM (hartes Limit je Solverprozess),"
	@echo "                              wenige 100 KB Platte"
	@echo ""
	@echo "make b3          Benchmark B3 -- quadratische Layouts 1x1 bis 10x10"
	@echo "                   liest:     benchmarks/payloads/b3.json"
	@echo "                   erzeugt:   $(BENCH_OUT_DIR)/b3.csv (3360 Zeilen, ca. 140 KB)"
	@echo "                   Dauer:     rund 10 Stunden"
	@echo "                   Speicher:  bis 12 GB RAM (hartes Limit je Solverprozess),"
	@echo "                              wenige 100 KB Platte"
	@echo ""
	@echo "make bench-all   B1, B2 und B3 hintereinander"
	@echo "                   liest:     benchmarks/payloads/b1.json, b2.json, b3.json"
	@echo "                   erzeugt:   $(BENCH_OUT_DIR)/b1.csv, b2.csv, b3.csv"
	@echo "                   Dauer:     rund 21 Stunden"
	@echo "                   Speicher:  bis 12 GB RAM, unter 1 MB Platte"
	@echo ""
	@echo "make clean       Zwischenprodukte loeschen (KEINE Benchmarkergebnisse)"
	@echo "                   liest:     nichts"
	@echo "                   erzeugt:   nichts; entfernt __pycache__/ und .pytest_cache/"
	@echo "                   Dauer:     Sekunden"
	@echo "                   Speicher:  vernachlaessigbar"
	@echo ""
	@echo "Hinweise"
	@echo "--------"
	@echo "* Die Benchmarks haengen an eine vorhandene CSV an, statt sie zu"
	@echo "  ueberschreiben. Ein Abbruch kostet nur die angebrochene Stufe."
	@echo "* Ausgabeverzeichnis umlenken: make b1 BENCH_OUT_DIR=/data/results"
	@echo "  Fuer grosse Laeufe ein eigenes Volume mounten (siehe Dockerfile)."
	@echo "* Timeout je Solveraufruf: $(TIMEOUT_SECONDS) s, gesetzt in den Payloads."
	@echo "  Die in der Arbeit berichteten Werte entstanden mit genau diesem Wert."
	@echo ""

app:
	flask --app app run --host 0.0.0.0 --port 5000

test:
	$(PYTHON) -m pytest tests/ -q

verify:
	$(PYTHON) verify_optimality.py

b1:
	BENCH_OUT_DIR=$(BENCH_OUT_DIR) $(PYTHON) bench_night_runner.py b1

b2:
	BENCH_OUT_DIR=$(BENCH_OUT_DIR) $(PYTHON) bench_night_runner.py b2

b3:
	BENCH_OUT_DIR=$(BENCH_OUT_DIR) $(PYTHON) bench_night_runner.py b3

bench-all: b1 b2 b3

clean:
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
	rm -rf .pytest_cache
