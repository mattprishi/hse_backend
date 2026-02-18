import asyncio
import json
import logging
from datetime import datetime
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from config import KAFKA_BOOTSTRAP_SERVERS, DATABASE_URL
from clients.postgres import init_db_pool, get_pg_connection
from repositories.ads import AdRepository
from repositories.moderation_results import ModerationResultRepository
from clients.kafka import TOPIC_MODERATION, TOPIC_DLQ
import sys
import os

# sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'hw2'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'hw2'))
from model import load_or_train_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY = 2


async def predict_ml(ad_data: dict, model):
    import numpy as np
    features = np.array([[
        1.0 if ad_data.get('is_verified_seller') else 0.0,
        ad_data['images_qty'] / 10.0,
        len(ad_data['description']) / 1000.0,
        ad_data['category'] / 100.0,
    ]])
    prediction = int(model.predict(features)[0])
    probability = float(model.predict_proba(features)[0][1])
    return {"is_violation": bool(prediction), "probability": probability}


async def process_message(msg_value: bytes, model):
    data = json.loads(msg_value.decode())
    item_id = data.get("item_id")

    if not item_id:
        raise ValueError("No item_id in message")

    ad_repo = AdRepository()
    moderation_repo = ModerationResultRepository()

    # Создаём запись если её нет
    existing_task = await moderation_repo.get_by_id(item_id)
    if not existing_task:
        await moderation_repo.create(item_id)

    ad_data = await ad_repo.get_with_user(item_id)
    if not ad_data:
        raise ValueError(f"Advertisement {item_id} not found")

    prediction = await predict_ml(ad_data, model)

    await moderation_repo.update_result(
        item_id,
        "completed",
        is_violation=prediction["is_violation"],
        probability=prediction["probability"]
    )

    logger.info(f"Successfully processed item_id={item_id}, result={prediction}")


async def send_to_dlq(producer: AIOKafkaProducer, original_msg: bytes, error: str, retry_count: int):
    dlq_message = {
        "original_message": json.loads(original_msg.decode()),
        "error": str(error),
        "timestamp": datetime.utcnow().isoformat(),
        "retry_count": retry_count
    }
    await producer.send_and_wait(TOPIC_DLQ, json.dumps(dlq_message).encode("utf-8"))
    logger.error(f"Sent message to DLQ: {error}")


async def update_db_status_failed(item_id: int, error_msg: str):
    moderation_repo = ModerationResultRepository()
    await moderation_repo.update_result(item_id, "failed", error_message=str(error_msg))


async def consume():
    await init_db_pool()

    model = load_or_train_model("model.pkl")

    consumer = AIOKafkaConsumer(
        TOPIC_MODERATION,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id="moderation_worker_group",
        auto_offset_reset='earliest',
        enable_auto_commit=False
    )

    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)

    await consumer.start()
    await producer.start()

    logger.info("Worker started. Waiting for messages...")

    try:
        async for msg in consumer:
            logger.info(f"Received message: {msg.value}")
            item_id = None

            try:
                payload = json.loads(msg.value)
                item_id = payload.get("item_id")
            except:
                pass

            try:
                for attempt in range(1, MAX_RETRIES + 2):
                    try:
                        await process_message(msg.value, model)
                        await consumer.commit()
                        break
                    except Exception as e:
                        if attempt <= MAX_RETRIES:
                            logger.warning(
                                f"Attempt {attempt}/{MAX_RETRIES} failed for item_id={item_id}: {e}. "
                                f"Retrying in {RETRY_DELAY}s..."
                            )
                            await asyncio.sleep(RETRY_DELAY)
                        else:
                            raise e

            except Exception as e:
                logger.error(f"Fatal error processing message: {e}")
                await send_to_dlq(producer, msg.value, str(e), MAX_RETRIES)
                if item_id:
                    await update_db_status_failed(item_id, str(e))
                await consumer.commit()

    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(consume())
