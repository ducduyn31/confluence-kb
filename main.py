#!/usr/bin/env python3
import argparse
import logging
import os
import sys
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from confluence_kb.cli.export import app as export_app
from confluence_kb.config import config
from confluence_kb.database import init_db

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger("confluence-kb")

# Rich console for pretty output
console = Console()


def setup_environment():
    """Set up the environment."""
    # Create data directory if it doesn't exist
    os.makedirs(config.data_dir, exist_ok=True)
    logger.info(f"Data directory: {config.data_dir}")

    # Initialize database
    init_db()
    logger.info("Database initialized")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Confluence Knowledge Base")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export Confluence content")
    export_parser.add_argument("--url", help="Confluence page URL")
    export_parser.add_argument("--page-id", help="Confluence page ID")
    export_parser.add_argument("--space", help="Confluence space key")
    export_parser.add_argument("--output", help="Output directory")
    export_parser.add_argument("--send", action="store_true", help="Send to Kafka pipeline")
    export_parser.add_argument("--limit", type=int, default=100, help="Maximum pages to export")

    # Process command
    process_parser = subparsers.add_parser("process", help="Process Confluence content")
    process_parser.add_argument("--job", choices=["html", "chunk", "embed", "db"], help="Job to run")

    # Query command
    query_parser = subparsers.add_parser("query", help="Query the knowledge base")
    query_parser.add_argument("--query", help="Query string")
    query_parser.add_argument("--limit", type=int, default=10, help="Maximum results to return")

    args = parser.parse_args()

    # Set up environment
    setup_environment()

    # Run command
    if args.command == "export":
        if args.url:
            export_app(["url", args.url, "--output", args.output or "", "--send" if args.send else ""])
        elif args.page_id:
            export_app(["page", args.page_id, "--output", args.output or "", "--send" if args.send else ""])
        elif args.space:
            export_app(["space", args.space, "--output", args.output or "", "--send" if args.send else "", "--limit", str(args.limit)])
        else:
            export_app(["--help"])
    elif args.command == "process":
        if args.job == "html":
            from confluence_kb.flink.html_processor_job import run_job
            run_job()
        else:
            console.print("[bold yellow]Warning:[/] Job not implemented yet")
    elif args.command == "query":
        console.print("[bold yellow]Warning:[/] Query functionality not implemented yet")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
