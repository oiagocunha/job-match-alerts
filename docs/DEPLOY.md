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

### Passo B — Copiar dados no Supabase

**Project Settings → Database → Connection string → URI → Session mode (porta 5432)**

Anote (não cole a URI inteira no Render):

| Campo Supabase | Variável Render |
|----------------|-----------------|
| Host (`db.xxxx.supabase.co`) | `DB_HOST` |
| User (`postgres` ou `postgres.xxxx`) | `DB_USER` |
| Password (Reveal) | `DB_PASSWORD` |
| Port `5432` | `DB_PORT` |
| Database `postgres` | `DB_NAME` |

No Render, crie **só estas** env vars:

```env
DB_HOST=db.xxxxxxxxxxxx.supabase.co
DB_USER=postgres
DB_PASSWORD=cole-a-senha-crua-aqui-sem-uri
DB_PORT=5432
DB_NAME=postgres
DB_SSL=true
CORS_ORIGINS=https://seu-app.vercel.app,http://localhost:5173
UPLOAD_DIR=/tmp/uploads
OPENAI_API_KEY=sk-...
```

**Não** defina `DATABASE_URL` ao mesmo tempo ( `DB_*` tem prioridade).

Save → **Manual Deploy**. No log deve aparecer: `DB config via DB_* parts, host=db.xxxx.supabase.co`.

### Passo C — Se ainda falhar no Supabase

- **Settings → Database → Network**: projeto novo costuma aceitar qualquer IP; em plano pago confira restrições.
- Tente **Direct connection** (host `db....supabase.co`, porta **5432**), não Transaction pooler na primeira vez.
- **Reset database password** no Supabase e atualize só `DB_PASSWORD`.

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
| `CORS_ORIGINS` | `https://SEU-APP.vercel.app,http://localhost:5173` |
| `OPENAI_API_KEY` | sua chave (opcional) |
| `UPLOAD_DIR` | `/tmp/uploads` |

**Não** use “Link Database” do Render no Job Match Alerts.

### Deploy

Manual Deploy → teste:

- `https://SUA-API.onrender.com/health` → `{"status":"ok",...}`
- `https://SUA-API.onrender.com/docs`

---

## 4. Frontend na Vercel

| Campo | Valor |
|-------|--------|
| **Root Directory** | `apps/web` |
| **Build** | `npm run build` |
| **Output** | `dist` |
| `VITE_API_URL` | `https://SUA-API.onrender.com` (sem `/` final, sem `/api`) |

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

- [ ] `DATABASE_URL` aponta para Neon/Supabase (não host `db`)
- [ ] `/health` 200 no Render
- [ ] `VITE_API_URL` + redeploy Vercel
- [ ] Sem erro CORS no console do browser
- [ ] URLs no README
