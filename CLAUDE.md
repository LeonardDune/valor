# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Valor** is a collaborative causal policy analysis platform (deliberatief democratie tool) using the CAUSA framework. It allows organizations to model causal relationships between policy factors through Factors (nodes) and Claims (directed causal edges with polarity/confidence/evidence). The live domain is `valor-ecosystem.nl`.

## Architecture

**Two-service monorepo:**
- `backend/` — FastAPI (Python 3.11) + Neo4j AuraDB graph database
- `frontend/` — React 19 + TypeScript + Vite

**Key external services:**
- **Supabase** — Auth only (JWT tokens). Neo4j is the data store.
- **Resend** — Transactional email (invites)
- **OpenAI + CrewAI** — AI analysis agents

### Data Model (Neo4j Graph)

Core hierarchy: `Organization → Project → Theme → ThemeVersion`

The **Base/Version pattern** is central: immutable identity nodes (e.g. `ThemeBase`, `FactorBase`, `ClaimBase`) paired with mutable versioned state nodes (`ThemeVersion`, `FactorVersion`, `ClaimVersion`). Only one `ThemeVersion` per theme has `valid_to = NULL` — that's the active version.

**Factor roles** are stored on the `HAS_FACTOR` relationship (not on the Factor node itself) as a `role` property — this allows the same factor to have different roles in different contexts (middel, extern, systeemelement, criterium).

**RBAC** via `HAS_ROLE` relationships: roles are `admin`, `moderator`, `member`, `viewer`. Permissions cascade down the hierarchy; checked via `app/db/permissions.py`. Platform admins (`is_platform_admin: true` on User node) bypass all org-level checks.

**Auth flow:** Supabase issues JWTs → verified in `app/auth.py` (supports both HS256 secret and RS256/ES256 JWKS). On each request, `get_current_user` dependency JIT-syncs the Supabase user into Neo4j via `ensure_user_sync`.

**Real-time:** WebSocket at `/ws/{project_id}` (token via query param). `ConnectionManager` in `app/services/connection_manager.py` broadcasts presence and data mutation events (FACTOR_CREATED, CLAIM_UPDATED, etc.) to all clients in a project room.

**Deliberation pipeline:** Three-stage voting sessions (`refine → ranking → consent`) managed by `app/db/deliberation.py` and `app/routers/deliberation.py`. The `RefinementBoard` component drives UI for this.

**AI Agents:** CrewAI-based; `CausalAnalyst` and `DevilsAdvocate` agents assembled per perspective in `app/agent/crew.py`. Agent writes to the DB are currently disabled (production safety flag in `main.py`).

### Backend Structure

```
backend/app/
  main.py          # FastAPI app, all route definitions (large - ~820 lines), CORS, WebSocket
  auth.py          # JWT verification, get_current_user dependency
  models/domain.py # All Pydantic models + enums (FactorType, Role, DeliberationStage, etc.)
  db/
    crud.py        # Main DB layer (~60KB) — all Neo4j queries for core entities
    invites.py     # Invite creation, accept flow
    permissions.py # RBAC check_permission function
    deliberation.py # Voting sessions, feedback, ranking, consent votes
    sessions.py    # Session management
    dashboard.py   # Dashboard-specific queries
    utils.py       # Neo4j driver singleton, connectivity check
  routers/
    proposals.py   # Proposal lifecycle
    threads.py     # Conversation threads & messages
    sessions.py    # Voting session endpoints
    deliberation.py # Deliberation phase endpoints
  agent/
    core.py        # Entry point for AI message processing
    crew.py        # CrewAI orchestration
    agents.py      # Agent definitions (CausalAnalyst, DevilsAdvocate)
    registry.py    # Agent registry by perspective
    tasks.py       # Task factory functions
  services/
    connection_manager.py # WebSocket manager (single instance)
    email.py       # Resend email service
```

### Frontend Structure

```
frontend/src/
  App.tsx                    # Route definitions
  services/api.ts            # Axios client + all typed API calls + shared TS interfaces
  context/
    AuthContext.tsx           # Supabase session management
    OrganizationContext.tsx   # Active org + full hierarchy (orgs→projects→themes)
    ThemeContext.tsx          # Active theme state
  hooks/
    useWebSocket.ts           # WebSocket with auto-reconnect + Supabase token injection
    useForceLayout.ts         # D3 force simulation for graph
    useDomExport.ts           # PNG/PDF export
  components/
    Workspace/ValorWorkspace.tsx  # Main causal graph editor
    deliberation/             # ConsentBoard, RankingBoard, RefinementBoard, etc.
    graph/                    # Graph visualization components
    dashboard/                # OrganizationGrid, ProjectGrid, ThemeGrid
    Settings/MemberManagement.tsx
  pages/                     # Route-level page components
  views/shell/               # DashboardLayout, VersionLayout, PerspectivesLanding
```

**State management:** React Query for server state; Context API (not Redux) for auth/org hierarchy. The `OrganizationContext` loads the full org→project→theme tree on login. Supabase token is auto-injected into all axios requests via interceptor in `api.ts`.

## Development Commands

### Backend

```bash
# Run locally (from backend/)
cd backend
python -m uvicorn app.main:app --reload --port 8000

# Or via Docker (from root)
docker compose up

# Install dependencies
pip install -r requirements.txt

# Initialize a fresh dev DB (DESTROYS existing data)
cd backend && python scripts/init_dev_db.py

# Promote a user to platform admin
cd backend && python promote_admin.py <email>
```

Required env vars in `backend/.env`:
```
NEO4J_URI=neo4j+s://...
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=...
SUPABASE_URL=https://...supabase.co
SUPABASE_JWT_SECRET=...
OPENAI_API_KEY=...
RESEND_API_KEY=...
```

### Frontend

```bash
# Run dev server (from frontend/)
cd frontend
npm run dev        # http://localhost:5173

npm run build      # TypeScript check + Vite build
npm run lint       # ESLint
```

Required env vars in `frontend/.env`:
```
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
VITE_SUPABASE_URL=https://...supabase.co
VITE_SUPABASE_ANON_KEY=...
VITE_APP_URL=http://localhost:5173   # Used for invite redirect URLs
```

## Coding Standards

### Frontend
- **Env vars:** `import.meta.env.VITE_*` (Vite standaard)
- **TypeScript:** Strict mode, interfaces voor alle props/API responses, geen `any`
- **Componenten:** Functional components only, één per bestand, PascalCase bestandsnamen
- **Path aliases:** `import { Button } from "@/components/ui/button"`

### Design System (STRIKT)
- **Primair:** Shadcn/UI — Style: "New York", Color: Zinc, Icons: Lucide React
- **Complexe primitieven** niet in Shadcn: gebruik Radix UI (`@radix-ui/react-*`)
- **Geen vervangers:** Als een component ontbreekt, INSTALLEER het. Nooit een "vergelijkbaar" component als workaround.
  ```bash
  npm install @radix-ui/react-<component>
  # Maak daarna components/ui/<component>.tsx aan volgens Shadcn-patroon
  ```
- **Styling:** Tailwind utility classes + semantische tokens (`bg-destructive`, `text-muted-foreground`, `border-input`)
- **Geen hand-gemaakte** modals/popovers/tabs van divs

### Directory structuur
- UI componenten: `src/components/ui/` (Shadcn/Radix only)
- Feature componenten: `src/components/<feature-name>/`
- Globale CSS / design tokens: `src/index.css`

### API Architectuur
- **ALLE** backend-communicatie via `src/services/api.ts`
- **VERBODEN:** `fetch('/api/...')` direct in React componenten
- **VERPLICHT:** `await api.getDashboardEnvironments()` etc.

### Lokalisatie
- Alle gebruikersgerichte tekst, labels, knoppen in het **Nederlands**
- Fout: `"Open Workspace"` / Goed: `"Werkruimte Openen"`

### Identiteit & Context
- Geen placeholder IDs — gebruik altijd echte IDs
- Gebruik `useAuth()` hook, handel error/loading states expliciet af

### Backend
- **Env vars:** via `config.py` (Pydantic Settings) of `os.getenv`
- **Python:** Type hints op alle functiesignaturen
- **Testing:** Altijd een virtual environment (venv) gebruiken

## Key Conventions

- **Route placement:** Most API routes live directly in `main.py` (not in routers). Only proposals, threads, sessions, and deliberation have dedicated router files.
- **DB calls are async** using `await`, but the Neo4j driver itself is synchronous — it's run in a thread pool via the async driver or wrapped with `asyncio.to_thread`.
- **`/spaces/` routes** are deprecated aliases for `/versions/` — both exist in parallel for backward compatibility.
- **Factor type** is not stored on the FactorVersion node but derived from the `HAS_FACTOR` relationship `role` property when querying.
- **WebSocket broadcast** happens after every mutation (factors, claims) to update other clients in real-time.
- **No comprehensive test suite** — `backend/tests/` has one test file; most verification is done via `verify_*.py` scripts run manually against the DB.
- **`crud.py` is intentionally monolithic** — all core DB operations are in one file. When adding new DB operations, prefer adding to the appropriate domain module (`deliberation.py`, `invites.py`, etc.) rather than `crud.py`.

## Deployment

**Production (VPS/Coolify):** `docker-compose.prod.yml` — backend at `api.valor-ecosystem.nl`, frontend built as static Nginx container at `valor-ecosystem.nl`.

**Legacy:** Render (backend) + Vercel (frontend) via `render.yaml`.

After any Supabase auth configuration change, update Redirect URLs in the Supabase dashboard to include the app URL (required for invite and password-reset flows).
