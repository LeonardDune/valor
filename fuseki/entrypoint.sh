#!/bin/sh
set -e

# In de gecombineerde container draait Fuseki lokaal
export FUSEKI_URL="${FUSEKI_URL:-http://localhost:3030}"

# Start Fuseki via de originele entrypoint in de achtergrond
/docker-entrypoint.sh &
FUSEKI_PID=$!

# Laad de VALOR-O ontologie (script wacht zelf op Fuseki health)
/load-ontology.sh

# Fuseki op de voorgrond houden
wait $FUSEKI_PID
