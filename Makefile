# Valor — veelgebruikte commando's

# ── Backend ──────────────────────────────────────────────────────────────────
.PHONY: test test-integration test-unit

# Alle tests (unit + integratie)
test:
	cd backend && FUSEKI_URL=http://localhost:3030 pytest -v

# Alleen integratietests (vereist draaiende Fuseki)
test-integration:
	cd backend && FUSEKI_URL=http://localhost:3030 pytest tests/integration/ -v -m integration

# Alleen unittests (geen Fuseki nodig)
test-unit:
	cd backend && pytest tests/ -v -m "not integration"

# Fuseki + backend lokaal opstarten
up:
	docker compose up fuseki fuseki-loader --detach
	cd backend && uvicorn app.main:app --reload --port 8000

# Alleen Fuseki opstarten (voor testontwikkeling)
fuseki:
	docker compose up fuseki fuseki-loader --detach
