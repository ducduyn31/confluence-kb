import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool

from confluence_kb.config import config
from confluence_kb.database.models import SQL_CREATE_TABLES

logger = logging.getLogger(__name__)


class Database:
    _pool = None

    @classmethod
    def initialize(cls):
        if cls._pool is not None:
            return

        try:
            cls._pool = SimpleConnectionPool(
                config.postgres.min_connections,
                config.postgres.max_connections,
                host=config.postgres.host,
                port=config.postgres.port,
                dbname=config.postgres.database,
                user=config.postgres.user,
                password=config.postgres.password,
            )
            logger.info("Database connection pool initialized")

            with cls.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(SQL_CREATE_TABLES)
                conn.commit()
                logger.info("Database tables created or verified")

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    @classmethod
    def get_connection(cls):
        if cls._pool is None:
            cls.initialize()
        return cls._pool.getconn()

    @classmethod
    def release_connection(cls, conn):
        cls._pool.putconn(conn)

    @classmethod
    @asynccontextmanager
    async def connection(cls) -> AsyncGenerator:
        conn = cls.get_connection()
        try:
            yield conn
        finally:
            cls.release_connection(conn)

    @classmethod
    async def execute(cls, query, params=None):
        async with cls.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params or {})
                conn.commit()
                return cursor.rowcount

    @classmethod
    async def fetch_one(cls, query, params=None):
        async with cls.connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params or {})
                return cursor.fetchone()

    @classmethod
    async def fetch_all(cls, query, params=None):
        async with cls.connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params or {})
                return cursor.fetchall()

    @classmethod
    async def close(cls):
        if cls._pool is not None:
            cls._pool.closeall()
            cls._pool = None
            logger.info("Database connection pool closed")


def init_db():
    Database.initialize()