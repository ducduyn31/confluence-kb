from pathlib import Path
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).parent.parent.parent


class ConfluenceConfig(BaseSettings):
    url: str = Field(..., description="Confluence Cloud URL")
    username: str = Field(..., description="Confluence username or email")
    api_token: str = Field(..., description="Confluence API token")
    verify_ssl: bool = Field(True, description="Verify SSL certificates")

    model_config = SettingsConfigDict(env_prefix="CONFLUENCE_")


class KafkaConfig(BaseSettings):
    bootstrap_servers: List[str] = Field("localhost:9092", description="Kafka bootstrap servers")
    raw_topic: str = Field("raw-confluence-data", description="Raw data topic")
    processed_topic: str = Field("processed-text", description="Processed text topic")
    chunks_topic: str = Field("text-chunks", description="Text chunks topic")
    embeddings_topic: str = Field("embeddings", description="Embeddings topic")
    version_topic: str = Field("version-metadata", description="Version metadata topic")

    model_config = SettingsConfigDict(env_prefix="KAFKA_")


class FlinkConfig(BaseSettings):
    job_manager_url: str = Field("localhost:8081", description="Flink JobManager URL")
    checkpoint_dir: str = Field(
        str(BASE_DIR / "data" / "checkpoints"), description="Checkpoint directory"
    )
    parallelism: int = Field(1, description="Default parallelism")

    model_config = SettingsConfigDict(env_prefix="FLINK_")


class PostgresConfig(BaseSettings):
    host: str = Field("localhost", description="PostgreSQL host")
    port: int = Field(5432, description="PostgreSQL port")
    database: str = Field("confluence_kb", description="PostgreSQL database name")
    user: str = Field("postgres", description="PostgreSQL username")
    password: str = Field("", description="PostgreSQL password")
    min_connections: int = Field(1, description="Minimum connections")
    max_connections: int = Field(10, description="Maximum connections")

    model_config = SettingsConfigDict(env_prefix="POSTGRES_")


class DocumentIntelligenceConfig(BaseSettings):
    endpoint: Optional[str] = Field(None, description="Azure Document Intelligence endpoint")

    model_config = SettingsConfigDict(env_prefix="DOCUMENT_INTELLIGENCE_")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    data_dir: Path = Field(BASE_DIR / "data", description="Data directory")
    
    log_level: str = Field("INFO", description="Logging level")

    confluence: ConfluenceConfig = Field(default_factory=ConfluenceConfig)
    kafka: KafkaConfig = Field(default_factory=KafkaConfig)
    flink: FlinkConfig = Field(default_factory=FlinkConfig)
    postgres: PostgresConfig = Field(default_factory=PostgresConfig)
    document_intelligence: DocumentIntelligenceConfig = Field(default_factory=DocumentIntelligenceConfig)


config = Settings()
