# Fontes de vagas

> Uso **educacional / portfólio**. Respeite os termos das plataformas; HTML e bloqueios podem mudar sem aviso.

O projeto usa **cadastro por URL**  não há agregador externo de vagas.

## Fluxo

1. Usuário cola o link da vaga (Gupy, LinkedIn, Inhire ou página com descrição).
2. A API importa o HTML, extrai título e descrição.
3. OpenAI (opcional) extrai `skills_required`, `seniority`, etc.
4. O motor ATS compara com o currículo salvo e devolve score + breakdown.

## Plataformas suportadas (import por URL)

| Plataforma | Como usar |
|------------|-----------|
| **Gupy** | Link direto da vaga (`*.gupy.io/jobs/...`) |
| **LinkedIn** | Link do post da vaga |
| **Inhire** | Link público da vaga |
| **Outras** | Qualquer página com JSON-LD `JobPosting` ou meta tags |
