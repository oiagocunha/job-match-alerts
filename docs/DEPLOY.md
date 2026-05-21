# Deploy — demo pública (portfólio)

Objetivo: **link da API (Swagger)** + **link da UI** sem transformar o projeto em produto.

## Demo ao vivo (referência)

| Camada | URL |
|--------|-----|
| UI (Vercel) | https://job-match-alerts-gut16pzvo-oiagocunhas-projects.vercel.app |
| API (Render) | https://job-match-alerts.onrender.com — [/docs](https://job-match-alerts.onrender.com/docs) · [/health](https://job-match-alerts.onrender.com/health) |
| DB | Supabase Postgres (Session pooler) |

## Visão

| Componente | Onde | Por quê |
|------------|------|---------|
| **API** | Render (Web Service, Docker) | FastAPI — igual ao Public Data Monitor |
| **Postgres** | **Supabase** (recomendado) ou Neon | Render free = **1 banco por conta**; se já existe o do `public-data-monitor`, use Postgres externo |
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
2. Ajuste para asyncpg (a API também converte `postgresql://` automaticamente).

3. **Senha com caracteres especiais (`?`, `@`, `#`, `%`):** use a URI que o Supabase gera ao clicar em **Copy** (já vem encoded).  
   Se colar a senha “crua”, a URL quebra e o host vira `postgres` no log.

   ```env
   DATABASE_URL=postgresql+asyncpg://postgres.xxxxx:SENHA_ENCODED@aws-0-xx.pooler.supabase.com:5432/postgres
   ```

   Exemplo Neon (SSL):

   ```env
   DATABASE_URL=postgresql+asyncpg://user:pass@ep-xxxx.neon.tech/neondb?sslmode=require
   ```

3. Guarde a URL; vai no Render abaixo.

---

## 2. Supabase + Render (recomendado — sem `DATABASE_URL`)

O Render **não rejeita** o Supabase. O que acontece na prática:

1. **“Link Database”** no Web Service injeta URL do Postgres **do Render** (`host=postgres` ou `db`) e **sobrescreve** o que você colou.
2. **`DATABASE_URL` com senha `?`, `@`, `#`** quebra o parse → log `host='postgres'`.

### Passo A — Desvincular banco do Render

No Web Service da API → **Environment**:

- Se existir **Linked Postgres** / **Add from database** → **Unlink** / remova o vínculo.
- **Apague** a variável `DATABASE_URL` (ou deixe vazia) se o valor tiver `postgres` como host ou `@db:`.

O app passa a usar variáveis **`DB_*`** (mais seguro no painel).

### Passo B — Copiar dados no Supabase (Session **pooler**, não Direct)

No Supabase: **Connect → Session pooler** (porta **5432**).  
**Não use** Direct (`db.xxxx.supabase.co`) no Render — conexão direta é IPv6 e o plano free do Render costuma falhar com `Network is unreachable`.

| Campo na tela Supabase | Variável Render |
|------------------------|-----------------|
| Host (`aws-0-….pooler.supabase.com`) | `DB_HOST` |
| User (`postgres.SEU_PROJECT_REF`) | `DB_USER` |
| Password (Reveal) | `DB_PASSWORD` |
| Port `5432` | `DB_PORT` |
| Database `postgres` | `DB_NAME` |

No Render, crie **só estas** env vars (valores do **seu** projeto no Supabase — nunca commite senha no repo):

```env
DB_HOST=aws-0-REGIAO.pooler.supabase.com
DB_USER=postgres.SEU_PROJECT_REF
DB_PASSWORD=<senha do painel Supabase>
DB_PORT=5432
DB_NAME=postgres
DB_SSL=true
CORS_ORIGINS=https://seu-app.vercel.app,http://localhost:5173
UPLOAD_DIR=/tmp/uploads
OPENAI_API_KEY=sk-...
```

> **TLS:** o pooler do Supabase apresenta cert auto-assinado na cadeia; a API usa `ssl=require` (criptografa sem verificar), igual ao `sslmode=require` do libpq. Para verificação completa, defina `DB_SSL_VERIFY=full` (precisa cert da CA no container).

Substitua host/user pelos valores **exatos** do seu projeto (região e ref aparecem na string do Supabase).

**Não** defina `DATABASE_URL` ao mesmo tempo (`DB_*` tem prioridade).

Save → **Manual Deploy**. No log: `host=aws-0-….pooler.supabase.com` (não `db.….supabase.co`).

### Passo C — Se ainda falhar

- Confirma **Session pooler**, não Direct nem Transaction (6543) na primeira subida.
- **Settings → Database → Network**: allow all IPs em projetos novos.
- Reset da senha no Supabase → atualize só `DB_PASSWORD`.

---

## 3. API no Render (sem criar Postgres lá)

### Root Directory (obrigatório)

| Campo | Valor |
|-------|--------|
| **Root Directory** | `apps/api` |
| **Runtime** | Docker |

Erro `open Dockerfile: no such file or directory` = Root Directory vazio ou na raiz do monorepo.

### Environment Variables (Web Service)

Preferir **`DB_*`** (seção 2). Alternativa: uma única `DATABASE_URL` (Neon/Supabase URI já encoded).

| Variável | Valor |
|----------|--------|
| `CORS_ORIGINS` | `https://job-match-alerts.vercel.app,http://localhost:5173` |
| `OPENAI_API_KEY` | sua chave (opcional) |
| `UPLOAD_DIR` | `/tmp/uploads` |

**Não** use “Link Database” do Render no Job Match Alerts.

### Deploy

Manual Deploy → teste (URL deste projeto):

- https://job-match-alerts.onrender.com/health → `{"status":"ok",...}`
- https://job-match-alerts.onrender.com/docs

---

## 4. Frontend na Vercel

| Campo | Valor |
|-------|--------|
| **Root Directory** | `apps/web` |
| **Build** | `npm run build` |
| **Output** | `dist` |
| `VITE_API_URL` | `https://job-match-alerts.onrender.com` (sem `/` final, sem `/api`) |

Depois de salvar `VITE_API_URL` → **Redeploy** (variável Vite entra no build).

---

## 5. CORS

`CORS_ORIGINS` na API deve incluir a URL exata da Vercel (com `https://`, sem barra no final).

---

## 6. Opção: reutilizar Postgres do Public Data Monitor

Se quiser **um único** Postgres no Render:

1. No banco existente, crie outro database (via psql ou painel, se disponível):

   ```sql
   CREATE DATABASE job_match;
   ```

2. Monte `DATABASE_URL` apontando para esse database (mesmo host/user do PDM, nome `job_match`).

Cuidado: dois apps no mesmo cluster — ok para portfólio, evite em produção.

---

## 7. Limitações demo free

- Render Web Service “dorme” ~30s no primeiro hit.
- PDF em `/tmp/uploads` some no restart do container.
- OpenAI gera custo — limite na conta.

---

## Checklist

- [x] `DB_*` apontando para Supabase Session pooler (não host `db.*.supabase.co`)
- [x] `/health` 200 no Render
- [x] `VITE_API_URL` + redeploy Vercel
- [x] Sem erro CORS no console do browser
- [x] URLs no README
