# Planejamento de Implementação — Graph DB + Visualização + Interação (Projeto #6)

## Contexto
Este plano organiza a continuidade do projeto para garantir:
1. **Banco em grafo operacional e confiável** (Neo4j + ingestão idempotente).
2. **Visualização navegável e interativa para o usuário final** (frontend com Cytoscape + API).
3. **Base técnica pronta para adicionar LLM/GraphRAG na próxima etapa**.

Escopo principal desta fase: entregar experiência funcional de exploração do grafo e trilha de produção.

---

## Objetivo de Produto (fase atual)
Permitir que qualquer usuário:
- abra a aplicação em uma URL única;
- visualize a linhagem histórica no grafo;
- interaja com zoom/pan/click;
- consulte detalhes de nós e relações;
- execute buscas de contexto histórico com retorno consistente.

---

## Estrutura sugerida no GitHub Projects #6

### Colunas
1. **Backlog**
2. **Ready**
3. **In Progress**
4. **Review/Testes**
5. **Done**

### Campos customizados
- **Prioridade**: P0, P1, P2
- **Tipo**: Infra, Backend, Frontend, Dados, QA, Docs
- **Status Técnico**: Bloqueado, Em andamento, Validado
- **Sprint**: S1, S2, S3

---

## Roadmap em 3 fases

## Fase 1 — Base de Grafo e Operação (P0)
**Meta:** garantir stack estável e dados consistentes.

### Entregas
- [ ] Neo4j saudável com volumes e permissões corretas.
- [ ] ETL idempotente com logs em PT-BR e tipagem consistente.
- [ ] Índices essenciais (BTREE + vetorial quando disponível).
- [ ] Endpoint de saúde consolidado (`/healthz`, `/timeline`, `/graph/{uid}`).
- [ ] Checklist de smoke test pós-deploy.

### Critérios de aceite
- [ ] `docker compose up --build` sobe sem reinício em loop.
- [ ] `GET /graph/{uid}` retorna nós/arestas para casos conhecidos.
- [ ] Ingestão repetida não gera duplicatas de nós/arestas.

### Riscos
- Permissões de volume no host.
- Falhas intermitentes de rede para serviços remotos.

---

## Fase 2 — Visualização e Interação do Usuário (P0/P1)
**Meta:** experiência completa de exploração de grafo no frontend.

### Entregas
- [ ] Dashboard com layout hierárquico por ano (esquerda → direita).
- [ ] Identidade visual por tipo de nó (Pessoa/Teoria/Tecnologia/Evento).
- [ ] Estilização semântica de arestas (`FEZ`, `INFLUENCIA`, `FUNDAMENTA`, `EVOLUI_PARA`).
- [ ] Drawer lateral com detalhes e fontes.
- [ ] Controles de zoom/pan/reset e centralização do subgrafo selecionado.
- [ ] Destaque do caminho de resposta e trilha de linhagem.
- [ ] Responsividade para telas menores sem obstrução de contexto.

### Critérios de aceite
- [ ] Usuário consegue abrir em porta única (`:8000`) e navegar.
- [ ] Clique em nó atualiza painel de detalhes em < 150ms para subgrafos médios.
- [ ] Renderização fluida para grafos de referência do projeto.

### Riscos
- Crescimento do subgrafo degradando UX.
- Inconsistência de propriedades entre nós legados e novos.

---

## Fase 3 — Preparação para LLM/GraphRAG (P1)
**Meta:** deixar o sistema pronto para evolução sem retrabalho.

### Entregas
- [ ] Contrato estável de API para busca híbrida (`/search`).
- [ ] Pipeline de fallback quando embeddings estiverem indisponíveis.
- [ ] Estrutura de prompts versionada por cenário de pergunta.
- [ ] Observabilidade de latência por camada (vetorial, grafo, síntese).
- [ ] Auditoria de fontes/anos citados na resposta final.

### Critérios de aceite
- [ ] `/search` responde com `answer`, `sources`, `lineage`.
- [ ] Falha de embedding não derruba API; retorna erro explicável.
- [ ] Logs permitem rastrear contexto usado na resposta.

### Riscos
- Permissão insuficiente da chave para endpoint de embedding.
- Variação de resposta do modelo sem citação adequada.

---

## Backlog inicial sugerido (cards para criar agora)

## P0 — Infra/Backend
1. **[P0][Infra] Harden do docker-compose para ciclo local confiável**
   - DoD: stack sobe limpa, healthchecks verdes, sem restart loop.

2. **[P0][Backend] Padronizar contrato `/graph/{uid}` e paginação de subgrafo**
   - DoD: resposta consistente para nós sem vizinhos e com vizinhos profundos.

3. **[P0][Dados] Validação automática de CSVs antes da ingestão**
   - DoD: job bloqueia ingestão com schema inválido.

## P0/P1 — Frontend
4. **[P0][Frontend] Navegação completa no Cytoscape com controles UX**
   - DoD: zoom/pan/reset + fit + destaque de seleção.

5. **[P1][Frontend] Drawer semântico com metadados e fontes**
   - DoD: mostra nome, ano, descrição, origem, relações-chave.

6. **[P1][Frontend] Modo Storyline temporal por marcos históricos**
   - DoD: usuário percorre 1679 → 2022 com checkpoints.

## P1 — Preparação LLM
7. **[P1][Backend] Telemetria de busca híbrida por etapa**
   - DoD: logs com tempo de embedding, query e síntese.

8. **[P1][NLP] Template de prompt com citação obrigatória de ano/fonte**
   - DoD: resposta rejeitada quando faltar citação mínima.

---

## Sprint sugerida (2 semanas)

### Semana 1
- Estabilização de infra/ETL/API (`P0`).
- Contrato de dados para `/graph/{uid}`.
- Smoke tests automatizados de backend.

### Semana 2
- UX do grafo + drawer + responsividade (`P0/P1`).
- Destaque de linhagem e trilha de resposta.
- Checklist de aceite funcional com gravação de evidências.

---

## Métricas de sucesso (fase atual)
- **Disponibilidade local da stack**: > 95% dos boots sem intervenção manual.
- **Tempo de primeira visualização do grafo**: < 3s em dataset base.
- **Taxa de erro do endpoint `/graph/{uid}`**: < 1% em testes de regressão.
- **Satisfação de navegação (QA interna)**: zoom/pan/click/reset funcionando em 100% dos testes.

---

## Dependências e bloqueadores
- Chave Ollama com escopo para embeddings (para etapa LLM posterior).
- Garantia de saúde do Neo4j e consistência dos CSVs.
- Definição final dos tipos de relação a priorizar na visualização.

---

## Definição de Pronto (DoR) para iniciar etapa LLM
Só iniciar implementação LLM quando:
- [ ] Fase 1 concluída e validada.
- [ ] Fase 2 concluída com UX aprovada.
- [ ] Endpoint `/search` com contrato estável e logs rastreáveis.
- [ ] Time alinhado sobre métricas de qualidade de resposta.
