from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.endpoints.rental_router import rental_router
from app.rabbitmq import connect_rabbitmq


@asynccontextmanager
async def lifespan(app: FastAPI):
    connection, channel, exchange, queue = await connect_rabbitmq()

    app.state.rabbitmq_exchange = exchange

    print("Сервис аренды подключён к RabbitMQ")

    try:
        yield
    finally:
        await connection.close()


app = FastAPI(
    title="Сервис аренды автомобиля",
    lifespan=lifespan,
)

app.include_router(
    rental_router,
    prefix="/api",
)