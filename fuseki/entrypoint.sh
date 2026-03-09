#!/bin/sh
set -e

# Start Fuseki via de originele entrypoint in de achtergrond
/docker-entrypoint.sh &
FUSEKI_PID=$!

# Laad de VALOR-O ontologie (script wacht zelf op Fuseki health)
/load-ontology.sh

# Fuseki op de voorgrond houden
wait $FUSEKI_PID
