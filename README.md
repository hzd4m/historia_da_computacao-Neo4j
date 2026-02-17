# GraphRAG - História da Computação

Infraestrutura completa para um motor de GraphRAG sobre a História da Computação.

## Stack
- Neo4j 5 (com plugins apoc e gds)
- FastAPI
- Ollama Cloud (modelo gpt-oss:120b)
- Docker

## Execução

1. Configure a variável de ambiente `OLLAMA_API_KEY` com seu token da Ollama Cloud.
2. Execute:

```
docker compose up --build
```

A API estará disponível em http://localhost:8000 e o Neo4j em http://localhost:7474.

## Endpoints
- `/search`: Busca híbrida (vetorial + Cypher + LLM)
- `/timeline`: Eventos ordenados cronologicamente

## Documentação
Toda documentação e logs estão em PT-BR.

---

*Projeto modular, tipado e pronto para produção.*
