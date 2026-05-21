# Arquitetura  Job Match Alerts

## Visão geral

Monorepo com frontend React (`apps/web`) e API FastAPI (`apps/api`). PostgreSQL persiste perfis, vagas e regras de alerta; arquivos PDF ficam em `uploads/` (volume Docker). Redis está no Compose para filas de e-mail (Fase 5).

```text
┌─────────────┐     HTTP      ┌──────────────┐
│  React UI   │ ────────────► │   FastAPI    │
│  (Vite)     │   REST/JSON   │   api_router │
└─────────────┘               └──────┬───────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              ▼                      ▼                      ▼
        profiles              job_import              ats_engine
        resume_parser              ai                  jobs / match
              │                      │                      │
              └──────────────────────┴──────────────────────┘
                                     ▼
                              PostgreSQL
                              uploads/ (PDF)
```

## Camadas da API

| Camada | Responsabilidade |
|--------|------------------|
| `api/routes` | HTTP, validação Pydantic, códigos de erro |
| `services` | Regras de negócio (matching, import, parse) |
| `models` | Tabelas SQLAlchemy |
| `schemas` | Contratos de entrada/saída + OpenAPI |
| `db` | Engine async, `create_all`, migrações leves |

## Fluxos principais

### 1. Currículo (`POST /profiles/parse`)

1. PDF → `pypdf` extrai texto bruto.
2. Heurística local preenche campos iniciais.
3. Se `OPENAI_API_KEY` definida → `parse_resume_structured` enriquece JSON.
4. **Novo** registro em `candidate_profiles` (vários por `demo_user_id`).
5. PDF salvo em `uploads/demo/`.

### 2. Vaga (`POST /jobs/import`)

1. `job_import` faz GET na URL (User-Agent identificável).
2. Detecta fonte (gupy / linkedin / inhire / external).
3. Extrai título, descrição, remoto, senioridade.
4. `upsert` em `jobs` por `(source, external_id)`.
5. OpenAI opcional → `skills_analysis` JSON na vaga.
6. `ats_engine.compute_match` com perfil (`profile_id` ou o mais recente).

### 3. Ranking (`GET /match/rank`)

Lista vagas, aplica filtros (`remote_only`, `seniority`, `min_score`), calcula match por vaga, ordena por `score` desc.

## Motor ATS

Implementação em `services/ats_engine.py`:

- Normalização de skills (lowercase, strip).
- Overlap obrigatório vs desejável sem variável stale em loops.
- `seniority_matches` via ranks em `job_meta.py`.
- Breakdown com chaves alinhadas aos pesos (`semantic_match`).

Testes unitários em `tests/test_ats_engine.py` (sem banco).

## Configuração e ambiente

`app/core/config.py`:

- Carrega `.env` da raiz do repo (detecta via `docker-compose.yml`).
- `.env.local` sobrescreve para API rodando fora do Docker (`localhost:5433`).

Compose injeta `env_file: .env` nos serviços.

## Migrações

Sem Alembic no MVP. No startup:

1. `Base.metadata.create_all`
2. `run_migrations`  colunas extras (`jobs.seniority`, `candidate_profiles.label`, drop índice único legado em `demo_user_id`).

## Frontend

- `ProfileContext`  lista de perfis + `activeProfileId` em `localStorage`.
- `ProfileSelector`  dropdown nas abas Vagas e ATS.
- Proxy Vite `/api` → `localhost:8002` em dev.
- Produção: `VITE_API_URL` apontando para API pública (Render).

## Segurança (escopo demo)

- Sem autenticação; um usuário demo.
- CORS configurável via `CORS_ORIGINS`.
- Upload limitado a 8 MB PDF.
- Não versionar `.env` nem `uploads/`.

## Evoluções planejadas

Ver tabela de roadmap no [README.md](../README.md).
