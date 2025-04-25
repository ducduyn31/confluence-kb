from pathlib import Path
from typing import List, Optional, Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict, NoDecode

BASE_DIR = Path(__file__).parent.parent.parent


class ConfluenceConfig(BaseSettings):
    url: str = Field(..., description="Confluence Cloud URL")
    username: str = Field(..., description="Confluence username or email")
    api_token: str = Field(..., description="Confluence API token")
    verify_ssl: bool = Field(True, description="Verify SSL certificates")

    model_config = SettingsConfigDict(env_prefix="CONFLUENCE_")


class KafkaConfig(BaseSettings):
    bootstrap_servers: Annotated[List[str], NoDecode] = Field("localhost:9092", description="Kafka bootstrap servers")
    raw_topic: str = Field("raw-confluence-data", description="Raw data topic")
    processed_topic: str = Field("processed-text", description="Processed text topic")
    chunks_topic: str = Field("text-chunks", description="Text chunks topic")
    embeddings_topic: str = Field("embeddings", description="Embeddings topic")
    version_topic: str = Field("version-metadata", description="Version metadata topic")

    model_config = SettingsConfigDict(env_prefix="KAFKA_")
    
    @field_validator('bootstrap_servers', mode='before')
    @classmethod
    def parse_bootstrap_servers(cls, v):
        if isinstance(v, str):
            if v.startswith('[') and v.endswith(']'):
                v = v[1:-1]
            
            servers = []
            for server in v.split(','):
                server = server.strip().strip("'").strip('"').strip()
                if server:  
                    servers.append(server)
            return servers
        return v


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
