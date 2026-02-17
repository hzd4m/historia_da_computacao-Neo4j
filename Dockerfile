FROM node:22-slim AS frontend-builder

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY scripts /app/scripts
COPY nodes_persons /app/nodes_persons
COPY nodes_theories /app/nodes_theories
COPY nodes_techs /app/nodes_techs
COPY nodes_events /app/nodes_events
COPY relationships.csv /app/relationships.csv
COPY --from=frontend-builder /frontend/dist /app/frontend_dist

ENV PYTHONUNBUFFERED=1

CMD ["bash", "-c", "python /app/scripts/ingest.py && uvicorn scripts.start_api:app --host 0.0.0.0 --port 8000"]
