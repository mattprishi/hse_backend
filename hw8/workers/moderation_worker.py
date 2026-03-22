from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from time import perf_counter
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import sentry_sdk
from config import (
    KAFKA_BOOTSTRAP_SERVERS,
    MODEL_PATH,
    WORKER_MAX_RETRIES,
    WORKER_RETRY_BASE_DELAY_SEC,
)
from clients.postgres import init_db_pool
from repositories.ads import AdRepository
from repositories.moderation_results import ModerationResultRepository
from clients.kafka import TOPIC_MODERATION, TOPIC_DLQ
from metrics import PREDICTION_DURATION, observe_prediction_metrics
from ml.model import load_model
from workers.retry_utils import exponential_backoff_seconds
from logging_config import setup_app_logging

setup_app_logging()
logger = logging.getLogger(__name__)


async def predict_ml(ad_data: dict, model):
    import numpy as np
    features = np.array([[
        1.0 if ad_data.get('is_verified_seller') else 0.0,
        ad_data['images_qty'] / 10.0,
        len(ad_data['description']) / 1000.0,
        ad_data['category'] / 100.0,
    ]])
    started_at = perf_counter()
    prediction = int(model.predict(features)[0])
    probability = float(model.predict_proba(features)[0][1])
    PREDICTION_DURATION.observe(perf_counter() - started_at)
    is_violation = bool(prediction)
    observe_prediction_metrics(is_violation, probability)
    return {"is_violation": is_violation, "probability": probability}


async def process_message(msg_value: bytes, model):
    data = json.loads(msg_value.decode())
    item_id = data.get("item_id")

    if not item_id:
        raise ValueError("No item_id in message")

    ad_repo = AdRepository()
    moderation_repo = ModerationResultRepository()

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


def _parse_item_id_from_message(msg_value: bytes | None) -> int | None:
    if msg_value is None:
        return None
    try:
        payload = json.loads(msg_value.decode())
        item_id = payload.get("item_id")
        return int(item_id) if item_id is not None else None
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError, TypeError):
        return None


async def process_kafka_message_with_retries(
    msg,
    model,
    consumer: AIOKafkaConsumer,
) -> None:
    """Обрабатывает одно сообщение с retry; при успехе делает commit."""
    item_id = _parse_item_id_from_message(msg.value)
    for attempt in range(WORKER_MAX_RETRIES + 1):
        try:
            await process_message(msg.value, model)
            await consumer.commit()
            return
        except Exception as e:
            if attempt < WORKER_MAX_RETRIES:
                delay = exponential_backoff_seconds(
                    WORKER_RETRY_BASE_DELAY_SEC,
                    attempt,
                )
                logger.warning(
                    "Attempt %s/%s failed for item_id=%s: %s. Retrying in %.2fs...",
                    attempt + 1,
                    WORKER_MAX_RETRIES + 1,
                    item_id,
                    e,
                    delay,
                )
                await asyncio.sleep(delay)
            else:
                raise


async def consume():
    await init_db_pool()

    try:
        model = load_model(MODEL_PATH)
    except FileNotFoundError:
        logger.error(
            "Model file not found: %s. Run: python train_model.py",
            MODEL_PATH,
        )
        raise

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
            item_id = _parse_item_id_from_message(msg.value)

            try:
                await process_kafka_message_with_retries(msg, model, consumer)
            except Exception as e:
                logger.error(f"Fatal error processing message: {e}")
                sentry_sdk.capture_exception(e)
                await send_to_dlq(producer, msg.value, str(e), WORKER_MAX_RETRIES)
                if item_id:
                    await update_db_status_failed(item_id, str(e))
                await consumer.commit()

    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(consume())
