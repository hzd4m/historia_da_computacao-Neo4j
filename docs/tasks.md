# Documentação das Tasks

Este arquivo irá documentar todas as tasks realizadas para a construção da infraestrutura "Graph Data Computer".

## Prompt Mestre

**Atuação:** Arquiteto de Software Sênior e Engenheiro de Dados especialista em Grafos e sistemas RAG (Retrieval-Augmented Generation).

**Objetivo:** Construir a infraestrutura completa de um sistema de GraphRAG sobre a História da Computação utilizando a stack: Neo4j 5 (Vector Index), FastAPI, Ollama Cloud (modelo gpt-oss:120b) e Docker.

**Contexto do Modelo de Dados (Ontologia):**
- Nós: Pessoa, Teoria, Tecnologia, Evento.
- Relacionamentos: [:FEZ], [:INFLUENCIA], ...
- Marcos Históricos: De Leibniz (1679) até IA Generativa moderna.

**Especificações Técnicas:**
1. Script de Ingestão (scripts/ingest.py)
2. Backend API (scripts/start_api.py)
3. Orquestração Local (docker-compose.yml)
4. Qualidade de Código e Documentação

---

## Histórico de Tasks

### 1. Criação da pasta /docs
Data: 16/02/2026
Descrição: Pasta criada para centralizar a documentação do projeto.

---

### 2. Geração dos arquivos principais
Data: 16/02/2026
Descrição: Foram criados os arquivos:
- scripts/ingest.py: Script de ingestão de dados históricos, geração de embeddings e indexação vetorial no Neo4j.
- scripts/start_api.py: Backend FastAPI com endpoints /search (busca híbrida) e /timeline (eventos cronológicos).
- docker-compose.yml: Orquestração dos serviços Neo4j e App Python, com healthcheck e execução automatizada.
- requirements.txt: Lista de dependências do projeto.
- README.md: Instruções de execução e descrição da stack em PT-BR.

---

*Novas tasks serão documentadas aqui conforme forem realizadas.*

---

### 3. Atualização do `docker-compose.yml`
Data: 17/02/2026
Descrição: `docker-compose.yml` foi atualizado para atender requisitos de produção/analítica:
- Uso da imagem oficial `neo4j:5`.
- Variáveis de ambiente para `NEO4J_PLUGINS` com `apoc` e `graph-data-science` (GDS).
- Configurações de segurança para permitir procedimentos `apoc.*` e `gds.*` (`dbms.security.procedures.unrestricted` e `dbms.security.procedures.allowlist`).
- Volumes mapeados: `./neo4j_data:/data`, `./neo4j_logs:/logs`, `./neo4j_import:/import`, `./neo4j_plugins:/plugins`.
- Limites de memória configuráveis via variáveis `NEO4J_dbms_memory_heap_max__size` e `NEO4J_dbms_memory_pagecache_size`.
- Healthcheck HTTP e política de restart.

---

### 4. Permissões de volumes (UID/GID)
Data: 17/02/2026
Descrição: Instruções para garantir que o usuário do container Neo4j tenha permissão de escrita nos diretórios host:

- Descobrir UID/GID do usuário `neo4j` na imagem:

	```bash
	docker run --rm --entrypoint id neo4j:5 neo4j
	```

- Ajustar proprietário dos diretórios no host (exemplo usando UID/GID retornado):

	```bash
	sudo chown -R 7474:7474 ./neo4j_data ./neo4j_logs ./neo4j_import ./neo4j_plugins
	```

- Alternativa menos restritiva (menos segura):

	```bash
	chmod -R 0775 ./neo4j_data ./neo4j_logs ./neo4j_import ./neo4j_plugins
	```

Observação: substitua `7474:7474` pelo UID:GID exato retornado pelo comando `id`.

---

### 5. Validação de carregamento dos plugins (APOC / GDS)
Data: 17/02/2026
Descrição: Comandos para verificar se APOC e GDS foram carregados corretamente após `docker compose up`.

- Verificar logs do container Neo4j por mensagens relativas a APOC/GDS:

	```bash
	docker logs neo4j 2>&1 | grep -i apoc || true
	docker logs neo4j 2>&1 | grep -i gds || true
	```

- Executar chamadas Cypher para checar procedimentos (usando `cypher-shell` dentro do container):

	```bash
	docker exec -it neo4j bin/cypher-shell -u neo4j -p password "CALL apoc.help('') YIELD name RETURN name LIMIT 5;"
	docker exec -it neo4j bin/cypher-shell -u neo4j -p password "CALL gds.version() YIELD version RETURN version;"
	```

- Alternativa via HTTP (REST API):

	```bash
	curl -s -u neo4j:password -H 'Content-Type: application/json' \
		-X POST http://localhost:7474/db/neo4j/tx/commit \
		-d '{"statements":[{"statement":"CALL gds.version() YIELD version RETURN version"}]}'
	```

Resultado esperado: respostas válidas sem erros indicando que `apoc` e `gds` estão ativos.

---

### 6. Status atual das tasks
Data: 17/02/2026
- `docker-compose.yml`: atualizado ✅
- Permissões de volumes (UID/GID): instruções adicionadas ✅
- Comandos de validação de plugins: instruções adicionadas ✅

*Próximo passo sugerido: rodar `docker compose up --build` localmente, aplicar `chown` nos volumes se necessário e validar os procedimentos com os comandos acima.*
