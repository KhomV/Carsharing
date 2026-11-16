from fastapi import FastAPI

from app.endpoints.telemetry_router import telemetry_router


app = FastAPI(
    title="Сервис телеметрии",
)

app.include_router(
    telemetry_router,
    prefix="/api",
)
