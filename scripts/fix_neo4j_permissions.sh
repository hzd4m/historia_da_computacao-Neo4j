#!/usr/bin/env bash
set -euo pipefail

# Ajusta ownership dos volumes do Neo4j para o UID/GID do usuario "neo4j"
# dentro da imagem oficial.
#
# Uso:
#   bash scripts/fix_neo4j_permissions.sh
#   bash scripts/fix_neo4j_permissions.sh --image neo4j:5.26.21
#   bash scripts/fix_neo4j_permissions.sh --dry-run

IMAGE="neo4j:5"
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --image)
      IMAGE="${2:-}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    *)
      echo "Opcao invalida: $1" >&2
      exit 1
      ;;
  esac
done

if ! command -v docker >/dev/null 2>&1; then
  echo "docker nao encontrado no PATH." >&2
  exit 1
fi

ID_OUTPUT="$(docker run --rm --entrypoint id "$IMAGE" neo4j 2>/dev/null || true)"
if [[ -z "$ID_OUTPUT" ]]; then
  echo "Nao foi possivel obter UID/GID com a imagem '$IMAGE'." >&2
  exit 1
fi

UID_VALUE="$(echo "$ID_OUTPUT" | sed -n 's/.*uid=\([0-9]\+\).*/\1/p')"
GID_VALUE="$(echo "$ID_OUTPUT" | sed -n 's/.*gid=\([0-9]\+\).*/\1/p')"

if [[ -z "$UID_VALUE" || -z "$GID_VALUE" ]]; then
  echo "Falha ao extrair UID/GID de: $ID_OUTPUT" >&2
  exit 1
fi

TARGETS=(./neo4j_data ./neo4j_logs ./neo4j_import ./neo4j_plugins)
for dir in "${TARGETS[@]}"; do
  mkdir -p "$dir"
done

echo "Imagem: $IMAGE"
echo "UID:GID detectado: ${UID_VALUE}:${GID_VALUE}"
echo "Diretorios: ${TARGETS[*]}"

if [[ "$DRY_RUN" == "true" ]]; then
  echo "[dry-run] sudo chown -R ${UID_VALUE}:${GID_VALUE} ${TARGETS[*]}"
  exit 0
fi

sudo chown -R "${UID_VALUE}:${GID_VALUE}" "${TARGETS[@]}"
echo "Permissoes ajustadas com sucesso."
