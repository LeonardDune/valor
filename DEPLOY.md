# Deployment Guide (Coolify & Self-Hosting)

Dit is de primaire deployment methode voor de Valor applicatie op een eigen VPS met Coolify.

## 1. Voorbereiding (VPS)
- Zorg dat **Coolify** is geïnstalleerd op je VPS.
- Koppel je GitHub repository (`LeonardDune/valor`) aan Coolify via een GitHub App.

## 2. Backend Setup (api.valor-ecosystem.nl)
1. **Service:** Maak een nieuwe "Application" aan in Coolify.
2. **Context:** Zet de `Base Directory` op `/backend`.
3. **Dockerfile:** Coolify detecteert automatisch de `Dockerfile` in de `/backend` map.
4. **Environment Variables:**
   - `NEO4J_URI`: `neo4j+s://<jouw-id>.databases.neo4j.io`
   - `NEO4J_USER`: `neo4j`
   - `NEO4J_PASSWORD`: (Je wachtwoord)
   - `OPENAI_API_KEY`: (Je OpenAI API Key)
   - `RESEND_API_KEY`: (Je Resend API Key)
   - `PORT`: `8000`
5. **Domains:** Stel in op `https://api.valor-ecosystem.nl`.

## 3. Frontend Setup (valor-ecosystem.nl)
1. **Service:** Maak een nieuwe "Application" aan in Coolify.
2. **Context:** Zet de `Base Directory` op `/frontend`.
3. **Dockerfile:** Coolify gebruikt de `Dockerfile` in `/frontend` (multi-stage build met Nginx).
4. **Build Arguments:**
   - `VITE_API_URL`: `https://api.valor-ecosystem.nl`
5. **Domains:** Stel in op `https://valor-ecosystem.nl`.

---

# Alternatieve Hosting (Legacy)

## 1. Backend (Render)
Zie `render.yaml` en de Render dashboard instellingen.

## 2. Frontend (Vercel)
Zie de Vercel project instellingen (Root: `frontend`).

## Workflow (Testen & Veiligheid)
- **Branch Keuze**: Je kunt in Coolify per applicatie instellen welke branch gemonitord moet worden.
- **Isolatie**: Voor de initiële test raden we aan om Coolify te verbinden met de branch `feature/coolify-migration`. Hierdoor blijft de `main` branch onaangeroerd en blijven Vercel/Render gewoon de huidige productie draaien.
- **Promotie**: Zodra de VPS omgeving 100% stabiel is, kun je in Coolify de branch omzetten naar `main` (of een aparte `production-vps` branch aanhouden).

*   **Dev:** Lokaal ontwikkelen op `feature/*` branches met `docker compose`.
*   **Prod (Legacy):** Merge naar `main` triggert Vercel/Render.
*   **Prod (VPS/Beta):** Push naar de geselecteerde branch in Coolify triggert de VPS deployment.
