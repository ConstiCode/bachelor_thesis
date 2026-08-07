# Reproduzierbare Benchmark-Umgebung für die OPRP-Webapp (Bachelorarbeit).
# Build:  docker build -t oprp-bench .
# Run:    docker run --rm -p 127.0.0.1:5000:5000 oprp-bench
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# --host 0.0.0.0 nötig, damit der Port aus dem Container heraus erreichbar ist
CMD ["flask", "--app", "app", "run", "--host", "0.0.0.0", "--port", "5000"]
