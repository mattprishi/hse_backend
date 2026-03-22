import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from workers.moderation_worker import process_kafka_message_with_retries
from config import WORKER_MAX_RETRIES


@pytest.mark.asyncio
async def test_process_kafka_message_with_retries_succeeds_after_one_failure():
    msg = MagicMock()
    msg.value = json.dumps({"item_id": 42}).encode()
    consumer = AsyncMock()
    model = object()

    with patch(
        "workers.moderation_worker.process_message",
        new_callable=AsyncMock,
    ) as pm:
        pm.side_effect = [RuntimeError("temporary"), None]
        with patch("workers.moderation_worker.asyncio.sleep", new_callable=AsyncMock):
            await process_kafka_message_with_retries(msg, model, consumer)

    assert pm.call_count == 2
    consumer.commit.assert_called_once()


@pytest.mark.asyncio
async def test_process_kafka_message_with_retries_exhausted():
    msg = MagicMock()
    msg.value = json.dumps({"item_id": 1}).encode()
    consumer = AsyncMock()
    model = object()

    with patch(
        "workers.moderation_worker.process_message",
        new_callable=AsyncMock,
    ) as pm:
        pm.side_effect = RuntimeError("always")
        with patch("workers.moderation_worker.asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(RuntimeError, match="always"):
                await process_kafka_message_with_retries(msg, model, consumer)

    assert pm.call_count == WORKER_MAX_RETRIES + 1
    consumer.commit.assert_not_called()
