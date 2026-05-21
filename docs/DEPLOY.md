# Deploy — demo pública (portfólio)

Objetivo: **link da API (Swagger)** + **link da UI** sem transformar o projeto em produto.

## Visão

| Componente | Onde | Por quê |
|------------|------|---------|
| **API** | Render (Web Service, Docker) | FastAPI — igual ao Public Data Monitor |
| **Postgres** | **Neon** ou **Supabase** (recomendado) | Render free = **1 banco por conta**; se já existe o do `public-data-monitor`, use Postgres externo |
| **Frontend** | Vercel | Build estático do Vite |

---

## Limite Render: um Postgres free por conta

Se aparecer:

`cannot have more than one active free tier database`

**Não crie** outro PostgreSQL no Render. Opções:

| Opção | Quando usar |
|-------|-------------|
| **A — Neon (recomendado)** | Banco free separado; API continua no Render |
| **B — Supabase** | Idem, connection string no painel |
| **C — Mesmo Postgres do Public Data Monitor** | Criar database `job_match` no mesmo cluster (avançado; dois projetos no mesmo DB) |
| **D — Só Swagger** | API no Render + Neon; UI só no README (screenshots) |

---

## 1. Postgres no Neon (5 min)

1. [neon.tech](https://neon.tech) → projeto novo → copie a connection string.
2. Ajuste para asyncpg (a API também converte `postgresql://` automaticamente):

   ```env
   DATABASE_URL=postgresql+asyncpg://user:pass@ep-xxxx.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```

   Neon costuma exigir SSL — `?sslmode=require` no final costuma funcionar com asyncpg.

3. Guarde a URL; vai no Render abaixo.

---

## 2. API no Render (sem criar Postgres lá)

### Root Directory (obrigatório)

| Campo | Valor |
|-------|--------|
| **Root Directory** | `apps/api` |
| **Runtime** | Docker |

Erro `open Dockerfile: no such file or directory` = Root Directory vazio ou na raiz do monorepo.

### Environment Variables (Web Service)

| Variável | Valor |
|----------|--------|
| `DATABASE_URL` | URL do **Neon** (ou Supabase) — **não** `db:5432` |
| `CORS_ORIGINS` | `https://SEU-APP.vercel.app,http://localhost:5173` |
| `OPENAI_API_KEY` | sua chave (opcional) |
| `UPLOAD_DIR` | `/tmp/uploads` |

**Não** use “Link Database” do Render se você não tiver slot free de Postgres.

### Deploy

Manual Deploy → teste:

- `https://SUA-API.onrender.com/health` → `{"status":"ok",...}`
- `https://SUA-API.onrender.com/docs`

---

## 3. Frontend na Vercel

| Campo | Valor |
|-------|--------|
| **Root Directory** | `apps/web` |
| **Build** | `npm run build` |
| **Output** | `dist` |
| `VITE_API_URL` | `https://SUA-API.onrender.com` (sem `/` final, sem `/api`) |

Depois de salvar `VITE_API_URL` → **Redeploy** (variável Vite entra no build).

---

## 4. CORS

`CORS_ORIGINS` na API deve incluir a URL exata da Vercel (com `https://`, sem barra no final).

---

## 5. Opção: reutilizar Postgres do Public Data Monitor

Se quiser **um único** Postgres no Render:

1. No banco existente, crie outro database (via psql ou painel, se disponível):

   ```sql
   CREATE DATABASE job_match;
   ```

2. Monte `DATABASE_URL` apontando para esse database (mesmo host/user do PDM, nome `job_match`).

Cuidado: dois apps no mesmo cluster — ok para portfólio, evite em produção.

---

## 6. Limitações demo free

- Render Web Service “dorme” ~30s no primeiro hit.
- PDF em `/tmp/uploads` some no restart do container.
- OpenAI gera custo — limite na conta.

---

## Checklist

- [ ] `DATABASE_URL` aponta para Neon/Supabase (não host `db`)
- [ ] `/health` 200 no Render
- [ ] `VITE_API_URL` + redeploy Vercel
- [ ] Sem erro CORS no console do browser
- [ ] URLs no README
