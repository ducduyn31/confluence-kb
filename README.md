# Confluence Knowledge Base for RAG

A knowledge base system for RAG using Confluence content. This system processes Confluence pages and makes them available for semantic search and retrieval.

## Architecture

This project implements a streaming data pipeline using Kafka and Flink to process Confluence content, with PostgreSQL (with pgvector extension) as the vector database. The system includes direct integration with Confluence Cloud via webhooks and REST API, as well as a CLI tool for on-demand exports.

For detailed architecture information, see the [Architecture Decision Record](adrs/001-confluence-kb-architecture.md).

## Features

- CLI tool for exporting Confluence content by URL, page ID, or space key
- Webhook handler for real-time updates from Confluence
- Streaming data pipeline using Kafka and Flink
- HTML processing using modern parsing libraries (selectolax and parsel)
- Vector storage in PostgreSQL with pgvector extension
- Version tracking for Confluence content
- Deduplication of content from different sources
- RAG query interface for semantic search

## Prerequisites

- Python 3.10 or higher
- Docker and Docker Compose (for development environment)
- Confluence Cloud account with API access

## Installation

1. Clone the repository:

```bash
git clone https://github.com/ducduyn31/confluence-kb.git
cd confluence-kb
```

2. Create a `.env` file in the project root with the following variables (see `.env.example` for a complete list):

```
# Confluence API settings
CONFLUENCE_URL=https://yourcompany.atlassian.net
CONFLUENCE_USERNAME=your-email@example.com
CONFLUENCE_API_TOKEN=your-api-token

# Application settings
DATA_DIR=./data
LOG_LEVEL=INFO
```

3. Start the development environment:

```bash
docker compose up -d
```

This will start all required services:
- Zookeeper
- Kafka
- Confluent Control Center (available at http://localhost:9021)
- Flink JobManager (available at http://localhost:8081)
- Flink TaskManager
- PostgreSQL with pgvector extension
- PgAdmin (available at http://localhost:5050, login with admin@example.com/admin)

4. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```
## Usage

### Export Confluence Content

Export a single page by URL:

```bash
python main.py export --url "https://yourcompany.atlassian.net/wiki/spaces/SPACE/pages/123456"
```

Export a single page by ID:

```bash
python main.py export --page-id "123456"
```

Export an entire space:

```bash
python main.py export --space "SPACE"
```

Export and send to Kafka pipeline:

```bash
python main.py export --url "https://yourcompany.atlassian.net/wiki/spaces/SPACE/pages/123456" --send
```

### Process Content

Run the HTML processor Flink job:

```bash
python main.py process --job html
```

### Query the Knowledge Base

(Not implemented yet)

```bash
python main.py query --query "Your search query"
```

## Development

### Docker Compose Development Environment

The Docker Compose setup provides a complete development environment with all required services. Here are some useful commands:

```bash
# Start all services
docker compose up -d

# View logs for all services
docker compose logs -f

# View logs for a specific service
docker compose logs -f kafka

# Stop all services
docker compose down

# Stop all services and remove volumes
docker compose down -v
```

### Web Interfaces

- **Confluent Control Center**: http://localhost:9021
  - Comprehensive management for Kafka
  - Monitor topics, brokers, and consumers
  - View and search messages in topics
  - Create and manage topics
  - Monitor cluster health

- **Flink JobManager UI**: http://localhost:8081
  - Monitor Flink jobs
  - View job metrics and logs

- **PgAdmin**: http://localhost:5050
  - Login with admin@example.com/admin
  - Connect to PostgreSQL server using:
    - Host: postgres
    - Port: 5432
    - Database: confluence_kb
    - Username: postgres
    - Password: postgres

### Project Structure

```
confluence-kb/
├── adrs/                  # Architecture Decision Records
├── scripts/               # Utility scripts
│   ├── init_db.py         # Database initialization
│   ├── create_kafka_topics.py # Kafka topic creation
│   └── run_html_processor.py # Run Flink HTML processor
├── src/
│   └── confluence_kb/     # Main package
│       ├── cli/           # CLI tools
│       ├── database/      # Database models and utilities
│       ├── flink/         # Flink jobs
│       ├── kafka/         # Kafka producers and consumers
│       └── utils/         # Utility functions
├── data/                  # Data directory (created at runtime)
├── docker-compose.yml     # Docker Compose configuration
├── main.py                # Main entry point
└── README.md              # This file
```

### Utility Scripts

The project includes several utility scripts to help with common tasks:

#### Initialize Database

```bash
# Create the required database tables
python scripts/init_db.py
```

#### Create Kafka Topics

```bash
# Create the required Kafka topics
python scripts/create_kafka_topics.py
```

#### Run HTML Processor Job

```bash
# Run the Flink HTML processor job
python scripts/run_html_processor.py
```

### Running Tests

```bash
pytest
```