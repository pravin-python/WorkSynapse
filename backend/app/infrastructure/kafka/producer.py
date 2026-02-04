"""
Kafka Service - Event Streaming for Chat, Agents, and Logs
"""
from typing import Optional, Callable, Any
import json
import asyncio
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from app.core.config import settings
from app.core.logging import logger

class KafkaService:
    """Kafka producer/consumer wrapper."""
    
    def __init__(self):
        self.producer: Optional[AIOKafkaProducer] = None
        self.consumers: dict = {}
    
    async def start_producer(self):
        """Initialize Kafka producer."""
        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        await self.producer.start()
        logger.info("Kafka producer started")
    
    async def stop_producer(self):
        """Stop Kafka producer."""
        if self.producer:
            await self.producer.stop()
    
    async def send_event(self, topic: str, event: dict, key: Optional[str] = None):
        """Send event to Kafka topic."""
        if self.producer:
            key_bytes = key.encode('utf-8') if key else None
            await self.producer.send_and_wait(topic, event, key=key_bytes)
    
    async def start_consumer(
        self,
        topic: str,
        group_id: str,
        handler: Callable[[dict], Any]
    ):
        """Start a Kafka consumer for a topic."""
        consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id=group_id,
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        await consumer.start()
        self.consumers[topic] = consumer
        
        # Start consuming in background
        asyncio.create_task(self._consume(topic, handler))
        logger.info(f"Kafka consumer started for topic: {topic}")
    
    async def _consume(self, topic: str, handler: Callable):
        """Internal consume loop."""
        consumer = self.consumers.get(topic)
        if not consumer:
            return
        try:
            async for msg in consumer:
                try:
                    await handler(msg.value)
                except Exception as e:
                    logger.error(f"Error processing Kafka message: {e}")
        finally:
            await consumer.stop()
    
    async def stop_all_consumers(self):
        """Stop all consumers."""
        for consumer in self.consumers.values():
            await consumer.stop()
        self.consumers.clear()

# Topics
class KafkaTopics:
    CHAT_MESSAGES = "worksynapse.chat.messages"
    AGENT_TASKS = "worksynapse.agent.tasks"
    SYSTEM_LOGS = "worksynapse.system.logs"
    USER_ACTIVITY = "worksynapse.user.activity"
    NOTIFICATIONS = "worksynapse.notifications"

# Singleton
kafka_service = KafkaService()

# Event Publishers
async def publish_chat_message(channel_id: str, user_id: str, message: str):
    """Publish chat message to Kafka."""
    await kafka_service.send_event(
        KafkaTopics.CHAT_MESSAGES,
        {
            "channel_id": channel_id,
            "user_id": user_id,
            "message": message,
            "type": "message"
        },
        key=channel_id
    )

async def publish_agent_task(agent_type: str, task_data: dict):
    """Publish agent task to Kafka."""
    await kafka_service.send_event(
        KafkaTopics.AGENT_TASKS,
        {
            "agent_type": agent_type,
            "task": task_data
        }
    )

async def publish_system_log(level: str, message: str, metadata: dict = None):
    """Publish system log to Kafka."""
    await kafka_service.send_event(
        KafkaTopics.SYSTEM_LOGS,
        {
            "level": level,
            "message": message,
            "metadata": metadata or {}
        }
    )
