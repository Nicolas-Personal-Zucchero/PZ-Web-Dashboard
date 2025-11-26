FROM python:3.11-slim

WORKDIR /app

# Installa Git (necessario per pip install da repo Git) e pip aggiornato
RUN apt-get update && \
    apt-get install -y git && \
    pip install --upgrade pip && \
    rm -rf /var/lib/apt/lists/*

# Installa tutte le dipendenze standard (da PyPI)
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copia il codice dell'app Flask
COPY app/ ./app
WORKDIR /app/app

EXPOSE 5000

# CMD ["python", "main.py"]
# Sintassi: gunicorn -w [numero_workers] -b [host:port] [file_python]:[variabile_flask]
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "main:app"]
