import asyncio
import json
import logging
import os
from typing import Any

import aiohttp
import nats

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("todo-broadcaster")

NATS_URL = os.getenv("NATS_URL", "nats://my-nats-headless.nats.svc.cluster.local:4222")
TODO_EVENT_SUBJECT = os.getenv("TODO_EVENT_SUBJECT", "todo.events")
TODO_EVENT_QUEUE = os.getenv("TODO_EVENT_QUEUE", "todo-broadcaster")
WEBHOOK_URL = os.getenv("BROADCAST_WEBHOOK_URL", "https://hooks.slack.com/services/REPLACE/ME/EXAMPLE")
BROADCAST_MODE = os.getenv("BROADCAST_MODE", "slack")


async def send_to_webhook(message: dict[str, Any]) -> None:
    todo = message.get("todo", {})
    event = message.get("event", "todo.updated")
    summary = todo.get("text", "unknown todo")
    action = event.replace("todo.", "")

    async with aiohttp.ClientSession() as session:
        message = f"Todo {action}: {summary}"
        payload = {"text": f"* {message} *"} if BROADCAST_MODE != "generic" else {
            "user": "bot",
            "message": message,
        }
        async with session.post(WEBHOOK_URL, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
            response.raise_for_status()
            logger.info("Forwarded todo event to webhook (status=%s)", response.status)


async def process_message(message: dict[str, Any]) -> None:
    if BROADCAST_MODE == "log":
        logger.info("Staging broadcast event: %s", json.dumps(message, sort_keys=True))
        return

    await send_to_webhook(message)


async def run() -> None:
    nc = await nats.connect(NATS_URL)
    logger.info("Connected to NATS at %s", NATS_URL)

    async def handler(msg):
        raw = msg.data.decode("utf-8")
        logger.info("Received message on %s: %s", msg.subject, raw)
        try:
            payload = json.loads(raw)
            await process_message(payload)
        except Exception as exc:
            logger.warning("Failed processing NATS event: %s", exc)

    await nc.subscribe(TODO_EVENT_SUBJECT, queue=TODO_EVENT_QUEUE, cb=handler)
    await nc.flush()
    logger.info("Listening for events on subject '%s' in queue '%s'", TODO_EVENT_SUBJECT, TODO_EVENT_QUEUE)
    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(run())
