#!/usr/bin/env python3
import logging
import sys
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from confluence_kb.flink.html_processor_job import run_job

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger("content-processor")

console = Console()


if __name__ == "__main__":
    console.print("[bold]Starting content processor Flink job (HTML to Markdown)...[/]")
    try:
        run_job()
    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        sys.exit(1)