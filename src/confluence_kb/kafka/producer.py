import json
import logging
from typing import Any, Callable, Dict, Optional

from confluent_kafka import Producer

from confluence_kb.config import config

logger = logging.getLogger(__name__)


class KafkaProducer:
    def __init__(self, bootstrap_servers: Optional[str] = None):
        if bootstrap_servers is None:
            bootstrap_servers = config.kafka.bootstrap_servers

        if isinstance(bootstrap_servers, list):
            bootstrap_servers = ",".join(bootstrap_servers) 
            
        self.producer = Producer({"bootstrap.servers": bootstrap_servers})
        logger.info(f"Initialized Kafka producer with bootstrap servers: {bootstrap_servers}")

    def delivery_report(self, err, msg):
        if err is not None:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}]")

    def send(
        self, 
        topic: str, 
        value: Dict[str, Any], 
        key: Optional[str] = None, 
        callback: Optional[Callable] = None
    ):
        if key is None and "id" in value:
            key = value["id"]
            
        if callback is None:
            callback = self.delivery_report
            
        try:
            self.producer.produce(
                topic,
                key=str(key).encode("utf-8") if key else None,
                value=json.dumps(value).encode("utf-8"),
                callback=callback,
            )
            self.producer.poll(0)  
            
        except Exception as e:
            logger.error(f"Failed to send message to Kafka: {e}")
            raise

    def send_raw_data(self, data: Dict[str, Any], key: Optional[str] = None):
        self.send(config.kafka.raw_topic, data, key)

    def send_processed_text(self, data: Dict[str, Any], key: Optional[str] = None):
        self.send(config.kafka.processed_topic, data, key)

    def send_text_chunks(self, data: Dict[str, Any], key: Optional[str] = None):
        self.send(config.kafka.chunks_topic, data, key)

    def send_embeddings(self, data: Dict[str, Any], key: Optional[str] = None):
        self.send(config.kafka.embeddings_topic, data, key)

    def send_version_metadata(self, data: Dict[str, Any], key: Optional[str] = None):
        self.send(config.kafka.version_topic, data, key)

    def flush(self, timeout: Optional[float] = None):
        self.producer.flush(timeout)
        
    def close(self):
        self.flush()
        # The producer will be garbage collected
        logger.info("Closed Kafka producer")


_producer = None


def get_producer() -> KafkaProducer:
    global _producer
    if _producer is None:
        _producer = KafkaProducer()
    return _producer