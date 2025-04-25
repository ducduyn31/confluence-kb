#!/usr/bin/env python3
import logging
import sys
from pathlib import Path

import psycopg2
from rich.console import Console
from rich.logging import RichHandler

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from confluence_kb.config import config
from confluence_kb.database.models import SQL_CREATE_TABLES

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger("init-db")

console = Console()


def init_db():
    try:
        conn = psycopg2.connect(
            host=config.postgres.host,
            port=config.postgres.port,
            database=config.postgres.database,
            user=config.postgres.user,
            password=config.postgres.password,
        )
        conn.autocommit = True
        cursor = conn.cursor()

        console.print("[bold blue]Creating tables...[/]")
        cursor.execute(SQL_CREATE_TABLES)
        console.print("[bold green]Tables created successfully![/]")

        cursor.close()
        conn.close()

    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    console.print("[bold]Initializing database...[/]")
    init_db()
    console.print("[bold green]Database initialized successfully![/]")