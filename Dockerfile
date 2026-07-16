FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

# Installa Git (necessario per pip install da repo Git) e pip aggiornato
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    python3-pip \
    python3-cffi \
    python3-brotli \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y --auto-remove \
    && rm -rf /var/lib/apt/lists/*

# Copia il codice dell'app Flask
COPY app/ ./app
WORKDIR /app/app

EXPOSE 5000

CMD ["gunicorn", "--workers", "4", "--timeout", "120", "--bind", "0.0.0.0:5000", "main:app"]
