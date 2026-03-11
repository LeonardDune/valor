#!/bin/sh
# load-ontology.sh — incrementele VALOR-O ontologie-loader voor Fuseki
#
# Gebruik: load-ontology.sh [--force]
#
#   --force  Verwijdert alle ontologie-graphs en herlaadt alles opnieuw.
#            Gebruik bij een full reset of dev-omgeving cleanup.
#
# Per-module versie-tracking in named graph urn:valor:ontology-modules.
# Modules worden alleen geladen als ze nieuw zijn of een andere versie hebben.
# Bij een versiewijziging wordt de oude graph gearchiveerd als {graph}/v{versie}.
set -e

FUSEKI_URL="${FUSEKI_URL:-http://fuseki:3030}"
FUSEKI_ADMIN_PASSWORD="${FUSEKI_ADMIN_PASSWORD:-admin}"
DATASET="${DATASET:-valor}"
ONTOLOGY_REPO="${ONTOLOGY_REPO:-https://github.com/LeonardDune/valor-ontology.git}"
MODULES_GRAPH="urn:valor:ontology-modules"
AUTH="-u admin:${FUSEKI_ADMIN_PASSWORD}"
FORCE=false

for arg in "$@"; do
  case "$arg" in --force) FORCE=true ;; esac
done

# ── Tools installeren ────────────────────────────────────────────────────────
echo "[fuseki-loader] Benodigde tools installeren..."
if command -v apk > /dev/null 2>&1; then
  apk add --no-cache curl git > /dev/null 2>&1
elif command -v apt-get > /dev/null 2>&1; then
  apt-get update -qq && apt-get install -y --no-install-recommends curl git > /dev/null 2>&1
fi

# ── Wachten op Fuseki ────────────────────────────────────────────────────────
echo "[fuseki-loader] Wachten op Fuseki..."
until curl -sf "${FUSEKI_URL}/\$/ping" > /dev/null; do
  sleep 2
done
echo "[fuseki-loader] Fuseki is bereikbaar."

# ── Dataset aanmaken indien nodig ────────────────────────────────────────────
curl -sf $AUTH \
  -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data "dbName=${DATASET}&dbType=tdb2" \
  "${FUSEKI_URL}/\$/datasets" > /dev/null 2>&1 || true

# ── Helpers ──────────────────────────────────────────────────────────────────

sparql_ask() {
  curl -sf $AUTH \
    --data-urlencode "query=$1" \
    "${FUSEKI_URL}/${DATASET}/query" \
    -H "Accept: application/sparql-results+json" | \
    grep -o '"boolean"[[:space:]]*:[[:space:]]*[a-z]*' | grep -o '[a-z]*$' || echo "false"
}

sparql_select_value() {
  # Retourneert de eerste ?value uit een SELECT-resultaat
  curl -sf $AUTH \
    --data-urlencode "query=$1" \
    "${FUSEKI_URL}/${DATASET}/query" \
    -H "Accept: application/sparql-results+json" | \
    grep -o '"value":"[^"]*"' | head -1 | sed 's/"value":"//;s/"//' || echo ""
}

sparql_update() {
  curl -sf $AUTH \
    -X POST \
    --data-urlencode "update=$1" \
    "${FUSEKI_URL}/${DATASET}/update"
}

extract_graph_uri() {
  # Eerste regel van de vorm <...> { — ook urn: en andere schemata
  grep -m1 '^<' "$1" | sed 's/[[:space:]]*{.*//' | tr -d '<>' || echo ""
}

extract_version() {
  # owl:versionInfo "0.1"
  grep -m1 'versionInfo' "$1" | grep -o '"[^"]*"' | head -1 | tr -d '"' || echo ""
}

file_fingerprint() {
  # Fallback voor bestanden zonder owl:versionInfo (bv. SHACL-files)
  md5sum "$1" 2>/dev/null | cut -c1-8 || \
  sha256sum "$1" 2>/dev/null | cut -c1-8 || \
  echo "unversioned"
}

# ── --force: reset alle ontologie-graphs ────────────────────────────────────
if [ "$FORCE" = "true" ]; then
  echo "[fuseki-loader] --force: bestaande ontologie-graphs verwijderen..."

  GRAPHS_QUERY="SELECT ?g WHERE { GRAPH <${MODULES_GRAPH}> { ?m <urn:valor:graphUri> ?g } }"
  GRAPHS=$(curl -sf $AUTH \
    --data-urlencode "query=${GRAPHS_QUERY}" \
    "${FUSEKI_URL}/${DATASET}/query" \
    -H "Accept: application/sparql-results+json" | \
    grep -o '"value":"http[^"]*"' | sed 's/"value":"//;s/"//' || true)

  for g in $GRAPHS; do
    echo "[fuseki-loader]   Drop: ${g}"
    sparql_update "DROP SILENT GRAPH <${g}>"
  done

  sparql_update "DROP SILENT GRAPH <${MODULES_GRAPH}>"
  echo "[fuseki-loader] Reset compleet."
fi

# ── Ontologie ophalen ────────────────────────────────────────────────────────
echo "[fuseki-loader] VALOR-O ontologie ophalen van GitHub..."
TMPDIR=$(mktemp -d)
git clone --depth=1 "${ONTOLOGY_REPO}" "${TMPDIR}/ontology" > /dev/null 2>&1

# ── Per-module laden ─────────────────────────────────────────────────────────
echo "[fuseki-loader] Ontologie-modules verwerken..."
LOADED=0
SKIPPED=0

for f in "${TMPDIR}/ontology/"*.trig; do
  [ -f "$f" ] || continue

  FNAME=$(basename "$f")
  MODULE_NAME=$(basename "$f" .trig)
  MODULE_URI="urn:valor:module:${MODULE_NAME}"
  GRAPH_URI=$(extract_graph_uri "$f")
  VERSION=$(extract_version "$f")

  if [ -z "$VERSION" ]; then
    VERSION=$(file_fingerprint "$f")
  fi

  # Al geladen met deze versie?
  CHECK="ASK { GRAPH <${MODULES_GRAPH}> { <${MODULE_URI}> <urn:valor:version> \"${VERSION}\" } }"
  if [ "$(sparql_ask "${CHECK}")" = "true" ]; then
    echo "[fuseki-loader]   Overslaan: ${FNAME} (versie ${VERSION})"
    SKIPPED=$((SKIPPED + 1))
    continue
  fi

  # Bestaande versie ophalen (voor archivering)
  OLD_VERSION=$(sparql_select_value \
    "SELECT ?v WHERE { GRAPH <${MODULES_GRAPH}> { <${MODULE_URI}> <urn:valor:version> ?v } }")

  if [ -n "$OLD_VERSION" ] && [ -n "$GRAPH_URI" ]; then
    ARCHIVE_URI="${GRAPH_URI}/v${OLD_VERSION}"
    echo "[fuseki-loader]   Archiveren: ${FNAME} (v${OLD_VERSION} → ${ARCHIVE_URI})"
    sparql_update "COPY SILENT <${GRAPH_URI}> TO <${ARCHIVE_URI}>"
    sparql_update "CLEAR GRAPH <${GRAPH_URI}>"
  fi

  echo "[fuseki-loader]   Laden: ${FNAME} (versie ${VERSION})"
  curl -sf $AUTH \
    -X POST \
    -H "Content-Type: application/trig" \
    --data-binary "@${f}" \
    "${FUSEKI_URL}/${DATASET}/data" || echo "[fuseki-loader]   WAARSCHUWING: ${FNAME} mislukt"

  # Registry bijwerken (fallback graph URI als het bestand geen named graph declareert)
  REG_GRAPH_URI="${GRAPH_URI:-urn:valor:module-data:${MODULE_NAME}}"
  sparql_update "
    DELETE { GRAPH <${MODULES_GRAPH}> {
      <${MODULE_URI}> <urn:valor:version> ?v .
      <${MODULE_URI}> <urn:valor:graphUri> ?g .
    }}
    INSERT { GRAPH <${MODULES_GRAPH}> {
      <${MODULE_URI}> <urn:valor:version> \"${VERSION}\" .
      <${MODULE_URI}> <urn:valor:graphUri> <${REG_GRAPH_URI}> .
    }}
    WHERE { OPTIONAL { GRAPH <${MODULES_GRAPH}> {
      <${MODULE_URI}> <urn:valor:version> ?v .
      <${MODULE_URI}> <urn:valor:graphUri> ?g .
    }}}
  " || echo "[fuseki-loader]   WAARSCHUWING: registry-update mislukt voor ${FNAME}"

  LOADED=$((LOADED + 1))
done

rm -rf "${TMPDIR}"
echo "[fuseki-loader] Klaar: ${LOADED} module(s) geladen, ${SKIPPED} overgeslagen."
