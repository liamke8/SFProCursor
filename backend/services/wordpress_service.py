"""
WordPress publishing service for publishing SEO content
"""
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    Page, PageElement, Site, Organization, PublishJob, PublishJobStatus,
    WordPressIntegration, RowGeneration
)

logger = logging.getLogger(__name__)

class WordPressService:
    """Service for publishing content to WordPress sites"""
    
    def __init__(self):
        self.timeout = httpx.Timeout(30.0)
    
    async def publish_seo_content(
        self,
        page_ids: List[str],
        integration_id: str,
        content_type: str,  # 'titles', 'descriptions', 'both'
        org: Organization,
        db_session: AsyncSession,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Publish SEO content to WordPress"""
        
        try:
            # Get WordPress integration
            result = await db_session.execute(
                select(WordPressIntegration).where(
                    WordPressIntegration.id == integration_id,
                    WordPressIntegration.org_id == org.id
                )
            )
            integration = result.scalar_one_or_none()
            
            if not integration:
                return {
                    "error": "WordPress integration not found",
                    "success": False
                }
            
            # Create publish job
            job = PublishJob(
                org_id=org.id,
                integration_id=integration_id,
                page_ids=page_ids,
                content_type=content_type,
                status=PublishJobStatus.PENDING,
                dry_run=dry_run
            )
            db_session.add(job)
            await db_session.flush()
            
            # Process pages
            results = []
            success_count = 0
            failed_count = 0
            
            for page_id in page_ids:
                try:
                    result = await self._publish_single_page(
                        page_id, integration, content_type, org, db_session, dry_run
                    )
                    
                    if result['success']:
                        success_count += 1
                    else:
                        failed_count += 1
                    
                    results.append(result)
                    
                    # Small delay between requests
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Failed to publish page {page_id}: {str(e)}")
                    failed_count += 1
                    results.append({
                        "page_id": page_id,
                        "success": False,
                        "error": str(e)
                    })
            
            # Update job status
            if failed_count == 0:
                job.status = PublishJobStatus.COMPLETED
            elif success_count == 0:
                job.status = PublishJobStatus.FAILED
            else:
                job.status = PublishJobStatus.COMPLETED  # Partial success
            
            job.completed_at = datetime.utcnow()
            job.results_json = {
                "results": results,
                "summary": {
                    "total": len(page_ids),
                    "success": success_count,
                    "failed": failed_count
                }
            }
            
            await db_session.commit()
            
            return {
                "job_id": job.id,
                "success": True,
                "summary": {
                    "total": len(page_ids),
                    "success": success_count,
                    "failed": failed_count
                },
                "results": results[:10],  # Return first 10 for preview
                "dry_run": dry_run
            }
            
        except Exception as e:
            logger.error(f"WordPress publishing failed: {str(e)}")
            return {
                "error": str(e),
                "success": False
            }
    
    async def _publish_single_page(
        self,
        page_id: str,
        integration: WordPressIntegration,
        content_type: str,
        org: Organization,
        db_session: AsyncSession,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Publish content for a single page"""
        
        try:
            # Get page and elements
            result = await db_session.execute(
                select(Page, PageElement, Site).outerjoin(
                    PageElement, Page.id == PageElement.page_id
                ).join(
                    Site, Page.site_id == Site.id
                ).where(
                    Page.id == page_id,
                    Site.org_id == org.id
                )
            )
            row = result.first()
            
            if not row:
                return {
                    "page_id": page_id,
                    "success": False,
                    "error": "Page not found"
                }
            
            page, elements, site = row
            
            # Get generated content
            generated_content = await self._get_generated_content_for_page(
                page_id, content_type, db_session
            )
            
            if not generated_content:
                return {
                    "page_id": page_id,
                    "url": page.url,
                    "success": False,
                    "error": "No generated content found for this page"
                }
            
            # Find WordPress post by URL
            wp_post = await self._find_wordpress_post_by_url(
                page.url, integration
            )
            
            if not wp_post:
                return {
                    "page_id": page_id,
                    "url": page.url,
                    "success": False,
                    "error": "WordPress post not found for this URL"
                }
            
            # Prepare update data
            update_data = {}
            
            if content_type in ['titles', 'both'] and 'title' in generated_content:
                update_data['title'] = generated_content['title']
            
            if content_type in ['descriptions', 'both'] and 'description' in generated_content:
                # Handle different SEO plugins
                if integration.plugin_type == 'yoast':
                    update_data['meta'] = {
                        '_yoast_wpseo_metadesc': generated_content['description']
                    }
                elif integration.plugin_type == 'rankmath':
                    update_data['meta'] = {
                        'rank_math_description': generated_content['description']
                    }
                elif integration.plugin_type == 'seopress':
                    update_data['meta'] = {
                        '_seopress_titles_desc': generated_content['description']
                    }
                else:
                    # Generic meta description
                    update_data['meta'] = {
                        'meta_description': generated_content['description']
                    }
            
            if dry_run:
                return {
                    "page_id": page_id,
                    "url": page.url,
                    "wp_post_id": wp_post['id'],
                    "success": True,
                    "action": "dry_run",
                    "would_update": update_data,
                    "message": "Dry run - no changes made"
                }
            
            # Update WordPress post
            update_result = await self._update_wordpress_post(
                wp_post['id'], update_data, integration
            )
            
            if update_result['success']:
                return {
                    "page_id": page_id,
                    "url": page.url,
                    "wp_post_id": wp_post['id'],
                    "success": True,
                    "action": "updated",
                    "updated_fields": list(update_data.keys()),
                    "message": f"Successfully updated {', '.join(update_data.keys())}"
                }
            else:
                return {
                    "page_id": page_id,
                    "url": page.url,
                    "wp_post_id": wp_post['id'],
                    "success": False,
                    "error": update_result.get('error', 'Unknown WordPress API error')
                }
                
        except Exception as e:
            logger.error(f"Failed to publish page {page_id}: {str(e)}")
            return {
                "page_id": page_id,
                "success": False,
                "error": str(e)
            }
    
    async def _get_generated_content_for_page(
        self,
        page_id: str,
        content_type: str,
        db_session: AsyncSession
    ) -> Optional[Dict[str, str]]:
        """Get the latest generated content for a page"""
        
        try:
            # Get most recent generations
            query = select(RowGeneration).where(
                RowGeneration.page_id == page_id
            ).order_by(RowGeneration.created_at.desc()).limit(10)
            
            result = await db_session.execute(query)
            generations = result.scalars().all()
            
            content = {}
            
            for generation in generations:
                output = generation.output_json or {}
                
                # Extract title
                if content_type in ['titles', 'both'] and 'title' not in content:
                    if 'title' in output:
                        content['title'] = output['title']
                
                # Extract description
                if content_type in ['descriptions', 'both'] and 'description' not in content:
                    if 'description' in output:
                        content['description'] = output['description']
                
                # Stop when we have all needed content
                if content_type == 'titles' and 'title' in content:
                    break
                elif content_type == 'descriptions' and 'description' in content:
                    break
                elif content_type == 'both' and 'title' in content and 'description' in content:
                    break
            
            return content if content else None
            
        except Exception as e:
            logger.error(f"Failed to get generated content: {str(e)}")
            return None
    
    async def _find_wordpress_post_by_url(
        self,
        page_url: str,
        integration: WordPressIntegration
    ) -> Optional[Dict[str, Any]]:
        """Find WordPress post by URL"""
        
        try:
            # Extract path from URL for WordPress search
            from urllib.parse import urlparse
            parsed_url = urlparse(page_url)
            post_path = parsed_url.path.rstrip('/')
            
            # WordPress REST API search
            api_url = f"{integration.wp_url.rstrip('/')}/wp-json/wp/v2/posts"
            
            # Try different search strategies
            search_params = [
                {"slug": post_path.split('/')[-1]},  # Last segment as slug
                {"search": post_path.split('/')[-1]},  # Search by last segment
            ]
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                for params in search_params:
                    response = await client.get(
                        api_url,
                        params=params,
                        auth=(integration.wp_username, integration.wp_password)
                    )
                    
                    if response.status_code == 200:
                        posts = response.json()
                        
                        # Find exact match by comparing URLs
                        for post in posts:
                            post_link = post.get('link', '')
                            if self._urls_match(page_url, post_link):
                                return post
                        
                        # If no exact match, return first result
                        if posts:
                            return posts[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to find WordPress post: {str(e)}")
            return None
    
    async def _update_wordpress_post(
        self,
        post_id: int,
        update_data: Dict[str, Any],
        integration: WordPressIntegration
    ) -> Dict[str, Any]:
        """Update WordPress post via REST API"""
        
        try:
            api_url = f"{integration.wp_url.rstrip('/')}/wp-json/wp/v2/posts/{post_id}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    api_url,
                    json=update_data,
                    auth=(integration.wp_username, integration.wp_password)
                )
                
                if response.status_code == 200:
                    return {
                        "success": True,
                        "data": response.json()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"WordPress API error: {response.status_code} - {response.text}"
                    }
                    
        except Exception as e:
            logger.error(f"WordPress update failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _urls_match(self, url1: str, url2: str) -> bool:
        """Check if two URLs point to the same page"""
        
        from urllib.parse import urlparse
        
        parsed1 = urlparse(url1)
        parsed2 = urlparse(url2)
        
        # Compare paths (normalize trailing slashes)
        path1 = parsed1.path.rstrip('/')
        path2 = parsed2.path.rstrip('/')
        
        return path1 == path2
    
    async def test_wordpress_connection(
        self,
        integration: WordPressIntegration
    ) -> Dict[str, Any]:
        """Test WordPress connection and credentials"""
        
        try:
            api_url = f"{integration.wp_url.rstrip('/')}/wp-json/wp/v2/posts"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    api_url,
                    params={"per_page": 1},
                    auth=(integration.wp_username, integration.wp_password)
                )
                
                if response.status_code == 200:
                    posts = response.json()
                    return {
                        "success": True,
                        "message": "Connection successful",
                        "post_count": len(posts),
                        "wp_version": response.headers.get('X-WP-Version', 'Unknown')
                    }
                elif response.status_code == 401:
                    return {
                        "success": False,
                        "error": "Authentication failed - check username/password"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Connection failed: {response.status_code} - {response.text}"
                    }
                    
        except Exception as e:
            logger.error(f"WordPress connection test failed: {str(e)}")
            return {
                "success": False,
                "error": f"Connection error: {str(e)}"
            }


# Global service instance
wordpress_service = WordPressService()
