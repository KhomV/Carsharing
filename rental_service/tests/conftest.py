import os

# Unit tests can import application classes without a real DB or broker.
# Port 1 is intentionally unusable: any accidental connection fails.
os.environ.setdefault("POSTGRES_URL", "postgresql+psycopg://test:test@127.0.0.1:1/rental_unit_test")
os.environ.setdefault("AMQP_URL", "amqp://test:test@127.0.0.1:1/")
