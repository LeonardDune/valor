#!/bin/sh
set -e

# Altijd localhost gebruiken — externe FUSEKI_URL (voor de backend) mag dit niet overschrijven
export FUSEKI_URL="http://localhost:3030"

# Start Fuseki via de originele entrypoint in de achtergrond
/docker-entrypoint.sh &
FUSEKI_PID=$!

# Laad de VALOR-O ontologie (script wacht zelf op Fuseki health)
/load-ontology.sh

# Fuseki op de voorgrond houden
wait $FUSEKI_PID
