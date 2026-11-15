from aio_pika import ExchangeType, connect_robust

from app.settings import settings
import asyncio
import logging

from aio_pika import IncomingMessage
from pydantic import ValidationError

from app.database import SessionLocal
from app.models.rental_event import RentalFinishedEvent
from app.services.invoice_service import InvoiceService

logger = logging.getLogger(__name__)


EXCHANGE_NAME = "ikbo-66_khomchenko_events"
QUEUE_NAME = "ikbo-66_khomchenko_payment"
ROUTING_KEY = "rental.finished"


async def connect_rabbitmq():
    connection = await connect_robust(
        settings.amqp_url,
        timeout=10,
    )

    try:
        channel = await connection.channel(
            publisher_confirms=True,
        )

        exchange = await channel.declare_exchange(
            EXCHANGE_NAME,
            ExchangeType.DIRECT,
            durable=True,
        )

        queue = await channel.declare_queue(
            QUEUE_NAME,
            durable=True,
        )

        await queue.bind(
            exchange,
            routing_key=ROUTING_KEY,
        )

        return connection, channel, exchange, queue

    except Exception:
        await connection.close()
        raise

def create_invoice_from_event(event: RentalFinishedEvent):
    with SessionLocal() as db:
        service = InvoiceService(db=db)

        return service.create_invoice(
            rental_id=event.rental_id,
            user_id=event.user_id,
            amount=event.amount,
        )


async def process_rental_finished(message: IncomingMessage):
    try:
        event = RentalFinishedEvent.model_validate_json(
            message.body
        )

        invoice = await asyncio.to_thread(
            create_invoice_from_event,
            event,
        )

    except (ValidationError, ValueError):
        logger.exception(
            "Некорректное событие или конфликт данных счёта"
        )

        await message.reject(requeue=False)
        return

    except Exception:
        logger.exception(
            "Ошибка обработки события. Сообщение будет возвращено"
        )

        await asyncio.sleep(2)
        await message.nack(requeue=True)
        return

    await message.ack()

    print(
        f"Счёт {invoice.id} для аренды "
        f"{invoice.rental_id} обработан",
        flush=True,
    )