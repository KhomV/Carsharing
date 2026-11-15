from aio_pika import ExchangeType, connect_robust

from app.settings import settings
from uuid import uuid4

from aio_pika import DeliveryMode, Message
from aio_pika.abc import AbstractExchange

from app.models.rental import Rental


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

async def publish_rental_finished(
    exchange: AbstractExchange,
    rental: Rental,
):
    event = {
        "event_id": str(uuid4()),
        "rental_id": str(rental.id),
        "user_id": str(rental.user_id),
        "amount": rental.total_amount,
        "finished_at": rental.finished_at.isoformat(),
    }

    import json

    message = Message(
        body=json.dumps(event).encode("utf-8"),
        content_type="application/json",
        delivery_mode=DeliveryMode.PERSISTENT,
    )

    await exchange.publish(
        message,
        routing_key=ROUTING_KEY,
        mandatory=True,
        timeout=10,
    )