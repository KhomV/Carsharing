from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from pymongo.errors import ConnectionFailure, ExecutionTimeout

from app.database import connect_mongo, prepare_tickets
from app.endpoints.ticket_router import ticket_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = connect_mongo()
    try:
        app.state.tickets = await run_in_threadpool(prepare_tickets, client)
        yield
    finally:
        client.close()


app = FastAPI(title="Carsharing Service Support", lifespan=lifespan)
app.include_router(ticket_router, prefix="/api")


@app.exception_handler(ConnectionFailure)
@app.exception_handler(ExecutionTimeout)
async def database_unavailable(_request: Request, _error: Exception) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": "Support database unavailable"})
