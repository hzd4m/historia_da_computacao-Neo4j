#!/usr/bin/env bash
# Script para ativar a virtualenv local `.venv` e preparar o ambiente
# Uso: bash scripts/activate_env.sh

set -euo pipefail

VENV_DIR=".venv"

if [ ! -d "$VENV_DIR" ]; then
  echo "Virtualenv $VENV_DIR não encontrada. Para criar: python3 -m venv .venv"
  exit 1
fi

echo "Ativando virtualenv em $VENV_DIR"
# ativa a virtualenv no shell atual quando source for usado
source "$VENV_DIR/bin/activate"

echo "Python: $(python --version)"
echo "PIP: $(pip --version)"

if [ -f requirements.txt ]; then
  echo "Instalando dependências (requirements.txt)..."
  pip install -r requirements.txt
fi

echo "Ambiente pronto. Para manter o shell ativo com a venv ativada, use: source scripts/activate_env.sh"
