"""
ETL de marcos históricos da computação para Neo4j 5.

O script realiza:
1. Carga idempotente (MERGE) dos CSVs em nós e relacionamentos.
2. Enriquecimento opcional com SimpleKGPipeline (neo4j-graphrag).
3. Geração de embeddings para Evento e Teoria via Ollama Cloud.
4. Criação de índices vetoriais para busca semântica.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
from neo4j import Driver, GraphDatabase

from neo4j_graphrag.embeddings import OllamaEmbeddings
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.llm.ollama_llm import OllamaLLM


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("ingest-etl")

PROJECT_ROOT = Path(__file__).resolve().parents[1]

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", os.getenv("NEO4J_AUTH", "neo4j/password").split("/", 1)[-1])
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
OLLAMA_HOST = os.getenv("OLLAMA_REMOTE_URL", "https://ollama.com")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:120b")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "120"))

# Header obrigatório para autenticar no Ollama Cloud.
OLLAMA_HEADERS = {"Authorization": "Bearer " + (OLLAMA_API_KEY or "")}

REL_TYPE_PATTERN = re.compile(r"^[A-Z_][A-Z0-9_]*$")


def parse_optional_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.upper() == "NULL":
        return None
    return int(float(text))


def parse_optional_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.upper() == "NULL":
        return None
    return float(text)


def normalize_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.upper() == "NULL":
        return None
    return text


def resolve_csv_path(candidates: list[str]) -> Path:
    for candidate in candidates:
        path = PROJECT_ROOT / candidate
        if path.exists():
            return path
    raise FileNotFoundError(f"Nenhum arquivo encontrado entre: {candidates}")


def load_csv(candidates: list[str]) -> pd.DataFrame:
    csv_path = resolve_csv_path(candidates)
    logger.info("Lendo CSV: %s", csv_path)
    return pd.read_csv(csv_path, dtype=str, keep_default_na=False).fillna("")


def connect_neo4j() -> Driver:
    logger.info("Conectando ao Neo4j em %s (database=%s)", NEO4J_URI, NEO4J_DATABASE)
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    driver.verify_connectivity()
    logger.info("Conexão com Neo4j validada com sucesso.")
    return driver


def merge_nodes(driver: Driver, label: str, rows: list[Dict[str, Any]], merge_key: str) -> None:
    query = f"""
    UNWIND $rows AS row
    MERGE (n:{label} {{{merge_key}: row.{merge_key}}})
    SET n += row
    """
    with driver.session(database=NEO4J_DATABASE) as session:
        session.run(query, rows=rows).consume()


def load_persons(driver: Driver, df: pd.DataFrame) -> None:
    rows: list[Dict[str, Any]] = []
    for _, row in df.iterrows():
        rows.append(
            {
                "nome": normalize_text(row.get("nome")),
                "nacionalidade": normalize_text(row.get("nacionalidade")),
                "contribuicao_chave": normalize_text(row.get("contribuicao_chave")),
                "bio": normalize_text(row.get("bio")),
            }
        )
    rows = [item for item in rows if item["nome"]]
    logger.info("Carregando %d nós de Pessoa...", len(rows))
    merge_nodes(driver, "Pessoa", rows, "nome")


def load_theories(driver: Driver, df: pd.DataFrame) -> None:
    rows: list[Dict[str, Any]] = []
    for _, row in df.iterrows():
        rows.append(
            {
                "nome": normalize_text(row.get("nome")),
                "ano_proposta": parse_optional_int(row.get("ano_proposta")),
                "paper": normalize_text(row.get("paper")),
                "problema_resolvido": normalize_text(row.get("problema_resolvido")),
                "impacto": normalize_text(row.get("impacto")),
            }
        )
    rows = [item for item in rows if item["nome"]]
    logger.info("Carregando %d nós de Teoria...", len(rows))
    merge_nodes(driver, "Teoria", rows, "nome")


def load_techs(driver: Driver, df: pd.DataFrame) -> None:
    rows: list[Dict[str, Any]] = []
    for _, row in df.iterrows():
        rows.append(
            {
                "nome": normalize_text(row.get("nome")),
                "tipo": normalize_text(row.get("tipo")),
                "ano": parse_optional_int(row.get("ano")),
                "material": normalize_text(row.get("material")),
                "impacto": normalize_text(row.get("impacto")),
            }
        )
    rows = [item for item in rows if item["nome"]]
    logger.info("Carregando %d nós de Tecnologia...", len(rows))
    merge_nodes(driver, "Tecnologia", rows, "nome")


def load_events(driver: Driver, df: pd.DataFrame) -> None:
    rows: list[Dict[str, Any]] = []
    for _, row in df.iterrows():
        uid = normalize_text(row.get("uid"))
        titulo = normalize_text(row.get("titulo"))
        rows.append(
            {
                "uid": uid,
                "nome": titulo,  # permite relacionar por nome/título em relationships.csv
                "ano": parse_optional_int(row.get("ano")),
                "titulo": titulo,
                "descricao": normalize_text(row.get("descricao")),
                "fonte": normalize_text(row.get("fonte")),
                "tecnologia_base": normalize_text(row.get("tecnologia_base")),
                "potencia_kw": parse_optional_float(row.get("potencia_kw")),
            }
        )
    rows = [item for item in rows if item["uid"]]
    logger.info("Carregando %d nós de Evento...", len(rows))
    merge_nodes(driver, "Evento", rows, "uid")


def ensure_named_node(driver: Driver, name: str) -> None:
    query = "MERGE (:Entidade {nome: $name})"
    with driver.session(database=NEO4J_DATABASE) as session:
        session.run(query, name=name).consume()


def merge_named_relationship(driver: Driver, from_id: str, to_id: str, rel_type: str, motivo: Optional[str]) -> None:
    rel = rel_type.strip().upper()
    if not REL_TYPE_PATTERN.match(rel):
        logger.warning("Tipo de relacionamento inválido e ignorado: %s", rel_type)
        return

    ensure_named_node(driver, from_id)
    ensure_named_node(driver, to_id)

    query = f"""
    MATCH (a {{nome: $from_id}})
    WITH a
    ORDER BY CASE WHEN a:Entidade THEN 1 ELSE 0 END
    LIMIT 1
    MATCH (b {{nome: $to_id}})
    WITH a, b
    ORDER BY CASE WHEN b:Entidade THEN 1 ELSE 0 END
    LIMIT 1
    MERGE (a)-[r:{rel}]->(b)
    SET r.prop_motivo = $motivo
    """
    with driver.session(database=NEO4J_DATABASE) as session:
        session.run(query, from_id=from_id, to_id=to_id, motivo=motivo).consume()


def load_relationships(driver: Driver, df: pd.DataFrame) -> None:
    logger.info("Carregando %d relacionamentos do CSV...", len(df))
    for _, row in df.iterrows():
        from_id = normalize_text(row.get("from_id"))
        to_id = normalize_text(row.get("to_id"))
        rel_type = normalize_text(row.get("rel_type"))
        motivo = normalize_text(row.get("prop_motivo"))

        if not from_id or not to_id or not rel_type:
            logger.warning("Relacionamento inválido ignorado: %s", dict(row))
            continue
        merge_named_relationship(driver, from_id, to_id, rel_type, motivo)


def load_priority_newton_babbage(driver: Driver) -> None:
    logger.info("Priorizando relação Newton -> Babbage para teste de RAG...")
    query = """
    MATCH (n:Pessoa {nome: 'Isaac Newton'})
    MATCH (b:Pessoa {nome: 'Charles Babbage'})
    MERGE (n)-[r:INFLUENCIA]->(b)
    SET r.prop_motivo = 'Mecanização da Aritmética'
    """
    with driver.session(database=NEO4J_DATABASE) as session:
        session.run(query).consume()


def init_ollama_components() -> tuple[Optional[OllamaEmbeddings], Optional[OllamaLLM], Optional[int]]:
    if not OLLAMA_API_KEY:
        logger.error("OLLAMA_API_KEY não definida no ambiente.")
        return None, None, None

    try:
        logger.info("Inicializando OllamaEmbeddings no host remoto %s...", OLLAMA_HOST)
        embedder = OllamaEmbeddings(
            model=OLLAMA_MODEL,
            host=OLLAMA_HOST,
            headers=OLLAMA_HEADERS,
            timeout=OLLAMA_TIMEOUT,
        )

        logger.info("Inicializando OllamaLLM no host remoto %s...", OLLAMA_HOST)
        llm = OllamaLLM(
            model_name=OLLAMA_MODEL,
            host=OLLAMA_HOST,
            headers=OLLAMA_HEADERS,
            timeout=OLLAMA_TIMEOUT,
        )

        logger.info("Validando autenticação no Ollama Cloud via /api/chat...")
        llm.invoke("Responda somente OK.")

        logger.info("Validando geração de embedding no Ollama Cloud...")
        probe_vector = embedder.embed_query("Teste curto de conectividade para embeddings.")
        emb_dim = len(probe_vector)
        logger.info("Embedding validado com dimensão %d.", emb_dim)
        return embedder, llm, emb_dim
    except Exception as exc:
        logger.exception("Falha ao conectar ao Ollama Cloud: %s", exc)
        return None, None, None


async def run_simple_kg_pipeline(
    driver: Driver,
    llm: OllamaLLM,
    embedder: OllamaEmbeddings,
) -> None:
    logger.info("Executando SimpleKGPipeline para enriquecimento automático...")
    pipeline = SimpleKGPipeline(
        llm=llm,
        driver=driver,
        embedder=embedder,
        from_pdf=False,
        schema="FREE",
        on_error="IGNORE",
        perform_entity_resolution=True,
        neo4j_database=NEO4J_DATABASE,
    )

    seed_text = (
        "Isaac Newton consolidou métodos de diferenças finitas. "
        "Charles Babbage aplicou esse fundamento na mecanização da aritmética "
        "na Difference Engine."
    )
    await pipeline.run_async(
        text=seed_text,
        document_metadata={"source": "seed-etl", "idioma": "pt-BR"},
    )
    logger.info("SimpleKGPipeline finalizado com sucesso.")


def generate_embeddings(driver: Driver, embedder: OllamaEmbeddings) -> None:
    # A recuperação vetorial no RAG usará similaridade de cosseno:
    # $S_c(A, B) = \frac{A \cdot B}{\|A\| \|B\|}$
    logger.info("Gerando embeddings para nós Teoria...")
    with driver.session(database=NEO4J_DATABASE) as session:
        theories = session.run(
            """
            MATCH (t:Teoria)
            RETURN t.nome AS nome, t.paper AS paper, t.problema_resolvido AS problema, t.impacto AS impacto
            """
        ).data()

        for row in theories:
            nome = row.get("nome")
            text = " | ".join(
                [
                    str(nome or ""),
                    str(row.get("paper") or ""),
                    str(row.get("problema") or ""),
                    str(row.get("impacto") or ""),
                ]
            )
            logger.info("Gerando embeddings para Teoria '%s'...", nome)
            try:
                vector = embedder.embed_query(text)
                session.run(
                    "MATCH (t:Teoria {nome: $nome}) SET t.embedding = $embedding",
                    nome=nome,
                    embedding=vector,
                ).consume()
            except Exception as exc:
                logger.exception("Falha ao gerar embedding da Teoria '%s': %s", nome, exc)

        logger.info("Gerando embeddings para nós Evento...")
        events = session.run(
            """
            MATCH (e:Evento)
            RETURN e.uid AS uid, e.titulo AS titulo, e.descricao AS descricao, e.tecnologia_base AS tecnologia_base
            """
        ).data()

        for row in events:
            uid = row.get("uid")
            titulo = row.get("titulo")
            text = " | ".join(
                [
                    str(titulo or ""),
                    str(row.get("descricao") or ""),
                    str(row.get("tecnologia_base") or ""),
                ]
            )
            logger.info("Gerando embeddings para Evento '%s'...", titulo or uid)
            try:
                vector = embedder.embed_query(text)
                session.run(
                    "MATCH (e:Evento {uid: $uid}) SET e.embedding = $embedding",
                    uid=uid,
                    embedding=vector,
                ).consume()
            except Exception as exc:
                logger.exception("Falha ao gerar embedding do Evento '%s': %s", titulo or uid, exc)


def create_vector_indexes(driver: Driver, emb_dim: Optional[int]) -> None:
    logger.info("Criando índices vetoriais para Teoria.embedding e Evento.embedding...")
    if emb_dim:
        idx_teoria = (
            "CREATE VECTOR INDEX teoria_embedding_idx IF NOT EXISTS "
            "FOR (n:Teoria) ON (n.embedding) "
            f"OPTIONS {{indexConfig: {{`vector.dimensions`: {emb_dim}, `vector.similarity_function`: 'cosine'}}}}"
        )
        idx_evento = (
            "CREATE VECTOR INDEX evento_embedding_idx IF NOT EXISTS "
            "FOR (n:Evento) ON (n.embedding) "
            f"OPTIONS {{indexConfig: {{`vector.dimensions`: {emb_dim}, `vector.similarity_function`: 'cosine'}}}}"
        )
    else:
        idx_teoria = (
            "CREATE VECTOR INDEX teoria_embedding_idx IF NOT EXISTS "
            "FOR (n:Teoria) ON (n.embedding) "
            "OPTIONS {indexConfig: {`vector.similarity_function`: 'cosine'}}"
        )
        idx_evento = (
            "CREATE VECTOR INDEX evento_embedding_idx IF NOT EXISTS "
            "FOR (n:Evento) ON (n.embedding) "
            "OPTIONS {indexConfig: {`vector.similarity_function`: 'cosine'}}"
        )

    with driver.session(database=NEO4J_DATABASE) as session:
        session.run(idx_teoria).consume()
        session.run(idx_evento).consume()
    logger.info("Índices vetoriais garantidos com sucesso.")


def main() -> None:
    logger.info("Iniciando ETL histórico para Graph Data Computer...")

    persons_df = load_csv(["nodes_persons/nodes_persons.csv", "nodes_persons.csv"])
    theories_df = load_csv(["nodes_theories/nodes_theories.csv", "nodes_theories.csv"])
    techs_df = load_csv(["nodes_techs/nodes_techs.csv", "nodes_techs.csv"])
    events_df = load_csv(["nodes_events/nodes_events.csv", "nodes_events.csv"])
    rels_df = load_csv(["relationships.csv"])

    driver = connect_neo4j()
    try:
        load_persons(driver, persons_df)
        load_theories(driver, theories_df)
        load_techs(driver, techs_df)
        load_events(driver, events_df)

        load_priority_newton_babbage(driver)
        load_relationships(driver, rels_df)

        embedder, llm, emb_dim = init_ollama_components()
        if embedder and llm:
            try:
                asyncio.run(run_simple_kg_pipeline(driver, llm, embedder))
            except Exception as exc:
                logger.exception("Falha no SimpleKGPipeline: %s", exc)

            generate_embeddings(driver, embedder)
        else:
            logger.warning(
                "Embeddings/Pipeline desativados por falha de conexão no Ollama Cloud. "
                "A carga estrutural do grafo foi concluída."
            )
            emb_dim = None

        create_vector_indexes(driver, emb_dim)
    finally:
        driver.close()
        logger.info("Conexão Neo4j encerrada.")

    logger.info("Ingestão concluída com sucesso.")


if __name__ == "__main__":
    main()
