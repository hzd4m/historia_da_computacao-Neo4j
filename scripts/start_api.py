"""
API Backend - GraphRAG
Busca híbrida (vetorial + travessia de grafo + síntese via LLM).
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List

import httpx
from fastapi import FastAPI, HTTPException
from neo4j import Driver, GraphDatabase
from pydantic import BaseModel, Field

from neo4j_graphrag.embeddings import OllamaEmbeddings


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("start-api")

app = FastAPI(
    title="GraphRAG - História da Computação",
    description="API para busca híbrida e linhagem tecnológica no grafo.",
    version="2.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", os.getenv("NEO4J_AUTH", "neo4j/password").split("/", 1)[-1])
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
OLLAMA_HOST = os.getenv("OLLAMA_REMOTE_URL", "https://ollama.com").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:120b")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "120"))

SEARCH_TOP_K = int(os.getenv("SEARCH_TOP_K", "8"))
SEARCH_SCORE_THRESHOLD = float(os.getenv("SEARCH_SCORE_THRESHOLD", "0.7"))
LINEAGE_MAX_DEPTH = int(os.getenv("LINEAGE_MAX_DEPTH", "4"))
LINEAGE_MAX_PATHS_PER_NODE = int(os.getenv("LINEAGE_MAX_PATHS_PER_NODE", "3"))

OLLAMA_HEADERS = {"Authorization": "Bearer " + (OLLAMA_API_KEY or "")}

# Camada vetorial usa similaridade de cosseno:
# S_c(A, B) = (A · B) / (||A|| ||B||)
EMBEDDER = OllamaEmbeddings(
    model=OLLAMA_MODEL,
    host=OLLAMA_HOST,
    headers=OLLAMA_HEADERS,
    timeout=OLLAMA_TIMEOUT,
)

NEO4J_DRIVER: Driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD),
)


class SearchRequest(BaseModel):
    query: str = Field(min_length=3, description="Pergunta do usuário")


class SearchResponse(BaseModel):
    answer: str
    sources: List[str]
    lineage: List[str]


class TimelineEvent(BaseModel):
    uid: str
    ano: int | None = None
    titulo: str
    descricao: str | None = None
    tecnologia_base: str | None = None
    potencia_kw: float | None = None


def _node_display_name(node_map: Dict[str, Any]) -> str:
    return (
        str(
            node_map.get("titulo")
            or node_map.get("nome")
            or node_map.get("uid")
            or node_map.get("element_id")
            or "Nó sem nome"
        )
    )


def _node_year(node_map: Dict[str, Any]) -> int | None:
    raw = node_map.get("ano")
    if raw is None:
        raw = node_map.get("ano_proposta")
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _format_node_with_year(node_map: Dict[str, Any]) -> str:
    name = _node_display_name(node_map)
    year = _node_year(node_map)
    if year is None:
        return name
    return f"{name} ({year})"


def _vector_search(embedding: List[float], top_k: int) -> List[Dict[str, Any]]:
    index_names = ("teoria_embedding_idx", "evento_embedding_idx")
    results: List[Dict[str, Any]] = []

    query = """
    CALL db.index.vector.queryNodes($index_name, $k, $embedding)
    YIELD node, score
    RETURN elementId(node) AS element_id,
           labels(node) AS labels,
           score AS score,
           node.nome AS nome,
           node.titulo AS titulo,
           node.uid AS uid,
           node.ano AS ano,
           node.ano_proposta AS ano_proposta,
           node.descricao AS descricao,
           node.impacto AS impacto,
           node.problema_resolvido AS problema_resolvido,
           node.tecnologia_base AS tecnologia_base
    """

    with NEO4J_DRIVER.session(database=NEO4J_DATABASE) as session:
        for index_name in index_names:
            try:
                rows = session.run(
                    query,
                    index_name=index_name,
                    k=top_k,
                    embedding=embedding,
                ).data()
                results.extend(rows)
            except Exception as exc:
                logger.warning("Falha ao consultar índice vetorial '%s': %s", index_name, exc)

    dedup: Dict[str, Dict[str, Any]] = {}
    for item in results:
        key = item["element_id"]
        if key not in dedup or float(item["score"]) > float(dedup[key]["score"]):
            dedup[key] = item

    ranked = sorted(dedup.values(), key=lambda x: float(x["score"]), reverse=True)
    return ranked


def _extract_lineage(element_id: str) -> List[str]:
    query = f"""
    MATCH (n)
    WHERE elementId(n) = $element_id
    OPTIONAL MATCH p=(n)-[:FEZ|INFLUENCIA|FUNDAMENTA*1..{LINEAGE_MAX_DEPTH}]-(ancestor)
    WITH p
    WHERE p IS NOT NULL
    RETURN [node IN nodes(p) | {{
        nome: coalesce(node.titulo, node.nome, node.uid),
        ano: coalesce(node.ano, node.ano_proposta)
    }}] AS cadeia
    ORDER BY length(p) DESC
    LIMIT $max_paths
    """
    chains: List[str] = []
    with NEO4J_DRIVER.session(database=NEO4J_DATABASE) as session:
        rows = session.run(query, element_id=element_id, max_paths=LINEAGE_MAX_PATHS_PER_NODE).data()
    for row in rows:
        raw_chain = row.get("cadeia") or []
        parts: List[str] = []
        for node_item in raw_chain:
            name = str(node_item.get("nome") or "Nó sem nome")
            year = node_item.get("ano")
            if year is None:
                parts.append(name)
            else:
                parts.append(f"{name} ({year})")
        if parts:
            chains.append(" -> ".join(parts))
    if not chains:
        with NEO4J_DRIVER.session(database=NEO4J_DATABASE) as session:
            row = session.run(
                """
                MATCH (n)
                WHERE elementId(n) = $element_id
                RETURN coalesce(n.titulo, n.nome, n.uid) AS nome, coalesce(n.ano, n.ano_proposta) AS ano
                """,
                element_id=element_id,
            ).single()
        if row:
            name = str(row.get("nome") or "Nó sem nome")
            year = row.get("ano")
            chains.append(f"{name} ({year})" if year is not None else name)
    return chains


def _build_context_payload(candidates: List[Dict[str, Any]], lineage: List[str]) -> str:
    lines: List[str] = []
    for idx, node in enumerate(candidates, start=1):
        lines.append(
            (
                f"[Fonte {idx}] nome={_node_display_name(node)} | "
                f"labels={node.get('labels')} | "
                f"score={float(node.get('score', 0.0)):.4f} | "
                f"ano={_node_year(node)} | "
                f"descricao={node.get('descricao') or node.get('impacto') or node.get('problema_resolvido') or 'N/A'}"
            )
        )

    if lineage:
        lines.append("Linhagens identificadas:")
        for item in lineage:
            lines.append(f"- {item}")

    return "\n".join(lines)


def _ensure_graph_citations(answer: str, sources: List[str], lineage: List[str]) -> str:
    if not sources:
        return answer

    citation_lines = ["Marcos citados do grafo:"]
    for src in sources[:8]:
        citation_lines.append(f"- {src}")
    if lineage:
        citation_lines.append("Linhagens usadas na síntese:")
        for item in lineage[:6]:
            citation_lines.append(f"- {item}")

    citation_block = "\n".join(citation_lines)
    if "Marcos citados do grafo:" in answer:
        return answer
    return f"{answer}\n\n{citation_block}"


async def _synthesize_answer(query_text: str, context_payload: str) -> str:
    if not OLLAMA_API_KEY:
        raise HTTPException(status_code=503, detail="OLLAMA_API_KEY não configurada.")

    prompt = (
        "Você é um historiador da tecnologia e arquiteto de software. "
        "Responda em PT-BR com precisão factual e narrativa clara. "
        "Cite explicitamente os marcos e anos. "
        "Inclua frases como 'Conforme documentado em 1679 por Leibniz...' quando aplicável. "
        "Se o contexto for insuficiente, diga isso claramente.\n\n"
        f"Pergunta do usuário:\n{query_text}\n\n"
        f"Contexto do grafo (fontes e relações):\n{context_payload}\n"
    )

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Você sintetiza respostas históricas com foco em linhagem tecnológica. "
                    "Não invente fatos fora das fontes recebidas."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "think": True,
        "options": {
            "num_ctx": 128000,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(40.0, read=180.0)) as client:
            resp = await client.post(
                f"{OLLAMA_HOST}/api/chat",
                headers={**OLLAMA_HEADERS, "Content-Type": "application/json"},
                json=payload,
            )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Falha de rede ao acessar Ollama Cloud: {exc}",
        ) from exc

    if resp.status_code in (401, 403):
        raise HTTPException(
            status_code=resp.status_code,
            detail="Falha de autenticação no Ollama Cloud.",
        )
    if resp.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=f"Erro do Ollama Cloud (HTTP {resp.status_code}): {resp.text[:500]}",
        )

    data = resp.json()
    message = data.get("message") if isinstance(data, dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if not content:
        raise HTTPException(status_code=502, detail="Resposta inválida do Ollama Cloud.")
    return str(content).strip()


@app.on_event("startup")
def on_startup() -> None:
    try:
        NEO4J_DRIVER.verify_connectivity()
        logger.info("Conexão com Neo4j validada.")
    except Exception as exc:
        logger.error("Falha na conexão com Neo4j: %s", exc)


@app.on_event("shutdown")
def on_shutdown() -> None:
    NEO4J_DRIVER.close()


@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest) -> SearchResponse:
    logger.info("Recebida query /search: %s", request.query)

    if not OLLAMA_API_KEY:
        raise HTTPException(status_code=503, detail="OLLAMA_API_KEY não configurada.")

    try:
        query_embedding = EMBEDDER.embed_query(request.query)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Falha ao gerar embedding da query via Ollama Cloud: {exc}",
        ) from exc

    candidates = _vector_search(query_embedding, SEARCH_TOP_K)
    qualified = [item for item in candidates if float(item.get("score", 0.0)) >= SEARCH_SCORE_THRESHOLD]

    if not qualified:
        return SearchResponse(
            answer=(
                "Não possuo contexto histórico suficiente para responder com precisão. "
                "Nenhum nó com similaridade acima de 0.7 foi encontrado no grafo."
            ),
            sources=[],
            lineage=[],
        )

    lineage: List[str] = []
    for node in qualified:
        lineage.extend(_extract_lineage(node["element_id"]))
    lineage = list(dict.fromkeys(lineage))

    sources = list(
        dict.fromkeys(
            [_format_node_with_year(node) for node in qualified]
        )
    )

    context_payload = _build_context_payload(qualified, lineage)
    answer = await _synthesize_answer(request.query, context_payload)
    answer = _ensure_graph_citations(answer, sources, lineage)
    return SearchResponse(answer=answer, sources=sources, lineage=lineage)


@app.get("/timeline", response_model=List[TimelineEvent])
def timeline() -> List[TimelineEvent]:
    query = """
    MATCH (e:Evento)
    RETURN e.uid AS uid,
           e.ano AS ano,
           e.titulo AS titulo,
           e.descricao AS descricao,
           e.tecnologia_base AS tecnologia_base,
           e.potencia_kw AS potencia_kw
    ORDER BY e.ano ASC
    """
    with NEO4J_DRIVER.session(database=NEO4J_DATABASE) as session:
        rows = session.run(query).data()
    return [TimelineEvent(**row) for row in rows]
