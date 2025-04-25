import logging
from typing import Dict

from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors.kafka import FlinkKafkaConsumer, FlinkKafkaProducer
from pyflink.datastream.formats.json import JsonRowDeserializationSchema, JsonRowSerializationSchema

from confluence_kb.config import config
from confluence_kb.utils.html_processor import extract_metadata, extract_sections, process_html_content
from confluence_kb.utils.markdown_processor import extract_markdown_metadata

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_kafka_consumer() -> FlinkKafkaConsumer:
    properties = {
        'bootstrap.servers': config.kafka.bootstrap_servers,
        'group.id': 'html-processor-job',
        'auto.offset.reset': 'latest'
    }
    
    schema = JsonRowDeserializationSchema.builder().type_info(
        {
            'id': 'STRING',
            'title': 'STRING',
            'space': 'STRING',
            'version': 'INT',
            'url': 'STRING',
            'source_type': 'STRING',
            'content': 'STRING',
            'timestamp': 'STRING'
        }
    ).build()
    
    return FlinkKafkaConsumer(
        topics=config.kafka.raw_topic,
        deserialization_schema=schema,
        properties=properties
    )


def create_kafka_producer() -> FlinkKafkaProducer:
    properties = {
        'bootstrap.servers': config.kafka.bootstrap_servers,
        'transaction.timeout.ms': '300000'
    }
    
    schema = JsonRowSerializationSchema.builder().with_type_info(
        {
            'id': 'STRING',
            'title': 'STRING',
            'space': 'STRING',
            'version': 'INT',
            'url': 'STRING',
            'source_type': 'STRING',
            'content': 'STRING',
            'text': 'STRING',
            'metadata': 'MAP<STRING, STRING>',
            'sections': 'ARRAY<MAP<STRING, STRING>>',
            'timestamp': 'STRING'
        }
    ).build()
    
    return FlinkKafkaProducer(
        topic=config.kafka.processed_topic,
        serialization_schema=schema,
        producer_config=properties
    )


def process_content(data: Dict) -> Dict:
    try:
        html_content = data.get('content', '')
        
        markdown_content = process_html_content(html_content)
        
        text = markdown_content
        
        markdown_metadata = extract_markdown_metadata(markdown_content)
        if markdown_metadata:
            metadata = markdown_metadata
        else:
            metadata = extract_metadata(html_content)
        
        sections = extract_sections(html_content)
        
        processed_data = {
            'id': data.get('id'),
            'title': data.get('title'),
            'space': data.get('space'),
            'version': data.get('version'),
            'url': data.get('url'),
            'source_type': data.get('source_type'),
            'content': markdown_content,
            'text': text,
            'metadata': metadata,
            'sections': sections,
            'timestamp': data.get('timestamp')
        }
        
        return processed_data
        
    except Exception as e:
        logger.error(f"Error processing content: {e}")
        data['error'] = str(e)
        return data


def run_job():
    """Run the Flink HTML processor job."""
    env = StreamExecutionEnvironment.get_execution_environment()
    
    env.set_parallelism(config.flink.parallelism)
    
    env.enable_checkpointing(60000)  # 60 seconds
    
    source = create_kafka_consumer()
    
    sink = create_kafka_producer()
    
    stream = env.add_source(source)
    
    processed_stream = stream.map(process_content)
    
    processed_stream.add_sink(sink)
    
    env.execute("Content Processor Job")


if __name__ == "__main__":
    run_job()