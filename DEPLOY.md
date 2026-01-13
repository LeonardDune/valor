# Deployment Guide (Vercel & Render)

## 1. Backend (Render)

We gebruiken **Render** voor de backend omdat het native Docker container ondersteuning biedt.

### Setup
1.  Ga naar [dashboard.render.com](https://dashboard.render.com/).
2.  Klik op **New +** -> **Blueprint**.
3.  Koppel je GitHub repository (`LeonardDune/valor`).
4.  Render detecteert automatisch `render.yaml` en stelt de service `valor-backend` voor.
5.  Klik op **Apply**.

### Environment Variables
Render zal vragen om de waarden voor de variabelen die in `render.yaml` als `sync: false` staan:
*   `NEO4J_URI`: `neo4j+s://<jouw-id>.databases.neo4j.io`
*   `NEO4J_USERNAME`: `neo4j`
*   `NEO4J_PASSWORD`: (Je wachtwoord)
*   `SUPABASE_URL`: (Van Supabase dashboard)
*   `SUPABASE_KEY`: (Anon key van Supabase)
*   `JWT_SECRET`: (Je Supabase JWT secret, zie API instellingen)

---

## 2. Frontend (Vercel)

We gebruiken **Vercel** voor de frontend (React/Vite).

### Setup
1.  Ga naar [vercel.com/new](https://vercel.com/new).
2.  Importeer de `LeonardDune/valor` repository.
3.  **Belangrijk:** Vercel herkent dit als een monorepo (misschien).
    *   **Root Directory:** Kies `frontend` (klik op Edit naast Root Directory).
    *   **Framework Preset:** Vite
    *   **Build Command:** `tsc -b && vite build` (of standaard `npm run build` als package.json klopt)
    *   **Output Directory:** `dist`

### Environment Variables
Voeg de volgende variabelen toe in het Vercel scherm voordat je op Deploy klikt:

*   `VITE_API_URL`: De URL van je Render backend (bijv. `https://valor-backend.onrender.com`)
*   `VITE_SUPABASE_URL`: Je Supabase project URL (via Dashboard -> Settings -> API)
*   `VITE_SUPABASE_ANON_KEY`: Je Supabase Anon/Public key (via Dashboard -> Settings -> API)

### Deploy
Klik op **Deploy**.

---

## 3. Workflow
*   **Dev:** Lokaal ontwikkelen op `feature/*` branches met `docker compose`.
*   **Test:** Pull Request openen. Vercel maakt automatisch een **Preview URL** (deze praat standaard met de Productie Backend, tenzij je VITE_API_URL overschrijft per environment).
*   **Prod:** Merge naar `main`. Render en Vercel updaten automatisch de live sites.
