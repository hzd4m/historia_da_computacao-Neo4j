#!/usr/bin/env bash
set -euo pipefail

# Script macOS: aplica DNS públicos (Cloudflare/Google), limpa cache DNS,
# reinicia o ollama_bridge e testa conectividade com api.ollama.cloud.
# Uso: sudo bash scripts/ensure_dns_and_restart_bridge.sh [--revert]

REVERT=false
if [ "${1:-}" = "--revert" ]; then
  REVERT=true
fi

if ! command -v networksetup >/dev/null 2>&1; then
  echo "Este script é para macOS com 'networksetup'. Saindo." >&2
  exit 1
fi

# Detectar serviço de rede preferencial (tenta Wi-Fi então Ethernet)
SERVICE=""
if networksetup -getinfo "Wi-Fi" >/dev/null 2>&1; then
  SERVICE="Wi-Fi"
elif networksetup -getinfo "Ethernet" >/dev/null 2>&1; then
  SERVICE="Ethernet"
else
  # pega o primeiro serviço listado (pula a linha de header)
  SERVICE=$(networksetup -listallnetworkservices 2>/dev/null | sed -n '2p')
fi

if [ -z "$SERVICE" ]; then
  echo "Não foi possível detectar o serviço de rede (Wi-Fi/Ethernet)." >&2
  exit 1
fi

echo "Serviço de rede detectado: $SERVICE"

if [ "$REVERT" = true ]; then
  echo "Revertendo DNS para usar DHCP (Empty) no serviço $SERVICE"
  sudo networksetup -setdnsservers "$SERVICE" Empty
  echo "Flush cache DNS..."
  sudo dscacheutil -flushcache || true
  sudo killall -HUP mDNSResponder || true
  echo "DNS revertido. Saindo."
  exit 0
fi

echo "Aplicando servidores DNS públicos: 1.1.1.1 8.8.8.8"
sudo networksetup -setdnsservers "$SERVICE" 1.1.1.1 8.8.8.8

echo "Limpando cache DNS..."
sudo dscacheutil -flushcache || true
sudo killall -HUP mDNSResponder || true

echo "Reiniciando o Ollama Bridge..."
pkill -f ollama_bridge.py || true
nohup python scripts/ollama_bridge.py > /tmp/ollama_bridge.log 2>&1 &
sleep 2

BRIDGE_PORT="${OLLAMA_BRIDGE_PORT:-11435}"

echo "Logs do bridge (últimas 200 linhas):"
tail -n 200 /tmp/ollama_bridge.log || true

echo "Testando disponibilidade de modelos remoto (api.ollama.cloud):"
if [ -z "${OLLAMA_API_KEY:-}" ]; then
  echo "A variável OLLAMA_API_KEY não está definida neste ambiente. Exporte-a antes de rodar o script." >&2
  exit 1
fi

echo "Chamando https://api.ollama.cloud/v1/models ..."
curl -s -H "Authorization: Bearer $OLLAMA_API_KEY" https://api.ollama.cloud/v1/models || echo "curl falhou"

echo "Teste de chat via bridge local (modelo de exemplo 'glm-5')"
curl -i -s "http://localhost:${BRIDGE_PORT}/api/chat" -H "Content-Type: application/json" -d '{"model":"glm-5","messages":[{"role":"user","content":"Teste de conexão."}],"stream":false}' || true

echo "Se estiver satisfeito, para reverter DNS execute: sudo bash scripts/ensure_dns_and_restart_bridge.sh --revert"
