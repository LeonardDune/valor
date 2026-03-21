"""Migratiescript: voeg baseId toe aan bestaande Fuseki Tesserae die het missen.

Het oude dual-write adapter schreef Tesserae zonder het <valor:baseId> predicaat.
De nieuwe create_factor_fuseki/create_claim_fuseki functie schrijft baseId wél.
Dit script voegt baseId toe door de UUID uit de tessera URI te extraheren.

Gebruik:
    python scripts/migrate_fuseki_add_base_id.py [--dry-run]

Idempotent: tesserae die al een baseId hebben worden overgeslagen.
"""
import sys
import os
import asyncio
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

DRY_RUN = "--dry-run" in sys.argv

TESSERA_PREFIX = "urn:valor:tessera:"


async def main():
    from app.services.fuseki import sparql_select_global, sparql_update
    from app.ontology import VALOR_NS

    # Vind alle DesignSpaces met hun asis-grafen
    ds_query = f"""
    SELECT DISTINCT ?ds WHERE {{
        GRAPH ?g {{
            ?t a <{VALOR_NS}Tessera> ;
               <{VALOR_NS}inDesignSpace> ?ds .
        }}
    }}
    """
    ds_rows = await sparql_select_global(ds_query)
    ds_uris = [r["ds"] for r in ds_rows if r.get("ds")]
    logger.info(f"Gevonden DesignSpaces met Tesserae: {len(ds_uris)}")

    total_patched = 0
    total_skipped = 0

    for ds_uri in ds_uris:
        # Extract ds_id from urn:valor:ds:{ds_id}
        ds_id = ds_uri.replace("urn:valor:ds:", "")
        asis_graph = f"urn:valor:ds:{ds_id}/asis"

        # Vind tesserae ZONDER baseId
        find_query = f"""
        SELECT ?tessera WHERE {{
            GRAPH <{asis_graph}> {{
                ?tessera a <{VALOR_NS}Tessera> .
                FILTER NOT EXISTS {{ ?tessera <{VALOR_NS}baseId> ?x }}
            }}
        }}
        """
        rows = await sparql_select_global(find_query)
        tesseras_missing = [r["tessera"] for r in rows if r.get("tessera")]

        if not tesseras_missing:
            logger.info(f"  DS {ds_id}: geen tesserae zonder baseId")
            total_skipped += len(rows)
            continue

        logger.info(f"  DS {ds_id}: {len(tesseras_missing)} tesserae missen baseId")

        for tessera_uri in tesseras_missing:
            if not tessera_uri.startswith(TESSERA_PREFIX):
                logger.warning(f"    Onverwacht URI-formaat: {tessera_uri} — overgeslagen")
                total_skipped += 1
                continue

            base_id = tessera_uri[len(TESSERA_PREFIX):]

            if DRY_RUN:
                logger.info(f"    [DRY-RUN] Zou toevoegen: <{tessera_uri}> baseId = {base_id}")
                total_patched += 1
                continue

            sparql = f"""
            INSERT DATA {{
                GRAPH <{asis_graph}> {{
                    <{tessera_uri}> <{VALOR_NS}baseId> "{base_id}" .
                }}
            }}
            """
            await sparql_update(sparql, ds_id)
            logger.info(f"    Toegevoegd: <{tessera_uri}> baseId = {base_id}")
            total_patched += 1

    logger.info(f"Klaar: {total_patched} tesserae gepatcht, {total_skipped} overgeslagen.")


if __name__ == "__main__":
    if DRY_RUN:
        logger.info("DRY-RUN modus — geen wijzigingen worden doorgevoerd.")
    asyncio.run(main())
