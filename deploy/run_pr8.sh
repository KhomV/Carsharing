#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p test-results
trap 'docker compose -f compose.tests.yaml down -v > test-results/cleanup.log 2>&1' EXIT
docker compose -f compose.tests.yaml build > test-results/build.log 2>&1
docker compose -f compose.tests.yaml run --rm --no-deps rental_tests python -m pytest tests/unit -v > test-results/unit-rental.log 2>&1
docker compose -f compose.tests.yaml run --rm --no-deps booking_tests python -m pytest tests/unit -v > test-results/unit-booking.log 2>&1
docker compose -f compose.tests.yaml run --rm --no-deps payment_tests python -m pytest tests/unit -v > test-results/unit-payment.log 2>&1
docker compose -f compose.tests.yaml run --rm --no-deps telemetry_tests python -m pytest tests/unit -v > test-results/unit-telemetry.log 2>&1
docker compose -f compose.tests.yaml run --rm --no-deps auth_tests python -m pytest tests/unit -v > test-results/unit-auth.log 2>&1
docker compose -f compose.tests.yaml up -d --wait rental_test_db booking_test_db payment_test_db telemetry_test_db auth_test_db > test-results/databases.log 2>&1
docker compose -f compose.tests.yaml run --rm --no-deps rental_tests sh -c 'python -m alembic upgrade head && python -m pytest tests/integration -v' > test-results/integration-rental.log 2>&1
docker compose -f compose.tests.yaml run --rm --no-deps booking_tests sh -c 'python -m alembic upgrade head && python -m pytest tests/integration -v' > test-results/integration-booking.log 2>&1
docker compose -f compose.tests.yaml run --rm --no-deps payment_tests sh -c 'python -m alembic upgrade head && python -m pytest tests/integration -v' > test-results/integration-payment.log 2>&1
docker compose -f compose.tests.yaml run --rm --no-deps telemetry_tests sh -c 'python -m alembic upgrade head && python -m pytest tests/integration -v' > test-results/integration-telemetry.log 2>&1
docker compose -f compose.tests.yaml run --rm --no-deps auth_tests sh -c 'python -m alembic upgrade head && python -m pytest tests/integration -v' > test-results/integration-auth.log 2>&1
tail -n 2 test-results/unit-rental.log test-results/unit-booking.log test-results/unit-payment.log test-results/unit-telemetry.log test-results/unit-auth.log test-results/integration-rental.log test-results/integration-booking.log test-results/integration-payment.log test-results/integration-telemetry.log test-results/integration-auth.log
