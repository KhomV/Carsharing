import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session


@pytest.fixture
def db():
    url = os.environ["POSTGRES_URL"]
    if os.getenv("ALLOW_TEST_DATABASE") != "1" or not make_url(url).database.endswith("_test"):
        pytest.fail("Use only an explicitly enabled isolated *_test database")
    engine = create_engine(url)
    with engine.connect() as connection:
        transaction = connection.begin()
        with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
            try:
                yield session
            finally:
                session.close()
                transaction.rollback()
    engine.dispose()
