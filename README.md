# GraphRAG - Historia da Computacao

Infraestrutura para GraphRAG usando Neo4j + FastAPI + Ollama.

## Stack
- Neo4j 5 + APOC
- FastAPI
- Ollama local + Ollama Cloud via bridge
- Docker Compose

## Configuracao rapida
1. Copie `.env.example` para `.env` e preencha `OLLAMA_API_KEY`.
2. Carregue o ambiente no shell:
   ```bash
   source scripts/load_env.sh
   ```
3. Suba os servicos:
   ```bash
   docker compose up --build
   ```

Endpoints:
- API: `http://localhost:8000`
- Neo4j Browser: `http://localhost:7474`

## Bridge Ollama Cloud
- Script: `scripts/ollama_bridge.py`
- Porta padrao do bridge: `11435` (evita conflito com Ollama local em `11434`)
- Mapeamento remoto configuravel por `OLLAMA_MODEL_MAP_JSON`
- Checagem de modelos remotos via `GET /v1/models`

Exemplo:
```bash
curl -s http://localhost:11435/bridge/config
curl -s http://localhost:11435/v1/models
```

## Neo4j + GDS
- `docker-compose.yml` instala apenas `apoc` automaticamente.
- `graph-data-science` deve ser instalado manualmente em `./neo4j_plugins` com JAR compativel com a versao do Neo4j.

## Permissoes de volumes Neo4j
Descubra o UID/GID do usuario `neo4j` na imagem e ajuste no host:
```bash
docker run --rm --entrypoint id neo4j:5 neo4j
sudo chown -R <uid>:<gid> ./neo4j_data ./neo4j_logs ./neo4j_import ./neo4j_plugins
```

Atalho:
```bash
bash scripts/fix_neo4j_permissions.sh
```

## Seguranca
- `.env` e dados de runtime estao no `.gitignore`.
- Se uma chave tiver vazado, revogue e gere nova em `https://ollama.com/settings/keys`.

## Frontend de Grafo
- Codigo React + Cytoscape em `frontend/`.
- O dashboard consome:
  - `POST /search`
  - `GET /graph/{uid}`

Executar:
```bash
cd frontend
npm install
npm run dev
```

Configurar base da API (opcional):
```bash
cp .env.example .env
# em frontend/.env
VITE_API_BASE_URL=http://localhost:8000
```
