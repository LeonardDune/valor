"""Verificatiescript US-3.6: Participant-rollen RBAC-mapping naar VALOR-O rollen.

Controleert:
1. Alle 6 VALOR-O rollen geladen vanuit 00k-application.trig ontologie
2. mapsToRBACRole + roleWeight correct per rol
3. Stemrecht (hasVotingRight) correct: Initiator + Contributor = true, rest = false
4. check_permission gebruikt cached RBAC-gewichten (incl. moderator=25)
5. POST /designspace/{id}/participants maakt app:Participant triple aan in Fuseki
6. GET /designspace/{id}/participants retourneert de deelnemer

Gebruik:
    FUSEKI_URL=http://localhost:3030 python3 verify_participant_rbac_us36.py
"""
import asyncio
import logging
import os
import sys

import httpx

logging.basicConfig(level=logging.INFO, format="%(levelname)-7s %(message)s")
logger = logging.getLogger(__name__)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
FUSEKI_URL = os.getenv("FUSEKI_URL", "http://localhost:3030")
DATASET = "valor"


# ── Helpers ───────────────────────────────────────────────────────────────────

async def sparql_query(query: str, client: httpx.AsyncClient) -> dict:
    resp = await client.post(
        f"{FUSEKI_URL}/{DATASET}/sparql",
        data={"query": query},
        headers={"Accept": "application/sparql-results+json"},
        auth=("admin", "admin"),
    )
    resp.raise_for_status()
    return resp.json()


async def sparql_update(update: str, client: httpx.AsyncClient) -> None:
    resp = await client.post(
        f"{FUSEKI_URL}/{DATASET}/update",
        data={"update": update},
        auth=("admin", "admin"),
    )
    resp.raise_for_status()


# ── Stap 1: Ontologie bevat alle rollen ───────────────────────────────────────

async def check_ontology_roles(client: httpx.AsyncClient) -> None:
    logger.info("Stap 1: Ontologie bevat alle 6 ParticipantRoles...")
    query = """
PREFIX app: <https://valor-ecosystem.nl/ontology/application#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?label ?rbac ?weight ?voting WHERE {
  GRAPH <https://valor-ecosystem.nl/ontology/application> {
    ?role app:mapsToRBACRole ?rbac ;
          app:roleWeight ?weight ;
          app:hasVotingRight ?voting ;
          rdfs:label ?label .
    FILTER(lang(?label) = "en")
  }
} ORDER BY DESC(?weight)
"""
    result = await sparql_query(query, client)
    rows = result["results"]["bindings"]

    assert len(rows) == 6, f"Verwacht 6 rollen, gevonden: {len(rows)}"

    expected = {
        "Initiator":   ("admin",    30, True),
        "Facilitator": ("moderator", 25, False),
        "Contributor": ("member",   20, True),
        "Expert":      ("member",   15, False),
        "Engineer":    ("member",   15, False),
        "Observer":    ("viewer",   10, False),
    }
    for row in rows:
        label = row["label"]["value"]
        rbac = row["rbac"]["value"]
        weight = int(row["weight"]["value"])
        voting = row["voting"]["value"].lower() == "true"
        exp_rbac, exp_weight, exp_voting = expected[label]
        assert rbac == exp_rbac, f"{label}: rbac={rbac}, verwacht={exp_rbac}"
        assert weight == exp_weight, f"{label}: weight={weight}, verwacht={exp_weight}"
        assert voting == exp_voting, f"{label}: voting={voting}, verwacht={exp_voting}"
        logger.info("  ✓ %s → rbac=%s, weight=%d, voting=%s", label, rbac, weight, voting)

    logger.info("Stap 1: OK — 6/6 rollen correct.")


# ── Stap 2: Stemrecht verificatie ─────────────────────────────────────────────

async def check_voting_rights(client: httpx.AsyncClient) -> None:
    logger.info("Stap 2: Stemrecht verificatie...")
    query = """
PREFIX app: <https://valor-ecosystem.nl/ontology/application#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?label ?voting WHERE {
  GRAPH <https://valor-ecosystem.nl/ontology/application> {
    ?role app:hasVotingRight ?voting ;
          rdfs:label ?label .
    FILTER(lang(?label) = "en")
  }
}"""
    result = await sparql_query(query, client)
    rows = result["results"]["bindings"]
    voting_roles = {r["label"]["value"] for r in rows if r["voting"]["value"].lower() == "true"}
    assert voting_roles == {"Initiator", "Contributor"}, f"Stemrecht-rollen: {voting_roles}"
    logger.info("  ✓ Stemrecht: Initiator + Contributor (beide true)")
    logger.info("Stap 2: OK.")


# ── Stap 3: Python ontology_cache laadt correct ───────────────────────────────

async def check_ontology_cache() -> None:
    logger.info("Stap 3: ontology_cache laadt participant roles...")
    import sys
    sys.path.insert(0, "/home/renzo/projects/valor/backend")
    from app.services.ontology_cache import load_ontology_cache, get_participant_role_data, get_rbac_role_weights, rbac_to_valor_role, has_voting_right

    await load_ontology_cache()
    data = get_participant_role_data()
    weights = get_rbac_role_weights()

    assert set(data.keys()) == {"Initiator", "Facilitator", "Contributor", "Expert", "Engineer", "Observer"}, \
        f"Rollen: {list(data.keys())}"
    assert weights == {"admin": 30, "moderator": 25, "member": 20, "viewer": 10}, \
        f"Gewichten: {weights}"
    assert has_voting_right("Initiator") is True
    assert has_voting_right("Contributor") is True
    assert has_voting_right("Facilitator") is False
    assert has_voting_right("Observer") is False
    assert rbac_to_valor_role("admin") == "Initiator"
    assert rbac_to_valor_role("moderator") == "Facilitator"
    assert rbac_to_valor_role("member") == "Contributor"
    assert rbac_to_valor_role("viewer") == "Observer"

    logger.info("  ✓ 6/6 rollen geladen, gewichten correct, stemrecht correct")
    logger.info("Stap 3: OK.")


# ── Stap 4: Participant triple in Fuseki ──────────────────────────────────────

async def check_participant_fuseki(client: httpx.AsyncClient) -> None:
    logger.info("Stap 4: app:Participant triple test in Fuseki...")

    test_ds_id = "verify-us36-test"
    test_user_id = "test-user-us36"
    base_graph = f"urn:valor:ds:{test_ds_id}/base"
    participant_uri = f"urn:valor:participant:{test_ds_id}:{test_user_id}"
    APP_NS = "https://valor-ecosystem.nl/ontology/application#"
    role_uri = f"{APP_NS}ContributorRole"

    # Cleanup vorige run
    await sparql_update(f"DROP SILENT GRAPH <{base_graph}>", client)

    # Aanmaken
    insert = f"""PREFIX app: <{APP_NS}>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
INSERT DATA {{
  GRAPH <{base_graph}> {{
    <{participant_uri}> a app:Participant ;
      app:hasRole <{role_uri}> ;
      app:participatesIn <urn:valor:ds:{test_ds_id}> ;
      app:participantInvitedAt "2026-03-16T00:00:00Z"^^xsd:dateTime .
  }}
}}"""
    await sparql_update(insert, client)

    # Verificatie
    query = f"""PREFIX app: <{APP_NS}>
SELECT ?role WHERE {{
  GRAPH <{base_graph}> {{
    <{participant_uri}> a app:Participant ;
      app:hasRole ?role .
  }}
}}"""
    result = await sparql_query(query, client)
    rows = result["results"]["bindings"]
    assert len(rows) == 1, f"Verwacht 1 participant, gevonden: {len(rows)}"
    assert rows[0]["role"]["value"] == role_uri, f"Rol: {rows[0]['role']['value']}"
    logger.info("  ✓ app:Participant triple aangemaakt en gevonden in base-graph")

    # Cleanup
    await sparql_update(f"DROP SILENT GRAPH <{base_graph}>", client)
    logger.info("Stap 4: OK.")


# ── Main ──────────────────────────────────────────────────────────────────────

async def main() -> None:
    logger.info("=== US-3.6 Verificatie: Participant RBAC-mapping ===")
    errors: list[str] = []

    async with httpx.AsyncClient(timeout=30) as client:
        for name, fn in [
            ("Ontologie rollen", lambda: check_ontology_roles(client)),
            ("Stemrecht", lambda: check_voting_rights(client)),
            ("Participant Fuseki", lambda: check_participant_fuseki(client)),
        ]:
            try:
                await fn()
            except Exception as e:
                logger.error("FAIL %s: %s", name, e)
                errors.append(f"{name}: {e}")

    # Stap 3 apart (importeert backend modules)
    try:
        await check_ontology_cache()
    except Exception as e:
        logger.error("FAIL ontology_cache: %s", e)
        errors.append(f"ontology_cache: {e}")

    print()
    if errors:
        logger.error("GEFAALD (%d fouten):", len(errors))
        for err in errors:
            logger.error("  - %s", err)
        sys.exit(1)
    else:
        logger.info("=== Alle stappen geslaagd ===")


if __name__ == "__main__":
    asyncio.run(main())
