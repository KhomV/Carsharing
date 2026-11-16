import os

os.environ.setdefault("POSTGRES_URL", "postgresql+psycopg://test:test@127.0.0.1:1/booking_unit_test")
os.environ.setdefault("TELEMETRY_SERVICE_URL", "http://127.0.0.1:1")
