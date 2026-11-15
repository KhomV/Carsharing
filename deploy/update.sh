#!/bin/sh
# Run only after the first successful publication of both public Docker Hub images.
set -eu
cd /home/khomch/carsharing
exec 9>.deploy.lock
flock -n 9 || exit 0
export RENTAL_IMAGE=khommv/carsharing-rental:latest
export PAYMENT_IMAGE=khommv/carsharing-payment:latest
docker compose --env-file .env.server -f compose.server.yaml pull rental_service payment_service
docker compose --env-file .env.server -f compose.server.yaml up -d --no-build --wait --wait-timeout 180
