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
