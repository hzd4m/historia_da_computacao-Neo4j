FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copia os scripts da aplicação
COPY scripts /app/scripts

ENV PYTHONUNBUFFERED=1

# Comando default: executa ingestão e sobe o servidor FastAPI
CMD ["bash", "-c", "python /app/scripts/ingest.py && uvicorn scripts.start_api:app --host 0.0.0.0 --port 8000"]
