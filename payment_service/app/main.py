from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.endpoints.invoice_router import invoice_router
from app.rabbitmq import (
    connect_rabbitmq,
    process_rental_finished,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    connection, channel, exchange, queue = await connect_rabbitmq()

    try:
        await channel.set_qos(prefetch_count=1)

        consumer_tag = await queue.consume(
            process_rental_finished
        )

        print("Сервис оплаты ожидает завершённые аренды")

        try:
            yield
        finally:
            await queue.cancel(consumer_tag)

    finally:
        await connection.close()


app = FastAPI(
    title="Сервис оплаты",
    lifespan=lifespan,
)

app.include_router(
    invoice_router,
    prefix="/api",
)