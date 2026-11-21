from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.clients.photo_store import get_photo_store
from app.endpoints.report_router import report_router
from app.settings import settings


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if settings.s3_create_bucket:
        get_photo_store().ensure_bucket()
    yield


app = FastAPI(title="Carsharing Vehicle Condition Reporting", lifespan=lifespan)
app.include_router(report_router, prefix="/api")
