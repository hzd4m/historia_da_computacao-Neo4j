"""
Ollama Cloud Bridge
s 
Proxy local para rotear modelos selecionados para o Ollama Cloud
e manter modelos locais no Ollama local.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from typing import Any, AsyncGenerator, Dict, List, Optional, Sequence, Set, Tuple

import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse


def env_bool(name: str, default: bool = False) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "y", "on"}


APP_HOST = os.getenv("OLLAMA_BRIDGE_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("OLLAMA_BRIDGE_PORT", "11435"))
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
OLLAMA_REMOTE_URL = os.getenv("OLLAMA_REMOTE_URL", "https://api.ollama.cloud").rstrip("/")
OLLAMA_LOCAL_UPSTREAM = os.getenv("OLLAMA_LOCAL_UPSTREAM", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_BRIDGE_DEBUG = env_bool("OLLAMA_BRIDGE_DEBUG", default=False)
OLLAMA_REMOTE_MODELS_TTL = int(os.getenv("OLLAMA_REMOTE_MODELS_TTL", "120"))

# Exemplo:
# OLLAMA_MODEL_MAP_JSON='{"gpt-oss:120b":["gpt-oss:120b","glm-5"],"*":["qwen3:32b"]}'
OLLAMA_MODEL_MAP_JSON = os.getenv("OLLAMA_MODEL_MAP_JSON", "").strip()

DEFAULT_MODEL_MAP = {"gpt-oss:120b": ["gpt-oss:120b"]}

REMOTE_PATH_CANDIDATES = {
    "/api/chat": ["/api/chat", "/chat", "/v1/api/chat", "/v1/chat"],
    "/api/generate": ["/api/generate", "/generate", "/v1/api/generate", "/v1/generate"],
}
LOCAL_PATH_CANDIDATES = {
    "/api/chat": ["/api/chat", "/chat"],
    "/api/generate": ["/api/generate", "/generate"],
}

REMOTE_MODEL_LIST_PATHS = ["/v1/models", "/api/tags"]
UPSTREAM_TIMEOUT = httpx.Timeout(60.0, read=300.0)
MODEL_LIST_TIMEOUT = httpx.Timeout(20.0, read=20.0)

logging.basicConfig(
    level=logging.DEBUG if OLLAMA_BRIDGE_DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("ollama-bridge")

app = FastAPI(title="Ollama Cloud Bridge", docs_url="/docs")

_remote_models_cache: Set[str] = set()
_remote_models_cached_at: float = 0.0
_remote_models_error: Optional[str] = None
_remote_models_lock = asyncio.Lock()


def load_model_map() -> Dict[str, List[str]]:
    if not OLLAMA_MODEL_MAP_JSON:
        return DEFAULT_MODEL_MAP
    try:
        parsed = json.loads(OLLAMA_MODEL_MAP_JSON)
    except json.JSONDecodeError as exc:
        logger.warning("OLLAMA_MODEL_MAP_JSON inválido. Usando default. Erro: %s", exc)
        return DEFAULT_MODEL_MAP

    if not isinstance(parsed, dict):
        logger.warning("OLLAMA_MODEL_MAP_JSON precisa ser objeto JSON. Usando default.")
        return DEFAULT_MODEL_MAP

    normalized: Dict[str, List[str]] = {}
    for key, value in parsed.items():
        if not isinstance(key, str):
            continue
        if isinstance(value, str):
            models = [item.strip() for item in value.split("|") if item.strip()]
        elif isinstance(value, list):
            models = [str(item).strip() for item in value if str(item).strip()]
        else:
            continue
        if models:
            normalized[key.strip()] = models

    if not normalized:
        logger.warning("OLLAMA_MODEL_MAP_JSON sem entradas válidas. Usando default.")
        return DEFAULT_MODEL_MAP
    return normalized


MODEL_MAP = load_model_map()


def extract_model_from_item(item: Any) -> Optional[str]:
    if isinstance(item, str):
        model = item.strip()
        return model or None
    if isinstance(item, dict):
        for key in ("id", "model", "name"):
            raw_value = item.get(key)
            if isinstance(raw_value, str) and raw_value.strip():
                return raw_value.strip()
    return None


def extract_remote_models(payload: Any) -> Set[str]:
    models: Set[str] = set()
    if isinstance(payload, dict):
        for list_key in ("data", "models"):
            entries = payload.get(list_key)
            if isinstance(entries, list):
                for item in entries:
                    model = extract_model_from_item(item)
                    if model:
                        models.add(model)
    elif isinstance(payload, list):
        for item in payload:
            model = extract_model_from_item(item)
            if model:
                models.add(model)
    return models


def model_not_found_text(text: str) -> bool:
    lowered = text.lower()
    return (
        "model not found" in lowered
        or "no such model" in lowered
        or "unknown model" in lowered
    )


def resolve_remote_candidates(requested_model: Optional[str]) -> List[str]:
    if not requested_model:
        return []
    requested_model = requested_model.strip()
    if not requested_model:
        return []
    mapped = MODEL_MAP.get(requested_model) or MODEL_MAP.get("*")
    if not mapped:
        return []
    unique: List[str] = []
    seen: Set[str] = set()
    for model in mapped:
        cleaned = model.strip()
        if cleaned and cleaned not in seen:
            unique.append(cleaned)
            seen.add(cleaned)
    return unique


def merge_paths(requested_path: str, candidates: Dict[str, Sequence[str]]) -> List[str]:
    paths = list(candidates.get(requested_path, [requested_path]))
    if requested_path not in paths:
        paths.insert(0, requested_path)
    return paths


def build_url(base_url: str, path: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        return path
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{base_url}{path}"


def response_from_upstream(resp: httpx.Response) -> Response:
    content_type = resp.headers.get("content-type", "application/octet-stream")
    try:
        parsed = resp.json()
    except ValueError:
        return Response(content=resp.content, status_code=resp.status_code, media_type=content_type)
    return JSONResponse(status_code=resp.status_code, content=parsed)


async def fetch_remote_models(force_refresh: bool = False) -> Tuple[Set[str], Optional[str]]:
    global _remote_models_cache, _remote_models_cached_at, _remote_models_error

    if not OLLAMA_API_KEY:
        return set(), "OLLAMA_API_KEY não configurada."

    now = time.monotonic()
    cache_valid = (now - _remote_models_cached_at) < OLLAMA_REMOTE_MODELS_TTL
    if not force_refresh and cache_valid:
        if _remote_models_cache:
            return set(_remote_models_cache), None
        return set(), _remote_models_error

    async with _remote_models_lock:
        now = time.monotonic()
        cache_valid = (now - _remote_models_cached_at) < OLLAMA_REMOTE_MODELS_TTL
        if not force_refresh and cache_valid:
            if _remote_models_cache:
                return set(_remote_models_cache), None
            return set(), _remote_models_error

        headers = {"Authorization": f"Bearer {OLLAMA_API_KEY}"}
        last_error: Optional[str] = None

        async with httpx.AsyncClient(timeout=MODEL_LIST_TIMEOUT) as client:
            for path in REMOTE_MODEL_LIST_PATHS:
                url = build_url(OLLAMA_REMOTE_URL, path)
                try:
                    resp = await client.get(url, headers=headers)
                except httpx.RequestError as exc:
                    last_error = f"Erro de rede em {url}: {exc}"
                    continue

                if resp.status_code in (401, 403):
                    last_error = f"Autorização falhou no endpoint de modelos ({resp.status_code})."
                    break
                if resp.status_code >= 400:
                    last_error = f"Falha ao listar modelos em {url} (HTTP {resp.status_code})."
                    continue

                try:
                    body = resp.json()
                except ValueError:
                    last_error = f"Resposta inválida de {url} (não JSON)."
                    continue

                models = extract_remote_models(body)
                if models:
                    _remote_models_cache = set(models)
                    _remote_models_cached_at = time.monotonic()
                    _remote_models_error = None
                    return set(models), None

                last_error = f"Nenhum modelo detectado em {url}."

        _remote_models_cache = set()
        _remote_models_cached_at = time.monotonic()
        _remote_models_error = last_error or "Falha desconhecida ao consultar modelos remotos."
        return set(), _remote_models_error


async def try_streaming_post(
    *,
    url: str,
    payload: Dict[str, Any],
    headers: Dict[str, str],
    allow_model_not_found_retry: bool,
) -> Tuple[Optional[Response], Optional[str], bool]:
    client = httpx.AsyncClient(timeout=UPSTREAM_TIMEOUT)
    request = client.build_request("POST", url, json=payload, headers=headers)
    try:
        resp = await client.send(request, stream=True)
    except httpx.RequestError as exc:
        await client.aclose()
        return None, str(exc), False

    if resp.status_code in (401, 403):
        body = (await resp.aread()).decode(errors="ignore")
        await resp.aclose()
        await client.aclose()
        return JSONResponse(
            status_code=resp.status_code,
            content={"error": "Autorização falhou no upstream remoto.", "detail": body[:1000]},
        ), None, False

    if resp.status_code >= 400:
        body = (await resp.aread()).decode(errors="ignore")
        await resp.aclose()
        await client.aclose()
        if allow_model_not_found_retry and model_not_found_text(body):
            return None, None, True
        return JSONResponse(
            status_code=resp.status_code,
            content={"error": f"Upstream retornou HTTP {resp.status_code}.", "detail": body[:1000]},
        ), None, False

    media_type = resp.headers.get("content-type", "application/octet-stream")

    async def event_generator() -> AsyncGenerator[bytes, None]:
        try:
            async for chunk in resp.aiter_bytes():
                if chunk:
                    yield chunk
        finally:
            await resp.aclose()
            await client.aclose()

    return StreamingResponse(
        event_generator(),
        media_type=media_type,
        status_code=resp.status_code,
    ), None, False


async def forward_local(path: str, payload: Dict[str, Any], stream: bool) -> Response:
    paths = merge_paths(path, LOCAL_PATH_CANDIDATES)
    headers = {"Content-Type": "application/json"}
    last_error: Optional[str] = None

    for candidate_path in paths:
        url = build_url(OLLAMA_LOCAL_UPSTREAM, candidate_path)
        try:
            if stream:
                proxied, network_error, retry = await try_streaming_post(
                    url=url,
                    payload=payload,
                    headers=headers,
                    allow_model_not_found_retry=False,
                )
                if retry:
                    continue
                if proxied is not None:
                    logger.info("Rota local usada: %s (stream)", url)
                    return proxied
                if network_error:
                    last_error = network_error
                continue

            async with httpx.AsyncClient(timeout=UPSTREAM_TIMEOUT) as client:
                resp = await client.post(url, json=payload, headers=headers)

            if resp.status_code == 404 and candidate_path != paths[-1]:
                continue
            logger.info("Rota local usada: %s", url)
            return response_from_upstream(resp)
        except httpx.RequestError as exc:
            last_error = str(exc)
            logger.warning("Erro de rede no upstream local %s: %s", url, exc)

    return JSONResponse(
        status_code=502,
        content={
            "error": "Falha ao contatar Ollama local.",
            "detail": last_error or "Nenhuma rota local respondeu com sucesso.",
        },
    )


async def forward_remote(
    path: str,
    payload: Dict[str, Any],
    stream: bool,
    requested_model: str,
    mapped_candidates: Sequence[str],
) -> Response:
    if not OLLAMA_API_KEY:
        return JSONResponse(
            status_code=503,
            content={"error": "OLLAMA_API_KEY ausente para roteamento remoto."},
        )

    models, models_error = await fetch_remote_models(force_refresh=False)
    selected_candidates = list(mapped_candidates)
    if models:
        filtered = [model for model in mapped_candidates if model in models]
        if filtered:
            selected_candidates = filtered
        else:
            return JSONResponse(
                status_code=404,
                content={
                    "error": f"Nenhum modelo remoto disponível para '{requested_model}'.",
                    "mapped_candidates": list(mapped_candidates),
                    "available_models_sample": sorted(models)[:30],
                },
            )
    elif models_error:
        logger.warning("Não foi possível validar modelos remotos antes do roteamento: %s", models_error)

    paths = merge_paths(path, REMOTE_PATH_CANDIDATES)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OLLAMA_API_KEY}",
    }

    last_network_error: Optional[str] = None
    for model in selected_candidates:
        payload_with_model = dict(payload)
        payload_with_model["model"] = model
        for candidate_path in paths:
            url = build_url(OLLAMA_REMOTE_URL, candidate_path)
            try:
                if stream:
                    proxied, network_error, retry = await try_streaming_post(
                        url=url,
                        payload=payload_with_model,
                        headers=headers,
                        allow_model_not_found_retry=True,
                    )
                    if retry:
                        if OLLAMA_BRIDGE_DEBUG:
                            logger.debug("Modelo '%s' não encontrado em %s (stream).", model, url)
                        continue
                    if proxied is not None:
                        logger.info(
                            "Rota remota usada: %s (modelo solicitado='%s', modelo remoto='%s', stream)",
                            url,
                            requested_model,
                            model,
                        )
                        return proxied
                    if network_error:
                        last_network_error = network_error
                    continue

                async with httpx.AsyncClient(timeout=UPSTREAM_TIMEOUT) as client:
                    resp = await client.post(url, json=payload_with_model, headers=headers)

                if resp.status_code in (401, 403):
                    return JSONResponse(
                        status_code=resp.status_code,
                        content={"error": "Autorização falhou ao acessar o endpoint remoto."},
                    )

                body_text = resp.text
                if model_not_found_text(body_text):
                    if OLLAMA_BRIDGE_DEBUG:
                        logger.debug("Modelo '%s' não encontrado em %s.", model, url)
                    continue

                logger.info(
                    "Rota remota usada: %s (modelo solicitado='%s', modelo remoto='%s')",
                    url,
                    requested_model,
                    model,
                )
                return response_from_upstream(resp)
            except httpx.RequestError as exc:
                last_network_error = str(exc)
                logger.warning("Erro de rede no upstream remoto %s: %s", url, exc)

    return JSONResponse(
        status_code=502 if last_network_error else 404,
        content={
            "error": "Falha ao rotear para o Ollama Cloud.",
            "requested_model": requested_model,
            "mapped_candidates": list(mapped_candidates),
            "detail": last_network_error or models_error or "Modelo não encontrado nos endpoints testados.",
        },
    )


async def forward_request(path: str, payload: Dict[str, Any], stream: bool) -> Response:
    model_value = payload.get("model")
    requested_model = model_value.strip() if isinstance(model_value, str) else ""
    remote_candidates = resolve_remote_candidates(requested_model)

    if remote_candidates:
        return await forward_remote(
            path=path,
            payload=payload,
            stream=stream,
            requested_model=requested_model,
            mapped_candidates=remote_candidates,
        )
    return await forward_local(path=path, payload=payload, stream=stream)


@app.get("/healthz")
async def healthz() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/models")
async def v1_models() -> Dict[str, Any]:
    models, error = await fetch_remote_models(force_refresh=True)
    if error and not models:
        raise HTTPException(status_code=502, detail=error)
    return {
        "object": "list",
        "data": [{"id": model, "object": "model"} for model in sorted(models)],
    }


@app.get("/bridge/config")
async def bridge_config() -> Dict[str, Any]:
    return {
        "local_upstream": OLLAMA_LOCAL_UPSTREAM,
        "remote_url": OLLAMA_REMOTE_URL,
        "remote_enabled": bool(OLLAMA_API_KEY),
        "model_map": MODEL_MAP,
    }


@app.post("/api/chat")
async def api_chat(request: Request) -> Response:
    payload = await request.json()
    stream = bool(payload.get("stream", False))
    logger.info("/api/chat recebida. Modelo: %s. Stream: %s", payload.get("model"), stream)
    return await forward_request("/api/chat", payload, stream)


@app.post("/api/generate")
async def api_generate(request: Request) -> Response:
    payload = await request.json()
    stream = bool(payload.get("stream", False))
    logger.info("/api/generate recebida. Modelo: %s. Stream: %s", payload.get("model"), stream)
    return await forward_request("/api/generate", payload, stream)


if __name__ == "__main__":
    import uvicorn

    logger.info("Iniciando Ollama Bridge em %s:%s", APP_HOST, APP_PORT)
    uvicorn.run(app, host=APP_HOST, port=APP_PORT)
