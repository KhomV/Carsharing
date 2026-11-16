#!/bin/sh
# Pull published images for all application services; persistent data stays in volumes.
set -eu
cd /home/khomch/carsharing
exec 9>.deploy.lock
flock -n 9 || exit 0
export RENTAL_IMAGE=khommv/carsharing-rental:latest
export PAYMENT_IMAGE=khommv/carsharing-payment:latest
export BOOKING_IMAGE=khommv/carsharing-booking:latest
export TELEMETRY_IMAGE=khommv/carsharing-telemetry:latest
docker compose --env-file .env.server -f compose.server.yaml pull rental_service booking_service payment_service telemetry_service
docker compose --env-file .env.server -f compose.server.yaml up -d --no-build --wait --wait-timeout 180
