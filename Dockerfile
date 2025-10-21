FROM python:3.11-slim

WORKDIR /app

# Copia i requirements
COPY requirements.txt .

# Installa tutte le dipendenze standard (da PyPI)
RUN pip install --upgrade pip && pip install -r requirements.txt

# Installa la libreria mailer-pz da TestPyPI (senza dipendenze)
RUN pip install --index-url https://test.pypi.org/simple/ --no-deps mailer-pz

# Copia il codice dell'app Flask
COPY app/ ./app
WORKDIR /app/app

EXPOSE 5000

CMD ["python", "main.py"]
