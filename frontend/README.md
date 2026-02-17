# Frontend de Visualização do Grafo

Dashboard React + Cytoscape para visualizar a linhagem histórica da computação.

## Requisitos
- Node.js 20+
- API FastAPI disponível (ex: `http://localhost:8000`)

## Configuração
```bash
cd frontend
npm install
```

Crie `.env` opcional para apontar para outra API:
```bash
VITE_API_BASE_URL=http://localhost:8000
```

## Execução
```bash
npm run dev
```

## Build
```bash
npm run build
```

## Endpoints consumidos
- `POST /search`
- `GET /graph/{uid}`
