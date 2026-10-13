"""
Unified Event Broker.
Supports RabbitMQ AMQP messaging (via pika) with instant graceful fallback
to high-throughput internal asyncio priority queue for zero-config local execution.
"""
import asyncio
import json
import logging
from typing import Callable, Dict, Any, List, Optional
import pika
from app.models.schemas import DisruptionWebhookPayload

logger = logging.getLogger("EventBroker")


class EventBroker:
    def __init__(self, rabbitmq_host: str = "localhost", rabbitmq_port: int = 5672):
        self.rabbitmq_host = rabbitmq_host
        self.rabbitmq_port = rabbitmq_port
        self.is_rabbitmq_connected = False
        self.pika_connection = None
        self.pika_channel = None
        self.async_queue: asyncio.Queue = asyncio.Queue()
        self.subscribers: List[Callable[[Dict[str, Any]], Any]] = []

    def connect(self):
        """Attempts RabbitMQ connection, falling back gracefully to local async queue."""
        import os
        if os.environ.get("VERCEL") or os.environ.get("SKIP_RABBITMQ", "").lower() in ("true", "1"):
            self.is_rabbitmq_connected = False
            logger.info("Running on high-performance native AsyncIO Event Queue (Serverless mode).")
            return

        try:
            parameters = pika.ConnectionParameters(
                host=self.rabbitmq_host,
                port=self.rabbitmq_port,
                connection_attempts=1,
                retry_delay=1,
                socket_timeout=2,
            )
            self.pika_connection = pika.BlockingConnection(parameters)
            self.pika_channel = self.pika_connection.channel()
            self.pika_channel.queue_declare(queue="flight_disruptions", durable=True)
            self.is_rabbitmq_connected = True
            logger.info(f"Connected to RabbitMQ broker at {self.rabbitmq_host}:{self.rabbitmq_port}")
        except Exception as e:
            self.is_rabbitmq_connected = False
            logger.info(f"RabbitMQ server offline ({e}). Running on high-performance native AsyncIO Event Queue.")

    def subscribe(self, callback: Callable[[Dict[str, Any]], Any]):
        """Subscribes an asynchronous consumer function to the event stream."""
        self.subscribers.append(callback)

    async def publish_disruption(self, payload: DisruptionWebhookPayload):
        """Publishes disruption event to RabbitMQ (if connected) and local async pipeline."""
        event_data = payload.model_dump(mode="json")
        
        # Publish to RabbitMQ if active
        if self.is_rabbitmq_connected and self.pika_channel:
            try:
                self.pika_channel.basic_publish(
                    exchange="",
                    routing_key="flight_disruptions",
                    body=json.dumps(event_data),
                    properties=pika.BasicProperties(delivery_mode=2),
                )
            except Exception as ex:
                logger.warning(f"RabbitMQ publish failed: {ex}. Utilizing internal queue.")

        # Always enqueue into async pipeline for local workers
        await self.async_queue.put(event_data)

    async def start_consumer_loop(self):
        """Consumes events from the internal queue and invokes all registered worker callbacks."""
        while True:
            try:
                event_data = await self.async_queue.get()
                for sub in self.subscribers:
                    try:
                        res = sub(event_data)
                        if asyncio.iscoroutine(res):
                            await res
                    except Exception as err:
                        logger.error(f"Error in subscriber callback: {err}")
                self.async_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Consumer error: {e}")
                await asyncio.sleep(0.1)


# Singleton broker
event_broker = EventBroker()
