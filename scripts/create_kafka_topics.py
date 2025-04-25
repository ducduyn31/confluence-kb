#!/usr/bin/env python3
import logging
import sys
from pathlib import Path

from confluent_kafka.admin import AdminClient, NewTopic
from rich.console import Console
from rich.logging import RichHandler

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from confluence_kb.config import config

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger("create-kafka-topics")

console = Console()


def create_topics():
    try:
        admin_client = AdminClient({"bootstrap.servers": config.kafka.bootstrap_servers})

        topics = [
            NewTopic(
                config.kafka.raw_topic,
                num_partitions=3,
                replication_factor=1,
                config={"retention.ms": 604800000},  # 7 days
            ),
            NewTopic(
                config.kafka.processed_topic,
                num_partitions=3,
                replication_factor=1,
                config={"retention.ms": 604800000},  # 7 days
            ),
            NewTopic(
                config.kafka.chunks_topic,
                num_partitions=3,
                replication_factor=1,
                config={"retention.ms": 604800000},  # 7 days
            ),
            NewTopic(
                config.kafka.embeddings_topic,
                num_partitions=3,
                replication_factor=1,
                config={"retention.ms": 604800000},  # 7 days
            ),
            NewTopic(
                config.kafka.version_topic,
                num_partitions=3,
                replication_factor=1,
                config={"retention.ms": 604800000},  # 7 days
            ),
        ]

        console.print("[bold blue]Creating Kafka topics...[/]")
        futures = admin_client.create_topics(topics)

        for topic, future in futures.items():
            try:
                future.result() 
                console.print(f"[green]Topic {topic} created successfully![/]")
            except Exception as e:
                if "already exists" in str(e):
                    console.print(f"[yellow]Topic {topic} already exists.[/]")
                else:
                    console.print(f"[bold red]Failed to create topic {topic}: {str(e)}[/]")

    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    console.print("[bold]Creating Kafka topics...[/]")
    create_topics()
    console.print("[bold green]Kafka topics created successfully![/]")