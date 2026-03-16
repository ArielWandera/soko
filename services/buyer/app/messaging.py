import aio_pika
import json
import logging
from app.config import settings

logger = logging.getLogger(__name__)


async def publish_event(event_type: str, data: dict):
    """
    Publishes buyer events to RabbitMQ.
    event_type examples: "order.placed", "transaction.completed"
    """
    try:
        connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        async with connection:
            channel = await connection.channel()
            await channel.declare_queue(event_type, durable=True)
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps({"event": event_type, "data": data}).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                ),
                routing_key=event_type,
            )
            logger.info(f"Published event: {event_type}")
    except Exception as e:
        logger.error(f"Failed to publish event {event_type}: {e}")
