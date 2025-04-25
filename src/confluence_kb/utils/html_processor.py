import logging
import re
from typing import Dict, List

from parsel import Selector
from selectolax.parser import HTMLParser

from confluence_kb.utils.markdown_processor import convert_html_to_markdown

logger = logging.getLogger(__name__)


def process_html_content(html_content: str) -> str:
    parser = HTMLParser(html_content)

    _remove_unnecessary_elements(parser)

    _clean_attributes(parser)

    _process_tables(parser)

    _process_code_blocks(parser)

    _process_confluence_macros(parser)

    cleaned_html = parser.body.html
    
    # Then convert the cleaned HTML to Markdown
    markdown_content = convert_html_to_markdown(cleaned_html)
    
    return markdown_content


def extract_text_content(html_content: str) -> str:
    """
    Extract plain text from HTML content.
    
    Args:
        html_content: HTML content
        
    Returns:
        Plain text content
    """
    parser = HTMLParser(html_content)
    
    # Remove script and style elements
    for tag in parser.css('script, style'):
        tag.decompose()
    
    # Get text content
    text = parser.body.text(separator=' ', strip=True)
    
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def extract_metadata(html_content: str) -> Dict[str, str]:
    """
    Extract metadata from HTML content.
    
    Args:
        html_content: HTML content
        
    Returns:
        Dictionary of metadata
    """
    metadata = {}
    
    # Use parsel for XPath queries
    selector = Selector(text=html_content)
    
    # Extract title
    title = selector.xpath('//h1[contains(@class, "title")]/text()').get()
    if title:
        metadata['title'] = title.strip()
    
    # Extract labels/tags
    labels = selector.css('.label-list .label-item::text').getall()
    if labels:
        metadata['labels'] = [label.strip() for label in labels]
    
    # Extract author information
    author = selector.css('.user-avatar-trigger::attr(data-username)').get()
    if author:
        metadata['author'] = author
    
    return metadata


def extract_sections(html_content: str) -> List[Dict[str, str]]:
    """
    Extract sections from HTML content based on headings.
    
    Args:
        html_content: HTML content
        
    Returns:
        List of sections with heading and content
    """
    parser = HTMLParser(html_content)
    sections = []
    
    # Find all headings
    headings = parser.css('h1, h2, h3, h4, h5, h6')
    
    for i, heading in enumerate(headings):
        # Get heading text and level
        heading_text = heading.text().strip()
        heading_level = int(heading.tag_name[1])
        
        # Get content until next heading of same or higher level
        content = []
        current = heading.next
        
        while current:
            if (current.tag_name and 
                current.tag_name.startswith('h') and 
                len(current.tag_name) == 2 and
                int(current.tag_name[1]) <= heading_level):
                break
                
            if current.html:
                content.append(current.html)
                
            current = current.next
            
        # Join content
        content_html = ''.join(content)
        
        # Add section
        sections.append({
            'heading': heading_text,
            'level': heading_level,
            'content': content_html,
            'text': extract_text_content(content_html)
        })
    
    return sections


def _remove_unnecessary_elements(parser: HTMLParser) -> None:
    for comment in parser.comments:
        comment.decompose()
    
    selectors_to_remove = [
        '.hidden',
        '.confluence-information-macro .confluence-information-macro-footer',
        '.page-metadata',
        '.page-tools',
        'script',
        'style',
        'meta',
        'link',
        '.aui-dropdown2',
    ]
    
    for selector in selectors_to_remove:
        for tag in parser.css(selector):
            tag.decompose()


def _clean_attributes(parser: HTMLParser) -> None:
    keep_attrs = {
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'title', 'width', 'height'],
        'table': ['border', 'cellpadding', 'cellspacing'],
        'th': ['colspan', 'rowspan'],
        'td': ['colspan', 'rowspan'],
        'code': ['class'],
        'pre': ['class'],
        'div': ['class'], 
    }
    
    for node in parser.root.traverse():
        if not node.tag_name:
            continue
            
        attrs_to_keep = keep_attrs.get(node.tag_name, [])
        
        attrs_to_remove = []
        for attr in node.attributes:
            if attr not in attrs_to_keep:
                attrs_to_remove.append(attr)
                
        for attr in attrs_to_remove:
            del node.attributes[attr]


def _process_tables(parser: HTMLParser) -> None:
    for table in parser.css('table'):
        if 'border' not in table.attributes:
            table.attributes['border'] = '1'
            
        if 'cellpadding' not in table.attributes:
            table.attributes['cellpadding'] = '4'
            
        if 'cellspacing' not in table.attributes:
            table.attributes['cellspacing'] = '0'


def _process_code_blocks(parser: HTMLParser) -> None:
    for code_block in parser.css('.code-block'):
        language = None
        for class_name in code_block.attributes.get('class', '').split():
            if class_name.startswith('language-'):
                language = class_name[9:]
                break
        
        code_content = code_block.text(strip=True)
        
        new_pre = parser.create_tag('pre')
        new_code = parser.create_tag('code')
        
        if language:
            new_code.attributes['class'] = f'language-{language}'
            
        new_code.text = code_content
        new_pre.append(new_code)
        
        code_block.replace_with(new_pre)


def _process_confluence_macros(parser: HTMLParser) -> None:
    for macro in parser.css('.confluence-information-macro'):
        macro_type = None
        
        for class_name in macro.attributes.get('class', '').split():
            if class_name.startswith('confluence-information-macro-'):
                macro_type = class_name[27:]
                break
        
        if not macro_type:
            continue
            
        content_elem = macro.css_first('.confluence-information-macro-body')
        if not content_elem:
            continue
            
        content = content_elem.html
        
        new_div = parser.create_tag('div')
        new_div.attributes['class'] = f'info-box {macro_type}'
        
        title_elem = macro.css_first('.confluence-information-macro-header')
        if title_elem:
            title = title_elem.text(strip=True)
            title_h5 = parser.create_tag('h5')
            title_h5.text = title
            new_div.append(title_h5)
        
        content_div = parser.create_tag('div')
        content_div.html = content
        new_div.append(content_div)
        
        macro.replace_with(new_div)
