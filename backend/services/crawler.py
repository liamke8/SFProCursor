"""
Web crawler service with JavaScript rendering and bot detection workarounds
"""
import asyncio
import json
import re
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse
from datetime import datetime
import logging

from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from bs4 import BeautifulSoup
import markdownify
from readability import Document

from database.models import Site, Crawl, Page as PageModel, PageElement, CrawlStatus
from services.content_processor import ContentProcessor

logger = logging.getLogger(__name__)

class CrawlerConfig:
    """Configuration for web crawler"""
    
    def __init__(
        self,
        max_pages: int = 1000,
        max_depth: int = 5,
        delay_min: float = 1.0,
        delay_max: float = 3.0,
        timeout: int = 30000,
        respect_robots: bool = True,
        user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        block_resources: List[str] = None
    ):
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.timeout = timeout
        self.respect_robots = respect_robots
        self.user_agent = user_agent
        self.block_resources = block_resources or ['image', 'font', 'media']

class WebCrawler:
    """Main web crawler class with JS rendering and bot detection workarounds"""
    
    def __init__(self, config: CrawlerConfig = None):
        self.config = config or CrawlerConfig()
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.content_processor = ContentProcessor()
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()
        
    async def start(self):
        """Initialize browser and context"""
        playwright = await async_playwright().start()
        
        # Launch browser with stealth settings
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-extensions',
                '--disable-gpu',
                '--disable-web-security',
                '--no-first-run',
                '--no-default-browser-check'
            ]
        )
        
        # Create context with realistic settings
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent=self.config.user_agent,
            locale='en-US',
            timezone_id='America/New_York'
        )
        
        # Add stealth scripts
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            window.chrome = {
                runtime: {},
            };
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
        """)
        
    async def stop(self):
        """Close browser and context"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
            
    async def crawl_site(
        self, 
        site: Site, 
        crawl: Crawl,
        urls: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Crawl a site completely or with directed URLs
        
        Args:
            site: Site model instance
            crawl: Crawl model instance
            urls: Optional list of specific URLs to crawl (directed crawl)
            
        Returns:
            Dictionary with crawl results and statistics
        """
        
        results = {
            'total_pages': 0,
            'pages_crawled': 0,
            'pages_failed': 0,
            'errors': []
        }
        
        try:
            if urls:
                # Directed crawl with specific URLs
                await self._crawl_directed(site, crawl, urls, results)
            else:
                # Full site crawl
                await self._crawl_full_site(site, crawl, results)
                
        except Exception as e:
            logger.error(f"Crawl failed for site {site.domain}: {str(e)}")
            results['errors'].append(str(e))
            
        return results
        
    async def _crawl_directed(
        self, 
        site: Site, 
        crawl: Crawl, 
        urls: List[str], 
        results: Dict[str, Any]
    ):
        """Crawl specific URLs provided in CSV"""
        
        results['total_pages'] = len(urls)
        
        for url in urls:
            try:
                page_data = await self._crawl_page(url)
                if page_data:
                    await self._save_page_data(site, crawl, page_data)
                    results['pages_crawled'] += 1
                else:
                    results['pages_failed'] += 1
                    
                # Add delay between requests
                await asyncio.sleep(
                    self.config.delay_min + 
                    (self.config.delay_max - self.config.delay_min) * 0.5
                )
                
            except Exception as e:
                logger.error(f"Failed to crawl {url}: {str(e)}")
                results['pages_failed'] += 1
                results['errors'].append(f"{url}: {str(e)}")
                
    async def _crawl_full_site(
        self, 
        site: Site, 
        crawl: Crawl, 
        results: Dict[str, Any]
    ):
        """Full site crawl starting from domain root"""
        
        start_url = f"https://{site.domain}"
        if not start_url.startswith(('http://', 'https://')):
            start_url = f"https://{start_url}"
            
        visited = set()
        to_visit = [(start_url, 0)]  # (url, depth)
        
        while to_visit and len(visited) < self.config.max_pages:
            url, depth = to_visit.pop(0)
            
            if url in visited or depth > self.config.max_depth:
                continue
                
            visited.add(url)
            
            try:
                page_data = await self._crawl_page(url)
                if page_data:
                    await self._save_page_data(site, crawl, page_data)
                    results['pages_crawled'] += 1
                    
                    # Extract links for further crawling
                    if depth < self.config.max_depth:
                        links = self._extract_internal_links(
                            page_data.get('links_json', []), 
                            site.domain
                        )
                        for link in links:
                            if link not in visited:
                                to_visit.append((link, depth + 1))
                else:
                    results['pages_failed'] += 1
                    
                # Add delay between requests
                await asyncio.sleep(
                    self.config.delay_min + 
                    (self.config.delay_max - self.config.delay_min) * 0.5
                )
                
            except Exception as e:
                logger.error(f"Failed to crawl {url}: {str(e)}")
                results['pages_failed'] += 1
                results['errors'].append(f"{url}: {str(e)}")
                
        results['total_pages'] = len(visited)
        
    async def _crawl_page(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Crawl a single page and extract all SEO elements
        
        Returns:
            Dictionary with page data or None if failed
        """
        
        page = await self.context.new_page()
        
        try:
            # Block unnecessary resources
            await page.route("**/*", self._route_handler)
            
            # Navigate to page with retries
            response = await self._navigate_with_retries(page, url)
            
            if not response or response.status >= 400:
                logger.warning(f"Failed to load {url}: {response.status if response else 'No response'}")
                return None
                
            # Wait for page to stabilize
            await self._wait_for_stable_page(page)
            
            # Extract page data
            page_data = await self._extract_page_data(page, url)
            
            return page_data
            
        except Exception as e:
            logger.error(f"Error crawling {url}: {str(e)}")
            return None
            
        finally:
            await page.close()
            
    async def _route_handler(self, route):
        """Handle resource requests to block unnecessary content"""
        
        if route.request.resource_type in self.config.block_resources:
            await route.abort()
        else:
            await route.continue_()
            
    async def _navigate_with_retries(self, page: Page, url: str, max_retries: int = 3):
        """Navigate to URL with retries and different strategies"""
        
        for attempt in range(max_retries):
            try:
                response = await page.goto(
                    url,
                    timeout=self.config.timeout,
                    wait_until='networkidle'
                )
                return response
                
            except Exception as e:
                logger.warning(f"Navigation attempt {attempt + 1} failed for {url}: {str(e)}")
                
                if attempt < max_retries - 1:
                    # Try different wait strategies
                    if attempt == 1:
                        # Second attempt: wait for load event
                        try:
                            response = await page.goto(url, timeout=self.config.timeout, wait_until='load')
                            return response
                        except:
                            pass
                    
                    # Add delay before retry
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise e
                    
        return None
        
    async def _wait_for_stable_page(self, page: Page):
        """Wait for page to become stable (DOM size stops changing)"""
        
        stable_count = 0
        last_size = 0
        
        for _ in range(10):  # Max 10 attempts
            await asyncio.sleep(0.5)
            
            current_size = await page.evaluate("document.body.innerHTML.length")
            
            if current_size == last_size:
                stable_count += 1
                if stable_count >= 3:  # Stable for 3 consecutive checks
                    break
            else:
                stable_count = 0
                
            last_size = current_size
            
    async def _extract_page_data(self, page: Page, url: str) -> Dict[str, Any]:
        """Extract all SEO-relevant data from page"""
        
        # Get page content
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract basic metadata
        title = await page.title()
        
        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc.get('content', '') if meta_desc else ''
        
        # Canonical URL
        canonical = soup.find('link', attrs={'rel': 'canonical'})
        canonical_url = canonical.get('href', '') if canonical else ''
        
        # Meta robots
        meta_robots = soup.find('meta', attrs={'name': 'robots'})
        robots_content = meta_robots.get('content', '') if meta_robots else ''
        
        # Headings
        h1_elements = soup.find_all('h1')
        h1 = h1_elements[0].get_text(strip=True) if h1_elements else ''
        
        h2_elements = soup.find_all('h2')
        h2_list = [h2.get_text(strip=True) for h2 in h2_elements]
        
        # Open Graph data
        og_data = {}
        for og_tag in soup.find_all('meta', property=re.compile(r'^og:')):
            property_name = og_tag.get('property', '').replace('og:', '')
            og_data[property_name] = og_tag.get('content', '')
            
        # Twitter Card data
        twitter_data = {}
        for twitter_tag in soup.find_all('meta', attrs={'name': re.compile(r'^twitter:')}):
            name = twitter_tag.get('name', '').replace('twitter:', '')
            twitter_data[name] = twitter_tag.get('content', '')
            
        # Structured data (JSON-LD)
        schema_data = []
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                schema_obj = json.loads(script.string)
                schema_data.append(schema_obj)
            except json.JSONDecodeError:
                continue
                
        # Images with alt text
        images = []
        for img in soup.find_all('img'):
            src = img.get('src', '')
            alt = img.get('alt', '')
            if src:
                images.append({
                    'src': urljoin(url, src),
                    'alt': alt
                })
                
        # Links (internal and external)
        links = []
        domain = urlparse(url).netloc
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            if href.startswith(('http://', 'https://')):
                full_url = href
                is_internal = urlparse(href).netloc == domain
            else:
                full_url = urljoin(url, href)
                is_internal = True
                
            links.append({
                'url': full_url,
                'text': text,
                'is_internal': is_internal
            })
            
        # Clean content for markdown conversion
        content_html = self._clean_html_for_content(soup)
        content_md = self.content_processor.html_to_markdown(content_html)
        
        # Word count
        word_count = len(content_md.split())
        
        return {
            'url': url,
            'status_code': 200,  # TODO: Get actual status from response
            'canonical': canonical_url,
            'meta_robots': robots_content,
            'content_html': content_html,
            'content_md': content_md,
            'word_count': word_count,
            'title': title,
            'description': description,
            'h1': h1,
            'h2_json': h2_list,
            'og_json': {**og_data, **twitter_data},
            'schema_json': schema_data,
            'links_json': links,
            'images_json': images
        }
        
    def _clean_html_for_content(self, soup: BeautifulSoup) -> str:
        """Clean HTML to extract main content"""
        
        # Remove navigation, footer, sidebar elements
        for element in soup.find_all(['nav', 'header', 'footer', 'aside', 'script', 'style']):
            element.decompose()
            
        # Remove elements with common navigation/footer classes
        for selector in [
            '[class*="nav"]',
            '[class*="menu"]',
            '[class*="footer"]',
            '[class*="sidebar"]',
            '[class*="widget"]',
            '[class*="advertisement"]',
            '[class*="ad-"]'
        ]:
            for element in soup.select(selector):
                element.decompose()
                
        # Use readability to extract main content
        try:
            doc = Document(str(soup))
            return doc.summary()
        except:
            # Fallback to main content areas
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|main'))
            return str(main_content) if main_content else str(soup)
            
    def _extract_internal_links(self, links: List[Dict], domain: str) -> List[str]:
        """Extract internal links for further crawling"""
        
        internal_urls = []
        for link in links:
            if link.get('is_internal') and link.get('url'):
                url = link['url']
                # Filter out non-page URLs
                if not any(url.endswith(ext) for ext in ['.pdf', '.jpg', '.png', '.gif', '.css', '.js']):
                    internal_urls.append(url)
                    
        return list(set(internal_urls))  # Remove duplicates
        
    async def _save_page_data(self, site: Site, crawl: Crawl, page_data: Dict[str, Any], db_session=None):
        """Save extracted page data to database"""
        
        if not db_session:
            logger.warning(f"No database session provided, skipping save for {page_data['url']}")
            return
        
        try:
            from sqlalchemy import select
            from database.models import Page, PageElement
            from services.content_processor import ContentProcessor
            
            # Check if page already exists
            result = await db_session.execute(
                select(Page).where(
                    Page.site_id == site.id,
                    Page.url == page_data['url']
                )
            )
            existing_page = result.scalar_one_or_none()
            
            if existing_page:
                # Update existing page
                page = existing_page
                page.status_code = page_data['status_code']
                page.canonical = page_data['canonical']
                page.meta_robots = page_data['meta_robots']
                page.content_html = page_data['content_html']
                page.content_md = page_data['content_md']
                page.word_count = page_data['word_count']
                page.last_crawled_at = datetime.utcnow()
            else:
                # Create new page
                page = Page(
                    site_id=site.id,
                    url=page_data['url'],
                    status_code=page_data['status_code'],
                    canonical=page_data['canonical'],
                    meta_robots=page_data['meta_robots'],
                    content_html=page_data['content_html'],
                    content_md=page_data['content_md'],
                    word_count=page_data['word_count'],
                    last_crawled_at=datetime.utcnow()
                )
                db_session.add(page)
                await db_session.flush()  # Get the page ID
            
            # Handle page elements
            result = await db_session.execute(
                select(PageElement).where(PageElement.page_id == page.id)
            )
            existing_elements = result.scalar_one_or_none()
            
            if existing_elements:
                # Update existing elements
                elements = existing_elements
            else:
                # Create new elements
                elements = PageElement(page_id=page.id)
                db_session.add(elements)
            
            # Update element data
            elements.title = page_data['title']
            elements.description = page_data['description']
            elements.h1 = page_data['h1']
            elements.h2_json = page_data['h2_json']
            elements.og_json = page_data['og_json']
            elements.schema_json = page_data['schema_json']
            elements.links_json = page_data['links_json']
            elements.images_json = page_data['images_json']
            
            await db_session.commit()
            
            # Generate embeddings in the background
            if page_data['content_md']:
                try:
                    content_processor = ContentProcessor()
                    
                    # Generate page embeddings
                    page_embeddings = content_processor.generate_embeddings(
                        page_data['content_md'], 
                        chunk_size=1000, 
                        chunk_overlap=200
                    )
                    
                    # Generate element embeddings
                    element_embeddings = content_processor.generate_element_embeddings({
                        'title': page_data['title'] or '',
                        'h1': page_data['h1'] or '',
                        'description': page_data['description'] or ''
                    })
                    
                    # Save embeddings to database
                    from database.models import PageEmbedding
                    
                    # Clear existing embeddings
                    await db_session.execute(
                        select(PageEmbedding).where(PageEmbedding.page_id == page.id)
                    )
                    
                    # Add new embeddings
                    all_embeddings = page_embeddings + element_embeddings
                    for embedding_data in all_embeddings:
                        embedding = PageEmbedding(
                            page_id=page.id,
                            kind=embedding_data['kind'],
                            vector=embedding_data['vector'],
                            content_text=embedding_data['content_text'],
                            chunk_index=embedding_data['chunk_index']
                        )
                        db_session.add(embedding)
                    
                    await db_session.commit()
                    
                except Exception as e:
                    logger.error(f"Failed to generate embeddings for {page_data['url']}: {str(e)}")
                    # Don't fail the entire crawl for embedding errors
            
            logger.info(f"Saved page data for {page_data['url']}")
            
        except Exception as e:
            logger.error(f"Failed to save page data for {page_data['url']}: {str(e)}")
            await db_session.rollback()
            raise e
