import logging
import re
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import typer
from atlassian import Confluence
from confluent_kafka import Producer
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn

from confluence_kb.config import config
from confluence_kb.utils.html_processor import process_html_content

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger("confluence-export")

app = typer.Typer(
    help="Export Confluence content for the knowledge base",
    add_completion=False,
)

console = Console()


def get_confluence_client() -> Confluence:
    return Confluence(
        url=config.confluence.url,
        username=config.confluence.username,
        password=config.confluence.api_token,
        verify_ssl=config.confluence.verify_ssl,
    )


def extract_page_id_from_url(url: str) -> Optional[str]:
    # Example URL: https://yourcompany.atlassian.net/wiki/spaces/SPACE/pages/123456
    match = re.search(r"/pages/(\d+)", url)
    if match:
        return match.group(1)
    return None


def setup_kafka_producer() -> Producer:
    return Producer({"bootstrap.servers": config.kafka.bootstrap_servers})


def delivery_report(err, msg):
    if err is not None:
        logger.error(f"Message delivery failed: {err}")
    else:
        logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}]")


def send_to_kafka(producer: Producer, content: dict, topic: str = None):
    if topic is None:
        topic = config.kafka.raw_topic

    import json
    producer.produce(
        topic,
        key=content.get("id", "unknown"),
        value=json.dumps(content).encode("utf-8"),
        callback=delivery_report,
    )
    producer.flush()


@app.command()
def url(
    url: str = typer.Argument(..., help="Confluence page URL"),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output directory for exported content"
    ),
    send_to_pipeline: bool = typer.Option(
        False, "--send", "-s", help="Send to Kafka pipeline"
    ),
):
    page_id = extract_page_id_from_url(url)
    if not page_id:
        console.print(f"[bold red]Error:[/] Could not extract page ID from URL: {url}")
        raise typer.Exit(1)

    export_page_by_id(page_id, output, send_to_pipeline)


@app.command()
def page(
    page_id: str = typer.Argument(..., help="Confluence page ID"),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output directory for exported content"
    ),
    send_to_pipeline: bool = typer.Option(
        False, "--send", "-s", help="Send to Kafka pipeline"
    ),
):
    export_page_by_id(page_id, output, send_to_pipeline)


@app.command()
def space(
    space_key: str = typer.Argument(..., help="Confluence space key"),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output directory for exported content"
    ),
    send_to_pipeline: bool = typer.Option(
        False, "--send", "-s", help="Send to Kafka pipeline"
    ),
    limit: int = typer.Option(100, "--limit", "-l", help="Maximum pages to export"),
):
    try:
        confluence = get_confluence_client()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Fetching pages from space {space_key}...", total=None)
            
            pages = confluence.get_all_pages_from_space(space_key, limit=limit)
            progress.update(task, total=len(pages))
            
            if not pages:
                console.print(f"[bold yellow]Warning:[/] No pages found in space {space_key}")
                return
                
            producer = setup_kafka_producer() if send_to_pipeline else None
            
            for i, page in enumerate(pages):
                page_id = page["id"]
                progress.update(task, description=f"Exporting page {i+1}/{len(pages)}: {page['title']}")
                export_page_by_id(page_id, output, send_to_pipeline, producer, quiet=True)
                progress.update(task, completed=i+1)
            
            console.print(f"[bold green]Success:[/] Exported {len(pages)} pages from space {space_key}")
            
    except Exception as e:
        console.print(f"[bold red]Error:[/] Failed to export space {space_key}: {str(e)}")
        raise typer.Exit(1)


def export_page_by_id(
    page_id: str, 
    output: Optional[Path] = None, 
    send_to_pipeline: bool = False,
    producer: Optional[Producer] = None,
    quiet: bool = False
):
    try:
        confluence = get_confluence_client()
        
        if not quiet:
            console.print(f"Exporting page with ID: {page_id}")
        
        page = confluence.get_page_by_id(page_id, expand="body.storage,version,space")
        
        if not page:
            console.print(f"[bold red]Error:[/] Page with ID {page_id} not found")
            raise typer.Exit(1)
        
        title = page["title"]
        space_key = page["space"]["key"]
        content = page["body"]["storage"]["value"]
        version = page["version"]["number"]
        
        processed_content = process_html_content(content)
        
        metadata = {
            "id": page_id,
            "title": title,
            "space": space_key,
            "version": version,
            "url": f"{config.confluence.url}/wiki/spaces/{space_key}/pages/{page_id}",
            "source_type": "cli",
            "content": processed_content,
            "timestamp": str(page["version"]["when"]),
        }
        
        if output:
            output_dir = Path(output)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            space_dir = output_dir / space_key
            space_dir.mkdir(exist_ok=True)
            
            file_path = space_dir / f"{page_id}.md"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(processed_content)
                
            import json
            meta_path = space_dir / f"{page_id}.meta.json"
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)
                
            if not quiet:
                console.print(f"[bold green]Success:[/] Exported page '{title}' to {file_path}")
        
        if send_to_pipeline:
            if producer is None:
                producer = setup_kafka_producer()
            send_to_kafka(producer, metadata)
            if not quiet:
                console.print(f"[bold green]Success:[/] Sent page '{title}' to Kafka pipeline")
                
        return metadata
        
    except Exception as e:
        if not quiet:
            console.print(f"[bold red]Error:[/] Failed to export page {page_id}: {str(e)}")
        raise


if __name__ == "__main__":
    app()