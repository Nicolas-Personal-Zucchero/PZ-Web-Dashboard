FROM python:3.11-slim

# Creazione utente non privilegiato per sicurezza
#RUN groupadd -g 10000 pzuser && useradd -m -r -u 10000 -g pzuser pzuser

WORKDIR /app

# Installa Git (necessario per pip install da repo Git) e pip aggiornato
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    python3-cffi \
    python3-brotli \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia il codice dell'app Flask
COPY app/ ./app
WORKDIR /app/app

# Assegnazione permessi e switch utente
#RUN chown -R pzuser:pzuser /app
#USER pzuser

EXPOSE 5000

CMD ["gunicorn", "--workers", "4", "--timeout", "120", "--bind", "0.0.0.0:5000", "main:create_app()"]
