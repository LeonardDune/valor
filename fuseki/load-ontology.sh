#!/bin/sh
set -e

FUSEKI_URL="${FUSEKI_URL:-http://fuseki:3030}"
FUSEKI_ADMIN_PASSWORD="${FUSEKI_ADMIN_PASSWORD:-admin}"
DATASET="${DATASET:-valor}"
ONTOLOGY_REPO="${ONTOLOGY_REPO:-https://github.com/LeonardDune/valor-ontology.git}"
SENTINEL_GRAPH="urn:valor:ontology-loaded"
AUTH="-u admin:${FUSEKI_ADMIN_PASSWORD}"

echo "[fuseki-loader] Benodigde tools installeren..."
if command -v apk > /dev/null 2>&1; then
  apk add --no-cache curl git > /dev/null 2>&1
elif command -v apt-get > /dev/null 2>&1; then
  apt-get update -qq && apt-get install -y --no-install-recommends curl git > /dev/null 2>&1
fi

echo "[fuseki-loader] Wachten op Fuseki..."
until curl -sf -u "admin:${FUSEKI_ADMIN_PASSWORD}" "${FUSEKI_URL}/\$/ping" > /dev/null; do
  sleep 2
done
echo "[fuseki-loader] Fuseki is bereikbaar."

# Controleer of ontologie al geladen is (sentinel graph)
QUERY="ASK { GRAPH <${SENTINEL_GRAPH}> { ?s ?p ?o } }"
RESULT=$(curl -sf $AUTH \
  --data-urlencode "query=${QUERY}" \
  "${FUSEKI_URL}/${DATASET}/query" \
  -H "Accept: application/sparql-results+json" | \
  grep -o '"boolean"[[:space:]]*:[[:space:]]*[a-z]*' | grep -o '[a-z]*$' || echo "false")

if [ "$RESULT" = "true" ]; then
  echo "[fuseki-loader] VALOR-O ontologie al geladen, overslaan."
  exit 0
fi

echo "[fuseki-loader] VALOR-O ontologie ophalen van GitHub..."
TMPDIR=$(mktemp -d)
git clone --depth=1 "${ONTOLOGY_REPO}" "${TMPDIR}/ontology"

echo "[fuseki-loader] TriG-modules laden in dataset '${DATASET}'..."
for f in "${TMPDIR}/ontology/"*.trig; do
  FNAME=$(basename "$f")
  echo "[fuseki-loader]   Laden: ${FNAME}"
  curl -sf $AUTH -X POST \
    -H "Content-Type: application/trig" \
    --data-binary "@${f}" \
    "${FUSEKI_URL}/${DATASET}/data" || echo "[fuseki-loader]   WAARSCHUWING: ${FNAME} mislukt"
done

# Sentinel graph aanmaken zodat volgende run overgeslagen wordt
curl -sf $AUTH -X PUT \
  -H "Content-Type: text/turtle" \
  --data-binary "<${SENTINEL_GRAPH}> a <urn:valor:Sentinel> ." \
  "${FUSEKI_URL}/${DATASET}/data?graph=${SENTINEL_GRAPH}"

rm -rf "${TMPDIR}"
echo "[fuseki-loader] VALOR-O ontologie-modules succesvol geladen."
