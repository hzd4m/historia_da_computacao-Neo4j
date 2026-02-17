"""
API Backend - GraphRAG
Infraestrutura: FastAPI, Neo4j, Ollama Cloud

Endpoints:
- /search: Busca híbrida (vetorial + Cypher + LLM)
- /timeline: Eventos ordenados cronologicamente

Logs e documentação em PT-BR.
"""

from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Dict, Any
import os
from neo4j_graphrag.pipeline import SimpleKGPipeline
from neo4j_graphrag.embeddings import OllamaEmbeddings

app = FastAPI(title="GraphRAG - História da Computação", description="API para busca híbrida e timeline histórica.", version="1.0", docs_url="/docs", redoc_url="/redoc")

# Configuração do Ollama Cloud
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
OLLAMA_HOST = "https://ollama.com"
OLLAMA_MODEL = "gpt-oss:120b"

ollama_embeddings = OllamaEmbeddings(
    api_key=OLLAMA_API_KEY,
    host=OLLAMA_HOST,
    model=OLLAMA_MODEL
)

pipeline = SimpleKGPipeline(
    neo4j_uri=os.getenv("NEO4J_URI", "bolt://neo4j:7687"),
    neo4j_user=os.getenv("NEO4J_USER", "neo4j"),
    neo4j_password=os.getenv("NEO4J_PASSWORD", "password"),
    embeddings=ollama_embeddings
)

class SearchRequest(BaseModel):
    query: str

class TimelineEvent(BaseModel):
    nome: str
    ano: int
    potencia_kw: float | None = None
    material: str | None = None
    metadados: Dict[str, Any] | None = None

@app.post("/search")
def search(request: SearchRequest) -> Dict[str, Any]:
    """
    Busca híbrida: vetorial + Cypher + LLM
    """
    # Busca vetorial
    vetorial_result = pipeline.vector_search(request.query, node_types=["Evento", "Teoria"])
    # Expansão de grafo
    cypher_result = pipeline.expand_subgraph(request.query)
    # Geração de resposta via LLM
    resposta_llm = pipeline.llm_generate_response(request.query, vetorial_result, cypher_result)
    return {
        "query": request.query,
        "resultados_vetoriais": vetorial_result,
        "subgrafo": cypher_result,
        "resposta_llm": resposta_llm
    }

@app.get("/timeline", response_model=List[TimelineEvent])
def timeline() -> List[TimelineEvent]:
    """
    Retorna eventos ordenados por ano, incluindo potencia_kw e material.
    """
    eventos = pipeline.get_timeline_events()
    return eventos
