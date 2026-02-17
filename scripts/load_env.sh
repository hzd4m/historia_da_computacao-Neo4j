#!/usr/bin/env bash
# Carrega variáveis do arquivo .env para o shell atual
# Uso (no shell atual): source scripts/load_env.sh

if [ ! -f .env ]; then
  echo ".env não encontrado na raiz do projeto. Crie-o a partir de .env.example e cole a OLLAMA_API_KEY." >&2
  return 1 2>/dev/null || exit 1
fi

# Exporta todas as variáveis definidas no .env
set -a
. ./.env
set +a

# Confirmação (não imprime a chave)
if [ -n "${OLLAMA_API_KEY:-}" ]; then
  echo "Variável OLLAMA_API_KEY carregada (oculta)."
else
  echo "OLLAMA_API_KEY não definida no .env." >&2
fi
