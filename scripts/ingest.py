"""
Script de Ingestão - GraphRAG
Infraestrutura: Neo4j 5, Ollama Cloud, SimpleKGPipeline

Este script realiza a ingestão de dados históricos da computação em Neo4j, gera embeddings vetoriais para nós de Evento e Teoria usando Ollama Cloud, e documenta a similaridade de cosseno:

$S_c(A, B) = \frac{A \cdot B}{\|A\| \|B\|}$

Logs e comentários em PT-BR.
"""

import os
from typing import List, Dict, Any
import pandas as pd
from neo4j_graphrag.pipeline import SimpleKGPipeline
from neo4j_graphrag.embeddings import OllamaEmbeddings

# Configuração do Ollama Cloud
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
OLLAMA_HOST = "https://ollama.com"
OLLAMA_MODEL = "gpt-oss:120b"

# Cliente de embeddings
ollama_embeddings = OllamaEmbeddings(
    api_key=OLLAMA_API_KEY,
    host=OLLAMA_HOST,
    model=OLLAMA_MODEL
)

# Função para ler CSVs

def load_csv(file_path: str) -> pd.DataFrame:
    return pd.read_csv(file_path)

# Carregar dados
nodes_persons = load_csv("nodes_persons.csv")
nodes_theories = load_csv("nodes_theories.csv")
nodes_techs = load_csv("nodes_techs.csv")
nodes_events = load_csv("nodes_events.csv")
relationships = load_csv("relationships.csv")

# Pipeline de ingestão
pipeline = SimpleKGPipeline(
    neo4j_uri=os.getenv("NEO4J_URI", "bolt://neo4j:7687"),
    neo4j_user=os.getenv("NEO4J_USER", "neo4j"),
    neo4j_password=os.getenv("NEO4J_PASSWORD", "password"),
    embeddings=ollama_embeddings
)

# Ingestão dos nós
pipeline.ingest_nodes("Pessoa", nodes_persons.to_dict(orient="records"))
pipeline.ingest_nodes("Teoria", nodes_theories.to_dict(orient="records"))
pipeline.ingest_nodes("Tecnologia", nodes_techs.to_dict(orient="records"))
pipeline.ingest_nodes("Evento", nodes_events.to_dict(orient="records"))

# Ingestão dos relacionamentos
pipeline.ingest_relationships(relationships.to_dict(orient="records"))

# Indexação vetorial
pipeline.create_vector_index("Evento", "embedding")
pipeline.create_vector_index("Teoria", "embedding")

print("Ingestão concluída com sucesso.")