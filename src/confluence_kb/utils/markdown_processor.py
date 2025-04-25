import logging
from typing import Dict

from markitdown import MarkItDown

from confluence_kb.config import config

logger = logging.getLogger(__name__)


def convert_html_to_markdown(html_content: str) -> str:
    try:
        docintel_endpoint = config.document_intelligence.endpoint
        
        if docintel_endpoint:
            logger.info("Using Document Intelligence for HTML to Markdown conversion")
            md = MarkItDown(docintel_endpoint=docintel_endpoint, enable_plugins=True)
        else:
            logger.warning("Document Intelligence endpoint not configured, falling back to standard Markitdown")
            md = MarkItDown(enable_plugins=True)
        
        from io import BytesIO
        html_bytes = BytesIO(html_content.encode('utf-8'))
        
        html_bytes.name = "content.html"
        
        result = md.convert(html_bytes)
        
        return result.text_content
    except Exception as e:
        logger.error(f"Error converting HTML to Markdown: {e}")
        return html_content


def extract_markdown_metadata(markdown_content: str) -> Dict[str, str]:
    metadata = {}
    
    import re
    title_match = re.search(r'^# (.+)$', markdown_content, re.MULTILINE)
    if title_match:
        metadata['title'] = title_match.group(1).strip()
    
    frontmatter_match = re.search(r'^---\s+(.*?)\s+---', markdown_content, re.DOTALL)
    if frontmatter_match:
        frontmatter = frontmatter_match.group(1)
        for line in frontmatter.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                metadata[key.strip()] = value.strip()
    
    return metadata