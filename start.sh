#!/bin/bash

# set -e: interrompe l'esecuzione al primo comando fallito
# set -u: interrompe se ci sono variabili non inizializzate
set -euo pipefail

if [ -f .env ]; then source .env; fi

#docker compose up -d --build --remove-orphans
infisical run --env=prod --path="/" --recursive -- docker compose up -d --build --remove-orphans