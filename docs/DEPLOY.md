# Deploy  demo pública (portfólio)

Objetivo: **link da API (Swagger)** + **link da UI** sem transformar o projeto em produto.

## Visão

| Componente | Onde | Por quê |
|------------|------|---------|
| API + Postgres | **Render** (ou Railway) | FastAPI + banco persistente, igual ao Public Data Monitor |
| Frontend | **Vercel** | Build estático do Vite; barato e rápido |

## 1. API no Render

1. Crie um **PostgreSQL** no Render e copie a `DATABASE_URL` interna (`postgresql+asyncpg://...`).
2. **Web Service** conectado ao repositório:
   - **Root Directory:** `apps/api` (ou build na raiz com Dockerfile em `apps/api`)
   - **Build:** `pip install .`
   - **Start:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Variáveis de ambiente:
   - `DATABASE_URL`  URL asyncpg do Postgres Render
   - `CORS_ORIGINS`  URL da Vercel (ex.: `https://job-match-alerts.vercel.app`)
   - `OPENAI_API_KEY`  opcional; sem ela, parte do parse/análise fica limitada
   - `UPLOAD_DIR`  `/tmp/uploads` ou disco efêmero do Render (PDFs não persistem entre deploys no plano free  aceitável para demo)
4. Após deploy, teste:
   - `https://SUA-API.onrender.com/health`
   - `https://SUA-API.onrender.com/docs`

Atualize o README com essas URLs na seção **Demo online**.

## 2. Frontend na Vercel

1. Importe o repositório na Vercel.
2. **Root Directory:** `apps/web`
3. **Build Command:** `npm run build`
4. **Output Directory:** `dist`
5. Variável de ambiente:
   - `VITE_API_URL` = `https://SUA-API.onrender.com` (sem barra final)
6. O arquivo `apps/web/vercel.json` já configura SPA fallback.

Redeploy após mudar `VITE_API_URL`.

## 3. CORS

Na API, `CORS_ORIGINS` deve incluir exatamente a origem da Vercel. Exemplo:

```env
CORS_ORIGINS=https://job-match-alerts.vercel.app,http://localhost:5173
```

## 4. Limitações da demo free

- Render free “dorme”  primeiro acesso pode demorar ~30s.
- Uploads em disco efêmero  PDF some após restart; para demo, reimportar é ok.
- LinkedIn/Gupy podem bloquear ou mudar HTML no servidor remoto.
- OpenAI gera custo por uso  defina limite na conta OpenAI.

## 5. Alternativa: só API pública

Se não quiser Vercel agora, publique **apenas a API** e use o Swagger como demo principal (como no Public Data Monitor). A UI local continua válida para screenshots no README.

## Checklist pós-deploy

- [ ] Health 200
- [ ] Swagger abre
- [ ] UI na Vercel chama API (sem erro CORS no console)
- [ ] URLs no README atualizadas
- [ ] Screenshot em `docs/images/swagger-home.png`
