"""
Export and publishing routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import csv
import io

from database.database import get_database
from database.models import (
    Site, Page, PageElement, RowGeneration, 
    PublishJob, PublishJobStatus, Organization, User
)
from api.dependencies import get_current_user, get_current_org
from services.export_service import export_service
from services.wordpress_service import wordpress_service

router = APIRouter()

class ExportRequest(BaseModel):
    site_id: Optional[str] = None
    page_ids: Optional[List[str]] = None
    columns: List[str] = [
        "url", "title_current", "title_generated", 
        "description_current", "description_generated",
        "h1", "word_count", "status_code"
    ]
    format: str = "csv"

class PublishRequest(BaseModel):
    page_ids: List[str]
    site_id: str
    fields_to_publish: List[str] = ["title", "description"]
    publish_mode: str = "draft"  # draft or live

class PublishResponse(BaseModel):
    job_id: str
    page_count: int
    status: PublishJobStatus
    
    class Config:
        from_attributes = True

@router.post("/csv")
async def export_csv(
    request: ExportRequest,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_database)
):
    """Export pages data to CSV using the enhanced export service"""
    
    try:
        result = await export_service.export_pages_csv(
            site_id=request.site_id,
            page_ids=request.page_ids,
            org=org,
            db_session=db,
            include_generated_content=True  # Always include generated content
        )
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error', 'Export failed')
            )
        
        return Response(
            content=result['content'],
            media_type=result['content_type'],
            headers={
                "Content-Disposition": f"attachment; filename={result['filename']}"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Export failed"
        )

@router.post("/prompt-results/csv")
async def export_prompt_results_csv(
    run_id: str,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_database)
):
    """Export prompt run results to CSV"""
    
    try:
        result = await export_service.export_prompt_results_csv(
            run_id=run_id,
            org=org,
            db_session=db
        )
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error', 'Export failed')
            )
        
        return Response(
            content=result['content'],
            media_type=result['content_type'],
            headers={
                "Content-Disposition": f"attachment; filename={result['filename']}"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Export failed"
        )

class WordPressPublishRequest(BaseModel):
    page_ids: List[str]
    integration_id: str
    content_type: str = "both"  # titles, descriptions, both
    dry_run: bool = False

@router.post("/publish", response_model=PublishResponse)
async def publish_to_cms(
    request: PublishRequest,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_database)
):
    """Legacy publish endpoint - maintained for compatibility"""
    
    # Convert to new format and call WordPress service
    wp_request = WordPressPublishRequest(
        page_ids=request.page_ids,
        integration_id="default",  # Would need to get from site
        content_type="both" if "title" in request.fields_to_publish and "description" in request.fields_to_publish else "titles" if "title" in request.fields_to_publish else "descriptions",
        dry_run=request.publish_mode == "draft"
    )
    
    return await publish_to_wordpress(wp_request, current_user, org, db)

@router.post("/publish/wordpress")
async def publish_to_wordpress(
    request: WordPressPublishRequest,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_database)
):
    """Publish SEO content to WordPress using the enhanced service"""
    
    try:
        result = await wordpress_service.publish_seo_content(
            page_ids=request.page_ids,
            integration_id=request.integration_id,
            content_type=request.content_type,
            org=org,
            db_session=db,
            dry_run=request.dry_run
        )
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error', 'Publishing failed')
            )
        
        return {
            "job_id": result['job_id'],
            "page_count": result['summary']['total'],
            "status": "completed" if result['summary']['failed'] == 0 else "partial",
            "summary": result['summary'],
            "dry_run": result['dry_run']
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Publishing failed"
        )

@router.get("/publish/{job_id}/status")
async def get_publish_status(
    job_id: str,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_database)
):
    """Get publish job status"""
    
    result = await db.execute(
        select(PublishJob)
        .join(Site, PublishJob.site_id == Site.id)
        .where(
            PublishJob.id == job_id,
            Site.org_id == org.id
        )
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publish job not found"
        )
    
    return {
        "job_id": str(job.id),
        "status": job.status,
        "created_at": job.created_at,
        "completed_at": job.completed_at,
        "error_message": job.error_message,
        "payload": job.payload_json
    }

@router.get("/publish/jobs")
async def list_publish_jobs(
    site_id: Optional[str] = None,
    status: Optional[PublishJobStatus] = None,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_database)
):
    """List publish jobs"""
    
    query = (
        select(PublishJob)
        .join(Site, PublishJob.site_id == Site.id)
        .where(Site.org_id == org.id)
    )
    
    if site_id:
        query = query.where(PublishJob.site_id == site_id)
    
    if status:
        query = query.where(PublishJob.status == status)
    
    query = query.order_by(PublishJob.created_at.desc()).limit(50)
    
    result = await db.execute(query)
    jobs = result.scalars().all()
    
    return [
        {
            "id": str(job.id),
            "site_id": str(job.site_id),
            "page_id": str(job.page_id),
            "status": job.status,
            "created_at": job.created_at,
            "completed_at": job.completed_at,
            "error_message": job.error_message
        }
        for job in jobs
    ]
