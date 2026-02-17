"""
API Backend - GraphRAG
Busca híbrida (vetorial + travessia de grafo + síntese via LLM).
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from neo4j import Driver, GraphDatabase
from pydantic import BaseModel, Field


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("start-api")

app = FastAPI(
    title="GraphRAG - História da Computação",
    description="API para busca híbrida e linhagem tecnológica no grafo.",
    version="3.0",
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

_EMBEDDER = None


def _get_embedder():
    """Inicializa o embedder sob demanda para não bloquear startup sem chave."""
    global _EMBEDDER
    if _EMBEDDER is not None:
        return _EMBEDDER
    try:
        from neo4j_graphrag.embeddings import OllamaEmbeddings
        _EMBEDDER = OllamaEmbeddings(
            model=OLLAMA_MODEL,
            host=OLLAMA_HOST,
            headers=OLLAMA_HEADERS,
            timeout=OLLAMA_TIMEOUT,
        )
    except Exception as exc:
        logger.warning("Falha ao inicializar embedder: %s", exc)
        _EMBEDDER = None
    return _EMBEDDER


NEO4J_DRIVER: Driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD),
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIST_ENV = os.getenv("FRONTEND_DIST_DIR", "").strip()


def _resolve_frontend_dist() -> Path | None:
    candidates: List[Path] = []
    if FRONTEND_DIST_ENV:
        candidates.append(Path(FRONTEND_DIST_ENV))
    candidates.append(PROJECT_ROOT / "frontend_dist")
    candidates.append(PROJECT_ROOT / "frontend" / "dist")

    for candidate in candidates:
        if (candidate / "index.html").exists():
            return candidate
    return None


FRONTEND_DIST = _resolve_frontend_dist()
if FRONTEND_DIST and (FRONTEND_DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="frontend-assets")


# ---------------------------------------------------------------------------
# Modelos Pydantic
# ---------------------------------------------------------------------------

class SearchRequest(BaseModel):
    query: str = Field(min_length=3, description="Pergunta do usuário")


class SearchTiming(BaseModel):
    embedding_ms: Optional[float] = None
    vector_search_ms: Optional[float] = None
    lineage_ms: Optional[float] = None
    synthesis_ms: Optional[float] = None
    total_ms: Optional[float] = None


class SearchResponse(BaseModel):
    answer: str
    sources: List[str]
    lineage: List[str]
    timing: Optional[SearchTiming] = None


class GraphNode(BaseModel):
    id: str
    uid: str | None = None
    nome: str | None = None
    titulo: str | None = None
    ano: int | None = None
    ano_proposta: int | None = None
    descricao: str | None = None
    bio: str | None = None
    impacto: str | None = None
    problema_resolvido: str | None = None
    category: str
    fontes: List[str] = []


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    rel_type: str
    prop_motivo: str | None = None


class GraphResponse(BaseModel):
    uid: str
    root_id: str
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    total_nodes: int
    total_edges: int
    page: int
    page_size: int


class TimelineEvent(BaseModel):
    uid: str
    ano: int | None = None
    titulo: str
    descricao: str | None = None
    tecnologia_base: str | None = None
    potencia_kw: float | None = None


class HealthResponse(BaseModel):
    status: str
    neo4j: str
    node_count: int | None = None
    edge_count: int | None = None
    embeddings_available: bool


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------

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


def _fulltext_fallback_search(query_text: str, top_k: int) -> List[Dict[str, Any]]:
    """Busca por texto quando embeddings não estão disponíveis."""
    cypher = """
    MATCH (n)
    WHERE n.nome IS NOT NULL OR n.titulo IS NOT NULL
    WITH n, labels(n) AS labels,
         CASE
           WHEN toLower(coalesce(n.nome, '')) CONTAINS toLower($query) THEN 1.0
           WHEN toLower(coalesce(n.titulo, '')) CONTAINS toLower($query) THEN 0.9
           WHEN toLower(coalesce(n.descricao, '')) CONTAINS toLower($query) THEN 0.7
           WHEN toLower(coalesce(n.impacto, '')) CONTAINS toLower($query) THEN 0.6
           WHEN toLower(coalesce(n.bio, '')) CONTAINS toLower($query) THEN 0.5
           ELSE 0.0
         END AS score
    WHERE score > 0
    RETURN elementId(n) AS element_id,
           labels(n) AS labels,
           score,
           n.nome AS nome,
           n.titulo AS titulo,
           n.uid AS uid,
           n.ano AS ano,
           n.ano_proposta AS ano_proposta,
           n.descricao AS descricao,
           n.impacto AS impacto,
           n.problema_resolvido AS problema_resolvido,
           n.tecnologia_base AS tecnologia_base
    ORDER BY score DESC
    LIMIT $top_k
    """
    with NEO4J_DRIVER.session(database=NEO4J_DATABASE) as session:
        return session.run(cypher, query=query_text, top_k=top_k).data()


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


def _node_category_from_labels(labels: List[str]) -> str:
    priority = ("Pessoa", "Teoria", "Tecnologia", "Evento")
    for label in priority:
        if label in labels:
            return label
    return labels[0] if labels else "Entidade"


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
        raise HTTPException(status_code=503, detail="OLLAMA_API_KEY não configurada para síntese LLM.")

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


def _build_fallback_answer(candidates: List[Dict[str, Any]], lineage: List[str], query_text: str) -> str:
    """Gera uma resposta estruturada sem LLM, baseada apenas nos dados do grafo."""
    lines: List[str] = [
        f"Resultados encontrados no grafo para: \"{query_text}\"",
        "",
    ]
    for idx, node in enumerate(candidates, start=1):
        name = _node_display_name(node)
        year = _node_year(node)
        desc = node.get("descricao") or node.get("impacto") or node.get("problema_resolvido") or "Sem descrição"
        year_str = f" ({year})" if year else ""
        lines.append(f"{idx}. **{name}{year_str}** — {desc}")

    if lineage:
        lines.append("")
        lines.append("Linhagens identificadas:")
        for chain in lineage[:6]:
            lines.append(f"  - {chain}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Rotas
# ---------------------------------------------------------------------------

@app.get("/")
def root() -> Any:
    if FRONTEND_DIST:
        return FileResponse(FRONTEND_DIST / "index.html")
    return {
        "status": "ok",
        "service": "GraphRAG API",
        "docs": "/docs",
        "healthz": "/healthz",
        "timeline": "/timeline",
        "example_graph": "/graph/Isaac Newton",
        "frontend_hint": "Build frontend e acesse /",
    }


@app.get("/healthz", response_model=HealthResponse)
def healthz() -> HealthResponse:
    """Endpoint consolidado de saúde — verifica Neo4j e disponibilidade de embeddings."""
    neo4j_status = "desconectado"
    node_count = None
    edge_count = None
    try:
        NEO4J_DRIVER.verify_connectivity()
        neo4j_status = "conectado"
        with NEO4J_DRIVER.session(database=NEO4J_DATABASE) as session:
            row = session.run(
                "MATCH (n) RETURN count(n) AS nodes"
            ).single()
            node_count = row["nodes"] if row else 0
            row = session.run(
                "MATCH ()-[r]->() RETURN count(r) AS edges"
            ).single()
            edge_count = row["edges"] if row else 0
    except Exception as exc:
        logger.warning("Healthcheck — falha ao verificar Neo4j: %s", exc)

    embeddings_ok = bool(OLLAMA_API_KEY and _get_embedder() is not None)
    overall = "ok" if neo4j_status == "conectado" else "degradado"

    return HealthResponse(
        status=overall,
        neo4j=neo4j_status,
        node_count=node_count,
        edge_count=edge_count,
        embeddings_available=embeddings_ok,
    )


@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest) -> SearchResponse:
    t_start = time.perf_counter()
    logger.info("Recebida query /search: %s", request.query)

    timing = SearchTiming()
    embedder = _get_embedder()
    candidates: List[Dict[str, Any]] = []

    # Etapa 1: embedding + busca vetorial (com fallback para fulltext)
    if embedder and OLLAMA_API_KEY:
        try:
            t0 = time.perf_counter()
            query_embedding = embedder.embed_query(request.query)
            timing.embedding_ms = round((time.perf_counter() - t0) * 1000, 1)

            t0 = time.perf_counter()
            candidates = _vector_search(query_embedding, SEARCH_TOP_K)
            timing.vector_search_ms = round((time.perf_counter() - t0) * 1000, 1)

            candidates = [item for item in candidates if float(item.get("score", 0.0)) >= SEARCH_SCORE_THRESHOLD]
        except Exception as exc:
            logger.warning("Falha na busca vetorial, usando fallback por texto: %s", exc)
            candidates = []

    if not candidates:
        logger.info("Fallback: busca por texto para query '%s'", request.query)
        candidates = _fulltext_fallback_search(request.query, SEARCH_TOP_K)

    if not candidates:
        timing.total_ms = round((time.perf_counter() - t_start) * 1000, 1)
        return SearchResponse(
            answer=(
                "Não possuo contexto histórico suficiente para responder com precisão. "
                "Nenhum nó relevante foi encontrado no grafo."
            ),
            sources=[],
            lineage=[],
            timing=timing,
        )

    # Etapa 2: extração de linhagem
    t0 = time.perf_counter()
    lineage: List[str] = []
    for node in candidates:
        lineage.extend(_extract_lineage(node["element_id"]))
    lineage = list(dict.fromkeys(lineage))
    timing.lineage_ms = round((time.perf_counter() - t0) * 1000, 1)

    sources = list(
        dict.fromkeys(
            [_format_node_with_year(node) for node in candidates]
        )
    )

    context_payload = _build_context_payload(candidates, lineage)

    # Etapa 3: síntese via LLM (com fallback estruturado)
    if OLLAMA_API_KEY:
        try:
            t0 = time.perf_counter()
            answer = await _synthesize_answer(request.query, context_payload)
            timing.synthesis_ms = round((time.perf_counter() - t0) * 1000, 1)
            answer = _ensure_graph_citations(answer, sources, lineage)
        except Exception as exc:
            logger.warning("Falha na síntese LLM, retornando resposta estruturada: %s", exc)
            answer = _build_fallback_answer(candidates, lineage, request.query)
    else:
        logger.info("OLLAMA_API_KEY ausente — retornando resposta estruturada sem LLM.")
        answer = _build_fallback_answer(candidates, lineage, request.query)

    timing.total_ms = round((time.perf_counter() - t_start) * 1000, 1)
    logger.info(
        "Busca concluída em %.1fms (embedding=%.1fms, vetorial=%.1fms, linhagem=%.1fms, síntese=%.1fms)",
        timing.total_ms or 0,
        timing.embedding_ms or 0,
        timing.vector_search_ms or 0,
        timing.lineage_ms or 0,
        timing.synthesis_ms or 0,
    )

    return SearchResponse(answer=answer, sources=sources, lineage=lineage, timing=timing)


@app.get("/graph/{uid}", response_model=GraphResponse)
def graph(
    uid: str,
    page: int = Query(1, ge=1, description="Número da página (1-based)"),
    page_size: int = Query(200, ge=1, le=1000, description="Nós por página"),
) -> GraphResponse:
    root_query = """
    MATCH (n)
    WHERE n.uid = $uid OR n.nome = $uid OR n.titulo = $uid
    RETURN elementId(n) AS id
    ORDER BY CASE WHEN n:Evento THEN 0 ELSE 1 END
    LIMIT 1
    """
    nodes_query = """
    MATCH (root)
    WHERE elementId(root) = $root_id
    MATCH p=(root)-[:FEZ|INFLUENCIA|FUNDAMENTA|EVOLUI_PARA*0..4]-(n)
    WITH DISTINCT n
    RETURN elementId(n) AS id, labels(n) AS labels, n{.*} AS props
    """
    edges_query = """
    MATCH (a)-[r:FEZ|INFLUENCIA|FUNDAMENTA|EVOLUI_PARA]-(b)
    WHERE elementId(a) IN $node_ids AND elementId(b) IN $node_ids
    RETURN DISTINCT elementId(r) AS id,
           elementId(a) AS source,
           elementId(b) AS target,
           type(r) AS rel_type,
           r.prop_motivo AS prop_motivo
    """

    with NEO4J_DRIVER.session(database=NEO4J_DATABASE) as session:
        root_row = session.run(root_query, uid=uid).single()
        if not root_row:
            raise HTTPException(status_code=404, detail=f"Nenhum nó encontrado para uid '{uid}'.")
        root_id = root_row["id"]

        all_node_rows = session.run(nodes_query, root_id=root_id).data()
        total_nodes = len(all_node_rows)

        # Paginação de nós
        start_idx = (page - 1) * page_size
        node_rows = all_node_rows[start_idx : start_idx + page_size]
        node_ids = [row["id"] for row in node_rows]

        edge_rows = session.run(edges_query, node_ids=node_ids).data() if node_ids else []

    nodes: List[GraphNode] = []
    for row in node_rows:
        labels = row.get("labels") or []
        props = row.get("props") or {}
        fontes = props.get("fontes") or props.get("sources") or []
        if isinstance(fontes, str):
            fontes = [fontes]
        nodes.append(
            GraphNode(
                id=row["id"],
                uid=props.get("uid"),
                nome=props.get("nome"),
                titulo=props.get("titulo"),
                ano=props.get("ano"),
                ano_proposta=props.get("ano_proposta"),
                descricao=props.get("descricao"),
                bio=props.get("bio"),
                impacto=props.get("impacto"),
                problema_resolvido=props.get("problema_resolvido"),
                category=_node_category_from_labels(labels),
                fontes=[str(item) for item in fontes if item],
            )
        )

    edges = [
        GraphEdge(
            id=row["id"],
            source=row["source"],
            target=row["target"],
            rel_type=row["rel_type"],
            prop_motivo=row.get("prop_motivo"),
        )
        for row in edge_rows
    ]

    return GraphResponse(
        uid=uid,
        root_id=root_id,
        nodes=nodes,
        edges=edges,
        total_nodes=total_nodes,
        total_edges=len(edges),
        page=page,
        page_size=page_size,
    )


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


@app.get("/{full_path:path}", include_in_schema=False)
def spa_fallback(full_path: str) -> Any:
    if not FRONTEND_DIST:
        raise HTTPException(status_code=404, detail="Not Found")

    candidate = FRONTEND_DIST / full_path
    if full_path and candidate.exists() and candidate.is_file():
        return FileResponse(candidate)

    return FileResponse(FRONTEND_DIST / "index.html")
