import os

os.environ.setdefault("POSTGRES_URL", "postgresql+psycopg://test:test@127.0.0.1:1/payment_unit_test")
os.environ.setdefault("AMQP_URL", "amqp://test:test@127.0.0.1:1/")
