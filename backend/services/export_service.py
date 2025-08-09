"""
Export service for CSV and data export functionality
"""
import csv
import io
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    Page, PageElement, Site, Organization, PromptRun, RowGeneration
)

logger = logging.getLogger(__name__)

class ExportService:
    """Service for exporting data to various formats"""
    
    def __init__(self):
        pass
    
    async def export_pages_csv(
        self,
        site_id: Optional[str],
        page_ids: Optional[List[str]],
        org: Organization,
        db_session: AsyncSession,
        include_generated_content: bool = False
    ) -> Dict[str, Any]:
        """Export pages to CSV format"""
        
        try:
            # Build query
            query = select(Page, PageElement, Site).outerjoin(
                PageElement, Page.id == PageElement.page_id
            ).join(
                Site, Page.site_id == Site.id
            ).where(
                Site.org_id == org.id
            )
            
            # Apply filters
            if site_id:
                query = query.where(Site.id == site_id)
            
            if page_ids:
                query = query.where(Page.id.in_(page_ids))
            
            # Execute query
            result = await db_session.execute(query)
            rows = result.fetchall()
            
            if not rows:
                return {
                    "error": "No pages found for export",
                    "success": False
                }
            
            # Prepare CSV data
            csv_data = []
            
            for page, elements, site in rows:
                row_data = {
                    'site_domain': site.domain,
                    'url': page.url,
                    'status_code': page.status_code,
                    'title': elements.title if elements else '',
                    'title_length': len(elements.title) if elements and elements.title else 0,
                    'description': elements.description if elements else '',
                    'description_length': len(elements.description) if elements and elements.description else 0,
                    'h1': elements.h1 if elements else '',
                    'h2_tags': json.dumps(elements.h2_json) if elements and elements.h2_json else '',
                    'word_count': page.word_count,
                    'canonical': page.canonical or '',
                    'meta_robots': page.meta_robots or '',
                    'last_crawled': page.last_crawled_at.isoformat() if page.last_crawled_at else '',
                    'missing_title': not bool((elements.title or '').strip()) if elements else True,
                    'missing_description': not bool((elements.description or '').strip()) if elements else True,
                    'missing_h1': not bool((elements.h1 or '').strip()) if elements else True,
                    'thin_content': page.word_count < 300,
                    'has_error': page.status_code >= 400 if page.status_code else False
                }
                
                # Add generated content if requested
                if include_generated_content:
                    generated_content = await self._get_latest_generated_content(
                        page.id, db_session
                    )
                    row_data.update(generated_content)
                
                csv_data.append(row_data)
            
            # Generate CSV
            csv_content = self._generate_csv_content(csv_data)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            site_name = rows[0][2].domain if site_id else "all_sites"
            filename = f"seo_export_{site_name}_{timestamp}.csv"
            
            return {
                "filename": filename,
                "content": csv_content,
                "content_type": "text/csv",
                "row_count": len(csv_data),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"CSV export failed: {str(e)}")
            return {
                "error": str(e),
                "success": False
            }
    
    async def export_prompt_results_csv(
        self,
        run_id: str,
        org: Organization,
        db_session: AsyncSession
    ) -> Dict[str, Any]:
        """Export prompt run results to CSV"""
        
        try:
            # Get prompt run
            result = await db_session.execute(
                select(PromptRun).where(PromptRun.id == run_id)
            )
            prompt_run = result.scalar_one_or_none()
            
            if not prompt_run:
                return {
                    "error": "Prompt run not found",
                    "success": False
                }
            
            # Get generations with page data
            query = select(
                RowGeneration, Page, PageElement, Site
            ).join(
                Page, RowGeneration.page_id == Page.id
            ).outerjoin(
                PageElement, Page.id == PageElement.page_id
            ).join(
                Site, Page.site_id == Site.id
            ).where(
                and_(
                    RowGeneration.prompt_run_id == run_id,
                    Site.org_id == org.id
                )
            )
            
            result = await db_session.execute(query)
            rows = result.fetchall()
            
            if not rows:
                return {
                    "error": "No results found for this prompt run",
                    "success": False
                }
            
            # Prepare CSV data
            csv_data = []
            
            for generation, page, elements, site in rows:
                row_data = {
                    'site_domain': site.domain,
                    'url': page.url,
                    'original_title': elements.title if elements else '',
                    'original_description': elements.description if elements else '',
                    'original_h1': elements.h1 if elements else '',
                    'variant': generation.variant,
                    'model_used': generation.model_used,
                    'tokens_in': generation.tokens_in,
                    'tokens_out': generation.tokens_out,
                    'created_at': generation.created_at.isoformat() if generation.created_at else ''
                }
                
                # Add generated content fields
                output_json = generation.output_json or {}
                
                # Extract common generated fields
                if 'title' in output_json:
                    row_data['generated_title'] = output_json['title']
                    row_data['generated_title_length'] = len(output_json['title'])
                
                if 'description' in output_json:
                    row_data['generated_description'] = output_json['description']
                    row_data['generated_description_length'] = len(output_json['description'])
                
                if 'primary' in output_json:  # Keywords
                    row_data['primary_keyword'] = output_json['primary']
                    row_data['secondary_keywords'] = ', '.join(output_json.get('secondary', []))
                
                if 'overall_score' in output_json:  # Content scoring
                    row_data['seo_score'] = output_json['overall_score']
                    row_data['title_score'] = output_json.get('scores', {}).get('title', '')
                    row_data['description_score'] = output_json.get('scores', {}).get('description', '')
                
                if 'schema_type' in output_json:  # Schema generation
                    row_data['schema_type'] = output_json['schema_type']
                    row_data['schema_valid'] = output_json.get('validation', '') == 'valid'
                
                # Add raw output for debugging
                row_data['raw_output'] = json.dumps(output_json)
                
                csv_data.append(row_data)
            
            # Generate CSV
            csv_content = self._generate_csv_content(csv_data)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"prompt_results_{prompt_run.template_id}_{timestamp}.csv"
            
            return {
                "filename": filename,
                "content": csv_content,
                "content_type": "text/csv",
                "row_count": len(csv_data),
                "template_name": prompt_run.template_id,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Prompt results export failed: {str(e)}")
            return {
                "error": str(e),
                "success": False
            }
    
    async def _get_latest_generated_content(
        self,
        page_id: str,
        db_session: AsyncSession
    ) -> Dict[str, Any]:
        """Get the latest generated content for a page"""
        
        try:
            # Get most recent generations for this page
            query = select(RowGeneration).where(
                RowGeneration.page_id == page_id
            ).order_by(RowGeneration.created_at.desc()).limit(5)
            
            result = await db_session.execute(query)
            generations = result.scalars().all()
            
            generated_data = {}
            
            for generation in generations:
                output = generation.output_json or {}
                template_id = generation.prompt_run_id  # Would need to join to get actual template_id
                
                # Add generated content by type
                if 'title' in output:
                    generated_data['ai_title'] = output['title']
                    generated_data['ai_title_length'] = len(output['title'])
                
                if 'description' in output:
                    generated_data['ai_description'] = output['description']
                    generated_data['ai_description_length'] = len(output['description'])
                
                if 'primary' in output:
                    generated_data['ai_primary_keyword'] = output['primary']
                    generated_data['ai_secondary_keywords'] = ', '.join(output.get('secondary', []))
                
                if 'overall_score' in output:
                    generated_data['ai_seo_score'] = output['overall_score']
                
                # Only take the first (most recent) of each type
                if len(generated_data) >= 4:  # Limit to avoid too many columns
                    break
            
            return generated_data
            
        except Exception as e:
            logger.error(f"Failed to get generated content: {str(e)}")
            return {}
    
    def _generate_csv_content(self, data: List[Dict[str, Any]]) -> str:
        """Generate CSV content from data"""
        
        if not data:
            return ""
        
        # Get all unique keys from all rows
        all_keys = set()
        for row in data:
            all_keys.update(row.keys())
        
        # Sort keys for consistent column order
        fieldnames = sorted(all_keys)
        
        # Generate CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
        
        writer.writeheader()
        for row in data:
            # Clean data for CSV
            clean_row = {}
            for key, value in row.items():
                if value is None:
                    clean_row[key] = ''
                elif isinstance(value, (list, dict)):
                    clean_row[key] = json.dumps(value)
                else:
                    clean_row[key] = str(value)
            
            writer.writerow(clean_row)
        
        return output.getvalue()


# Global service instance
export_service = ExportService()
