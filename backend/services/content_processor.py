"""
Content processing service for HTML to Markdown conversion and embeddings
"""
import re
from typing import List, Dict, Any, Optional
import markdownify
from bs4 import BeautifulSoup
import numpy as np
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

class ContentProcessor:
    """Process HTML content into markdown and generate embeddings"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.embedding_model = None
        self.model_name = model_name
        self._load_embedding_model()
        
    def _load_embedding_model(self):
        """Load sentence transformer model for embeddings"""
        try:
            self.embedding_model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded embedding model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            
    def html_to_markdown(self, html_content: str) -> str:
        """
        Convert HTML to clean markdown with SEO-focused preservation
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            Clean markdown content
        """
        
        if not html_content:
            return ""
            
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove unwanted elements
        self._remove_unwanted_elements(soup)
        
        # Clean up formatting
        self._clean_formatting(soup)
        
        # Convert to markdown
        markdown_options = {
            'heading_style': 'ATX',  # Use # for headings
            'bullets': '-',  # Use - for lists
            'strip': ['script', 'style'],
            'convert': ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'a', 'strong', 'em', 'blockquote']
        }
        
        markdown = markdownify.markdownify(
            str(soup),
            **markdown_options
        )
        
        # Post-process markdown
        markdown = self._clean_markdown(markdown)
        
        return markdown
        
    def _remove_unwanted_elements(self, soup: BeautifulSoup):
        """Remove elements that don't contribute to content"""
        
        # Remove script, style, and meta elements
        for tag in ['script', 'style', 'meta', 'link', 'noscript']:
            for element in soup.find_all(tag):
                element.decompose()
                
        # Remove navigation and footer elements
        selectors_to_remove = [
            'nav', 'header', 'footer', 'aside',
            '[role="navigation"]',
            '[class*="nav"]', '[class*="menu"]',
            '[class*="footer"]', '[class*="sidebar"]',
            '[class*="widget"]', '[class*="ad"]',
            '[class*="advertisement"]', '[class*="banner"]',
            '[class*="popup"]', '[class*="modal"]',
            '[class*="cookie"]', '[class*="consent"]'
        ]
        
        for selector in selectors_to_remove:
            for element in soup.select(selector):
                element.decompose()
                
    def _clean_formatting(self, soup: BeautifulSoup):
        """Clean up HTML formatting for better markdown conversion"""
        
        # Remove empty elements
        for element in soup.find_all():
            if not element.get_text(strip=True) and not element.find('img'):
                element.decompose()
                
        # Convert div elements with heading-like classes to actual headings
        for div in soup.find_all('div'):
            class_list = div.get('class', [])
            class_str = ' '.join(class_list).lower()
            
            if any(keyword in class_str for keyword in ['title', 'heading', 'header']):
                # Determine heading level based on context
                level = 2  # Default to h2
                if 'main' in class_str or 'primary' in class_str:
                    level = 1
                elif 'sub' in class_str or 'secondary' in class_str:
                    level = 3
                    
                # Create new heading element
                new_heading = soup.new_tag(f'h{level}')
                new_heading.string = div.get_text(strip=True)
                div.replace_with(new_heading)
                
    def _clean_markdown(self, markdown: str) -> str:
        """Post-process markdown for consistency and readability"""
        
        # Remove excessive whitespace
        markdown = re.sub(r'\n\s*\n\s*\n', '\n\n', markdown)
        
        # Remove leading/trailing whitespace
        markdown = markdown.strip()
        
        # Ensure single space after list markers
        markdown = re.sub(r'^(\s*)[-*+](\s+)', r'\1- ', markdown, flags=re.MULTILINE)
        
        # Clean up link formatting
        markdown = re.sub(r'\[([^\]]*)\]\(\s*\)', r'\1', markdown)  # Remove empty links
        
        # Remove excessive emphasis markers
        markdown = re.sub(r'\*{3,}', '**', markdown)
        markdown = re.sub(r'_{3,}', '__', markdown)
        
        # Limit content length for embedding efficiency
        max_chars = 50000
        if len(markdown) > max_chars:
            markdown = markdown[:max_chars] + "..."
            
        return markdown
        
    def generate_embeddings(
        self, 
        content: str, 
        chunk_size: int = 1000, 
        chunk_overlap: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Generate embeddings for content with chunking
        
        Args:
            content: Text content to embed
            chunk_size: Size of each chunk in characters
            chunk_overlap: Overlap between chunks in characters
            
        Returns:
            List of embedding dictionaries with vectors and metadata
        """
        
        if not self.embedding_model or not content:
            return []
            
        embeddings = []
        
        try:
            # Generate full content embedding
            full_embedding = self.embedding_model.encode(content)
            embeddings.append({
                'kind': 'page',
                'vector': full_embedding.tolist(),
                'content_text': content[:500] + "..." if len(content) > 500 else content,
                'chunk_index': None
            })
            
            # Generate chunked embeddings for longer content
            if len(content) > chunk_size:
                chunks = self._chunk_text(content, chunk_size, chunk_overlap)
                
                for i, chunk in enumerate(chunks):
                    if chunk.strip():  # Skip empty chunks
                        chunk_embedding = self.embedding_model.encode(chunk)
                        embeddings.append({
                            'kind': 'chunk',
                            'vector': chunk_embedding.tolist(),
                            'content_text': chunk,
                            'chunk_index': i
                        })
                        
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {str(e)}")
            
        return embeddings
        
    def generate_element_embeddings(self, elements: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Generate embeddings for specific page elements
        
        Args:
            elements: Dictionary with element types and content
            
        Returns:
            List of element embeddings
        """
        
        if not self.embedding_model:
            return []
            
        embeddings = []
        
        # Element types to embed
        element_types = ['title', 'h1', 'description']
        
        for element_type in element_types:
            content = elements.get(element_type, '')
            if content and content.strip():
                try:
                    embedding = self.embedding_model.encode(content)
                    embeddings.append({
                        'kind': element_type,
                        'vector': embedding.tolist(),
                        'content_text': content,
                        'chunk_index': None
                    })
                except Exception as e:
                    logger.error(f"Failed to generate {element_type} embedding: {str(e)}")
                    
        return embeddings
        
    def _chunk_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Text to chunk
            chunk_size: Maximum chunk size in characters
            overlap: Overlap between chunks in characters
            
        Returns:
            List of text chunks
        """
        
        if len(text) <= chunk_size:
            return [text]
            
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundaries
            if end < len(text):
                # Look for sentence endings near the break point
                sentence_end = text.rfind('.', start, end)
                if sentence_end > start + chunk_size // 2:
                    end = sentence_end + 1
                else:
                    # Look for paragraph breaks
                    para_break = text.rfind('\n\n', start, end)
                    if para_break > start + chunk_size // 2:
                        end = para_break + 2
                    else:
                        # Look for word boundaries
                        word_break = text.rfind(' ', start, end)
                        if word_break > start + chunk_size // 2:
                            end = word_break
                            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
                
            # Move start position with overlap
            start = end - overlap
            if start <= 0:
                start = end
                
        return chunks
        
    def extract_keywords(self, content: str, max_keywords: int = 10) -> List[str]:
        """
        Extract key terms from content using simple frequency analysis
        
        Args:
            content: Text content
            max_keywords: Maximum number of keywords to return
            
        Returns:
            List of keywords sorted by relevance
        """
        
        # Simple keyword extraction - can be enhanced with NLP libraries
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'between', 'among', 'is', 'are',
            'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do',
            'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
            'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he',
            'she', 'it', 'we', 'they', 'them', 'their', 'what', 'which', 'who',
            'when', 'where', 'why', 'how'
        }
        
        # Extract words and count frequency
        words = re.findall(r'\b[a-zA-Z]{3,}\b', content.lower())
        word_freq = {}
        
        for word in words:
            if word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
                
        # Sort by frequency and return top keywords
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [keyword[0] for keyword in keywords[:max_keywords]]
