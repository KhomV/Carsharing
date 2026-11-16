from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.settings import settings


engine = create_engine(
    settings.postgres_url,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine)


def get_db():
    with SessionLocal() as session:
        yield session
