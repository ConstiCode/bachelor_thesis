#!/bin/sh
# Wird bei jedem Containerstart ausgefuehrt und erklaert die naechsten
# Schritte, bevor der eigentliche Befehl laeuft. Reproducibility-Anforderung
# des Lehrstuhls: "There is information on the console on how to proceed
# further."
cat <<'NOTICE'

==============================================================================
 OPRP -- Vergleich heuristischer, approximativer und parametrisierter
 Algorithmen zur Routenoptimierung in der Lagerkommissionierung
 Bachelorarbeit Constantin Dietrich, Lehrstuhl fuer Algorithmen und
 Datenstrukturen, Universitaet Freiburg
==============================================================================

 Wie es weitergeht:

  * Ohne weiteres Argument startet die Webanwendung. Sie ist danach im
    Browser des Hosts unter  http://localhost:5000  erreichbar, sofern der
    Container mit  -p 127.0.0.1:5000:5000  gestartet wurde. Dort lassen sich
    Lagerlayout und Auftrag einstellen und die drei Routen vergleichen.

  * Was sonst moeglich ist, zeigt das Makefile. Es nennt fuer jedes Target
    die gelesenen und erzeugten Dateien, die Laufzeit und den Speicherbedarf:

        docker run --rm oprp-bench make help

  * Die drei Benchmarks der Arbeit reproduzieren (B1 unter einer Minute,
    B2 und B3 je rund 10 bis 11 Stunden):

        docker run --rm -v "$PWD/results:/data" oprp-bench make b1 BENCH_OUT_DIR=/data

  * Testsuite und Optimalitaetsvalidierung:

        docker run --rm oprp-bench make test
        docker run --rm oprp-bench make verify

 Alle Befehle stehen auch als Kommentare am Ende des Dockerfiles
 (cat Dockerfile) und im README.md.

==============================================================================

NOTICE

exec "$@"
