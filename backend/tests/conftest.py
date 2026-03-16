"""Pytest fixtures voor Fuseki integratietests.

Vereisten:
  - Fuseki draait op FUSEKI_URL (default: http://localhost:3030)
  - Dataset 'valor-test' wordt aangemaakt en na de sessie verwijderd
  - Elke test krijgt een schone DesignSpace via de `ds_id` fixture

Gebruik:
    cd backend
    FUSEKI_URL=http://localhost:3030 pytest tests/integration/ -v
"""
import os
import sys

import httpx
import pytest

# Zet FUSEKI_URL vóór app-imports zodat de module-level defaults kloppen
FUSEKI_TEST_URL = os.environ.setdefault("FUSEKI_URL", "http://localhost:3030")
FUSEKI_TEST_DATASET = "valor-test"
FUSEKI_ADMIN_PASSWORD = os.getenv("FUSEKI_ADMIN_PASSWORD", "admin")

# Zorg dat backend/ op het pad staat
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _http_update(update: str) -> None:
    url = f"{FUSEKI_TEST_URL}/{FUSEKI_TEST_DATASET}/update"
    async with httpx.AsyncClient() as client:
        r = await client.post(
            url,
            data={"update": update},
            auth=("admin", FUSEKI_ADMIN_PASSWORD),
            timeout=15,
        )
        r.raise_for_status()


async def _create_dataset() -> None:
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{FUSEKI_TEST_URL}/$/datasets",
            data={"dbName": FUSEKI_TEST_DATASET, "dbType": "mem"},
            auth=("admin", FUSEKI_ADMIN_PASSWORD),
            timeout=15,
        )
        # 409 = dataset bestaat al — geen probleem
        if r.status_code not in (200, 201, 409):
            r.raise_for_status()


async def _delete_dataset() -> None:
    async with httpx.AsyncClient() as client:
        await client.delete(
            f"{FUSEKI_TEST_URL}/$/datasets/{FUSEKI_TEST_DATASET}",
            auth=("admin", FUSEKI_ADMIN_PASSWORD),
            timeout=15,
        )


async def _clear_all_graphs() -> None:
    await _http_update("CLEAR ALL")


def _seed_ontology_cache() -> None:
    """Vult de ontologie-cache handmatig met minimale testwaarden.

    Vermijdt dat tests afhankelijk zijn van een geladen VALOR-O ontologie.
    """
    from app.ontology import VALOR_NS
    from app.services import ontology_cache

    ontology_cache._argue_label_to_uri = {
        "supports": f"{VALOR_NS}supports",
        "undermines": f"{VALOR_NS}undermines",
    }
    ontology_cache._status_label_to_uri = {
        "Proposed": f"{VALOR_NS}ProposedStatus",
        "Accepted": f"{VALOR_NS}AcceptedStatus",
        "NotFeasible": f"{VALOR_NS}NotFeasible",
        "NotCovered": f"{VALOR_NS}NotCovered",
    }
    ontology_cache._status_uri_to_label = {
        v: k for k, v in ontology_cache._status_label_to_uri.items()
    }


# ---------------------------------------------------------------------------
# Sessie-scoped fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
async def fuseki_test_session():
    """Maakt de 'valor-test' dataset aan, patcht de fuseki-module en ruimt op."""
    # 1. Dataset aanmaken
    await _create_dataset()

    # 2. Patch app.services.fuseki zodat alle functies 'valor-test' gebruiken
    import app.services.fuseki as fs

    original = {
        "FUSEKI_URL": fs.FUSEKI_URL,
        "FUSEKI_DATASET": fs.FUSEKI_DATASET,
        "FUSEKI_ADMIN_PASSWORD": fs.FUSEKI_ADMIN_PASSWORD,
        "_SPARQL_ENDPOINT": fs._SPARQL_ENDPOINT,
        "_UPDATE_ENDPOINT": fs._UPDATE_ENDPOINT,
        "_SHACL_ENDPOINT": fs._SHACL_ENDPOINT,
    }
    fs.FUSEKI_URL = FUSEKI_TEST_URL
    fs.FUSEKI_DATASET = FUSEKI_TEST_DATASET
    fs.FUSEKI_ADMIN_PASSWORD = FUSEKI_ADMIN_PASSWORD
    fs._SPARQL_ENDPOINT = f"{FUSEKI_TEST_URL}/{FUSEKI_TEST_DATASET}/sparql"
    fs._UPDATE_ENDPOINT = f"{FUSEKI_TEST_URL}/{FUSEKI_TEST_DATASET}/update"
    fs._SHACL_ENDPOINT = f"{FUSEKI_TEST_URL}/{FUSEKI_TEST_DATASET}/shacl"

    # 3. Ontologie-cache zaaien met minimale testwaarden
    _seed_ontology_cache()

    yield

    # 4. Teardown
    for k, v in original.items():
        setattr(fs, k, v)
    await _delete_dataset()


# ---------------------------------------------------------------------------
# Test-scoped fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
async def clean_fuseki_graphs():
    """Verwijdert alle graphs in 'valor-test' na elke test."""
    yield
    await _clear_all_graphs()
    # Ontologie-cache opnieuw zaaien (CLEAR ALL wist ook seeded data)
    _seed_ontology_cache()


@pytest.fixture
def ds_id() -> str:
    """Geeft een vaste DesignSpace-ID voor gebruik in integratietests."""
    return "test-ds-integration"


@pytest.fixture
def user_uri() -> str:
    return "urn:valor:user:test-user-001"
