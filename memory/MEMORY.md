# Valor Project Memory

## Project Overview
**Valor** is a collaborative policy analysis platform (deliberatief democratie tool) voor causal policy analysis.
- Domain: Public Policy Analysis / Deliberative Democracy / CAUSA framework
- URL: valor-ecosystem.nl
- Active branch: fix/general-bugs

## Tech Stack
- **Backend:** FastAPI (Python 3.11) + Neo4j AuraDB + CrewAI + Supabase Auth + Resend email
- **Frontend:** React 19 + TypeScript + Vite + Tailwind v4 + Radix UI + React Query + D3.js
- **Deploy:** Docker/Coolify (VPS) + Vercel (legacy frontend) + Render (legacy backend)

## Key Architecture
- Hierarchical model: Organization → Project → Theme (versioned)
- Core entities: Factors → Claims (causal relationships with polarity/confidence/evidence)
- Base/Version pattern: ThemeBase (immutable identity) + ThemeVersion (mutable state)
- Factor roles via HAS_FACTOR relationship (not node attribute)
- RBAC: Admin, Moderator, Member, Viewer

## Important Files
- [backend/app/db/crud.py](backend/app/db/crud.py) - Large CRUD layer (~60KB), core DB operations
- [backend/app/db/invites.py](backend/app/db/invites.py) - Invite & membership management
- [backend/app/db/permissions.py](backend/app/db/permissions.py) - RBAC permission checks
- [backend/app/db/deliberation.py](backend/app/db/deliberation.py) - Voting sessions & consensus
- [backend/app/agent/](backend/app/agent/) - CrewAI agents (CausalAnalyst, DevilsAdvocate)
- [backend/app/main.py](backend/app/main.py) - FastAPI entry, CORS, routes
- [frontend/src/App.tsx](frontend/src/App.tsx) - Main routing & layout
- [frontend/src/context/](frontend/src/context/) - AuthContext, OrganizationContext, ThemeContext

## Known Technical Debt
1. crud.py is too large - needs splitting into domain modules
2. No comprehensive test suite (only verification scripts)
3. Multiple graph visualization libraries (D3, force-graph, reactflow) - could consolidate
4. ConnectionManager WebSocket single instance - may not scale
5. Mixed enum usage patterns

## Current Work
Branch `fix/general-bugs` has modifications to:
- invites.py, email.py, docker-compose.yml, requirements.txt