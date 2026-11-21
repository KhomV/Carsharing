import os


os.environ.setdefault("POSTGRES_URL", "postgresql+psycopg://test:test@127.0.0.1:1/license_unit_test")
os.environ.setdefault("LICENSE_STATUS_KEY", "test-license-status-key")
