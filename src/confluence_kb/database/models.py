from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    AUTO = "auto"
    MANUAL = "manual"


class Document(BaseModel):
    id: Optional[int] = None
    title: str
    url: str
    space: str
    version: int
    source_type: SourceType
    source_priority: int = Field(default=1)
    content_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Chunk(BaseModel):
    id: Optional[int] = None
    document_id: int
    content: str
    embedding: List[float] = Field(default_factory=list)
    chunk_index: int
    version_id: int
    source_type: SourceType


class Version(BaseModel):
    id: Optional[int] = None
    document_id: int
    version_number: int
    source_type: SourceType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    hash: str


class SourceMapping(BaseModel):
    id: Optional[int] = None
    document_id: int
    confluence_page_id: str
    source_type: SourceType
    last_update_time: datetime = Field(default_factory=datetime.utcnow)


class Relationship(BaseModel):
    id: Optional[int] = None
    source_chunk_id: int
    target_chunk_id: int
    relationship_type: str


SQL_CREATE_TABLES = """
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create sequences starting from 10000
CREATE SEQUENCE IF NOT EXISTS documents_id_seq START WITH 10000;
CREATE SEQUENCE IF NOT EXISTS versions_id_seq START WITH 10000;
CREATE SEQUENCE IF NOT EXISTS chunks_id_seq START WITH 10000;
CREATE SEQUENCE IF NOT EXISTS source_mappings_id_seq START WITH 10000;
CREATE SEQUENCE IF NOT EXISTS relationships_id_seq START WITH 10000;

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY DEFAULT nextval('documents_id_seq'),
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    space TEXT NOT NULL,
    version INTEGER NOT NULL,
    source_type TEXT NOT NULL,
    source_priority INTEGER NOT NULL DEFAULT 1,
    content_hash TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Versions table
CREATE TABLE IF NOT EXISTS versions (
    id INTEGER PRIMARY KEY DEFAULT nextval('versions_id_seq'),
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    source_type TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    hash TEXT NOT NULL,
    UNIQUE(document_id, version_number, source_type)
);

-- Chunks table with vector support
CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY DEFAULT nextval('chunks_id_seq'),
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    chunk_index INTEGER NOT NULL,
    version_id INTEGER NOT NULL REFERENCES versions(id) ON DELETE CASCADE,
    source_type TEXT NOT NULL,
    UNIQUE(document_id, chunk_index, version_id)
);

-- Source mappings table
CREATE TABLE IF NOT EXISTS source_mappings (
    id INTEGER PRIMARY KEY DEFAULT nextval('source_mappings_id_seq'),
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    confluence_page_id TEXT NOT NULL,
    source_type TEXT NOT NULL,
    last_update_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(document_id, confluence_page_id, source_type)
);

-- Relationships table
CREATE TABLE IF NOT EXISTS relationships (
    id INTEGER PRIMARY KEY DEFAULT nextval('relationships_id_seq'),
    source_chunk_id INTEGER NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
    target_chunk_id INTEGER NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL,
    UNIQUE(source_chunk_id, target_chunk_id, relationship_type)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_documents_space ON documents(space);
CREATE INDEX IF NOT EXISTS idx_documents_content_hash ON documents(content_hash);
CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_version_id ON chunks(version_id);
CREATE INDEX IF NOT EXISTS idx_source_mappings_confluence_page_id ON source_mappings(confluence_page_id);

-- Create vector index for similarity search
CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON chunks USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
"""