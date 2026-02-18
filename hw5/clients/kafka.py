import json
import logging
from datetime import datetime
from aiokafka import AIOKafkaProducer
from contextlib import asynccontextmanager
from config import KAFKA_BOOTSTRAP_SERVERS

logger = logging.getLogger(__name__)

TOPIC_MODERATION = "moderation"
TOPIC_DLQ = "moderation_dlq"


class KafkaClient:
    def __init__(self):
        self.producer: AIOKafkaProducer | None = None

    async def start(self):
        self.producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
        await self.producer.start()
        logger.info("Kafka producer started")

    async def stop(self):
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka producer stopped")

    async def send_moderation_request(self, item_id: int):
        message = {
            "item_id": item_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        value_json = json.dumps(message).encode('utf-8')
        try:
            await self.producer.send_and_wait(TOPIC_MODERATION, value_json)
            logger.info(f"Sent moderation request for item_id={item_id}")
        except Exception as e:
            logger.error(f"Failed to send Kafka message: {e}")
            raise

    async def send_to_dlq(self, original_message: dict, error: str, retry_count: int = 0):
        dlq_message = {
            "original_message": original_message,
            "error": error,
            "timestamp": datetime.utcnow().isoformat(),
            "retry_count": retry_count
        }
        value_json = json.dumps(dlq_message).encode('utf-8')
        try:
            await self.producer.send_and_wait(TOPIC_DLQ, value_json)
            logger.error(f"Sent message to DLQ: {error}")
        except Exception as e:
            logger.error(f"Failed to send to DLQ: {e}")
            raise


kafka_client = KafkaClient()


@asynccontextmanager
async def lifespan_kafka(app):
    await kafka_client.start()
    yield
    await kafka_client.stop()
