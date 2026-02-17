# Issue (GitHub Projects): Corrigir chamadas ao Ollama Cloud no GraphRAG

## Título sugerido
**[Infra][Ollama] Resolver falhas de chamada ao Ollama Cloud (DNS, endpoint remoto e validação de modelo)**

## Problema
As chamadas remotas para o Ollama Cloud apresentaram falhas intermitentes e bloqueios operacionais, impactando ingestão, busca híbrida e resposta RAG.

Principais sintomas observados:
- Falha de resolução DNS para `api.ollama.cloud`.
- Chamadas de embedding não autorizadas (`401`) em `/api/embed`.
- Dependência do bridge para roteamento e fallback de modelos.
- Falta de checklist operacional único para validar conectividade ponta a ponta.

## Objetivo
Garantir chamadas estáveis ao Ollama Cloud no ambiente local e Docker, com validação explícita de endpoint, autenticação Bearer e disponibilidade de modelos necessários para chat e embeddings.

## Escopo
- Padronizar `OLLAMA_REMOTE_URL` para host funcional.
- Validar `OLLAMA_API_KEY` para os endpoints de chat e embedding.
- Consolidar diagnóstico de DNS/rede com comandos reproduzíveis.
- Confirmar funcionamento do bridge e da API (`/search`) após correções.
- Documentar fallback operacional quando embedding estiver indisponível.

## Fora de escopo
- Treinamento de modelos.
- Execução local de modelos grandes (download de pesos).
- Mudança de provedor de LLM.

## Critérios de Aceite (DoD)
- [ ] `curl -H "Authorization: Bearer $OLLAMA_API_KEY" https://ollama.com/v1/models` retorna `200`.
- [ ] `POST /api/chat` no Ollama remoto responde `200` para `gpt-oss:120b`.
- [ ] `POST /api/embed` responde `200` com a mesma chave usada pela aplicação.
- [ ] Bridge (`scripts/ollama_bridge.py`) responde `200` em `/healthz` e `/v1/models`.
- [ ] Endpoint `/search` da API retorna resposta útil quando houver similaridade >= `0.7`.
- [ ] Em caso de falha de embedding, API retorna erro claro sem derrubar o serviço.

## Plano de Implementação
1. **Rede e endpoint**
   - Confirmar resolução de `ollama.com` e conectividade HTTPS.
   - Padronizar `.env` com `OLLAMA_REMOTE_URL=https://ollama.com`.

2. **Autenticação e permissões**
   - Validar escopo da `OLLAMA_API_KEY` para `chat` e `embed`.
   - Rotacionar chave se necessário e manter `.env` fora do Git.

3. **Validação funcional**
   - Executar smoke tests no bridge: `/healthz`, `/v1/models`, `/api/chat`.
   - Executar smoke test da API: `POST /search`.

4. **Observabilidade**
   - Registrar logs de erro sem vazar segredo.
   - Documentar matriz de erros comuns (DNS, 401, timeout, modelo inexistente).

## Riscos
- Bloqueio de DNS/Firewall corporativo impedindo saída para host remoto.
- Chave sem permissão para embeddings, degradando a busca híbrida.
- Instabilidade de rede mascarando problema de configuração.

## Dependências
- Variáveis de ambiente corretas no Docker e shell local.
- Neo4j saudável para etapa de recuperação vetorial.
- Endpoint do Ollama Cloud disponível.

## Evidências esperadas na conclusão
- Captura de logs com `200` para `/v1/models` e `/api/chat`.
- Teste documentado de `/api/embed` com status final.
- Resultado de `/search` com `answer`, `sources` e `lineage`.
