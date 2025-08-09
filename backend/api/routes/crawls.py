"""
Crawl management routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from database.database import get_database
from database.models import Site, Crawl, CrawlMode, CrawlStatus, Organization
from api.dependencies import get_current_user, get_current_org

router = APIRouter()

class CrawlCreate(BaseModel):
    site_id: str
    mode: CrawlMode = CrawlMode.FULL
    urls: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None

class CrawlResponse(BaseModel):
    id: str
    site_id: str
    started_at: datetime
    completed_at: Optional[datetime]
    mode: CrawlMode
    total_pages: int
    pages_crawled: int
    pages_failed: int
    status: CrawlStatus
    config: Optional[Dict[str, Any]]
    error_message: Optional[str]
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[CrawlResponse])
async def list_crawls(
    site_id: Optional[str] = None,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_database)
):
    """List crawls for organization or specific site"""
    
    query = select(Crawl).join(Site).where(Site.org_id == org.id)
    
    if site_id:
        query = query.where(Crawl.site_id == site_id)
        
    query = query.order_by(Crawl.started_at.desc())
    
    result = await db.execute(query)
    crawls = result.scalars().all()
    
    return [CrawlResponse.from_orm(crawl) for crawl in crawls]

@router.post("/", response_model=CrawlResponse)
async def create_crawl(
    crawl_data: CrawlCreate,
    background_tasks: BackgroundTasks,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_database)
):
    """Create a new crawl"""
    
    # Verify site belongs to organization
    result = await db.execute(
        select(Site).where(
            Site.id == crawl_data.site_id,
            Site.org_id == org.id
        )
    )
    site = result.scalar_one_or_none()
    
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found"
        )
    
    # Create crawl record
    crawl = Crawl(
        site_id=crawl_data.site_id,
        mode=crawl_data.mode,
        status=CrawlStatus.PENDING,
        config=crawl_data.config or {}
    )
    
    db.add(crawl)
    await db.commit()
    await db.refresh(crawl)
    
    # Start crawl in background
    background_tasks.add_task(start_crawl_task, crawl.id, crawl_data.urls)
    
    return CrawlResponse.from_orm(crawl)

@router.get("/{crawl_id}", response_model=CrawlResponse)
async def get_crawl(
    crawl_id: str,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_database)
):
    """Get crawl by ID"""
    
    result = await db.execute(
        select(Crawl)
        .join(Site)
        .where(
            Crawl.id == crawl_id,
            Site.org_id == org.id
        )
    )
    crawl = result.scalar_one_or_none()
    
    if not crawl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crawl not found"
        )
    
    return CrawlResponse.from_orm(crawl)

@router.post("/{crawl_id}/cancel")
async def cancel_crawl(
    crawl_id: str,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_database)
):
    """Cancel a running crawl"""
    
    result = await db.execute(
        select(Crawl)
        .join(Site)
        .where(
            Crawl.id == crawl_id,
            Site.org_id == org.id
        )
    )
    crawl = result.scalar_one_or_none()
    
    if not crawl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crawl not found"
        )
    
    if crawl.status not in [CrawlStatus.PENDING, CrawlStatus.RUNNING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel crawl that is not pending or running"
        )
    
    crawl.status = CrawlStatus.CANCELLED
    crawl.completed_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": "Crawl cancelled successfully"}

async def start_crawl_task(crawl_id: str, urls: Optional[List[str]] = None):
    """Background task to start crawl"""
    from services.crawler import WebCrawler, CrawlerConfig
    from database.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        try:
            # Get the crawl and site
            result = await db.execute(
                select(Crawl, Site)
                .join(Site, Crawl.site_id == Site.id)
                .where(Crawl.id == crawl_id)
            )
            row = result.first()
            
            if not row:
                print(f"Crawl {crawl_id} not found")
                return
            
            crawl, site = row
            
            # Update crawl status
            crawl.status = CrawlStatus.RUNNING
            await db.commit()
            
            # Configure crawler
            config = CrawlerConfig(
                max_pages=crawl.config.get('max_pages', 1000) if crawl.config else 1000,
                max_depth=crawl.config.get('max_depth', 3) if crawl.config else 3,
                delay_min=crawl.config.get('delay_min', 1.0) if crawl.config else 1.0,
                delay_max=crawl.config.get('delay_max', 3.0) if crawl.config else 3.0,
                respect_robots=site.robots_policy == "respect"
            )
            
            # Start crawler
            async with WebCrawler(config) as crawler:
                results = await crawler.crawl_site(site, crawl, urls)
                
                # Update crawl with results
                crawl.total_pages = results['total_pages']
                crawl.pages_crawled = results['pages_crawled'] 
                crawl.pages_failed = results['pages_failed']
                
                if results['pages_failed'] > 0 and results['pages_crawled'] == 0:
                    crawl.status = CrawlStatus.FAILED
                    crawl.error_message = "; ".join(results['errors'][:5])  # First 5 errors
                else:
                    crawl.status = CrawlStatus.COMPLETED
                
                crawl.completed_at = datetime.utcnow()
                await db.commit()
                
                print(f"Completed crawl {crawl_id}: {results['pages_crawled']} pages crawled, {results['pages_failed']} failed")
                
        except Exception as e:
            print(f"Failed to execute crawl {crawl_id}: {str(e)}")
            
            # Update crawl status to failed
            try:
                result = await db.execute(select(Crawl).where(Crawl.id == crawl_id))
                crawl = result.scalar_one_or_none()
                if crawl:
                    crawl.status = CrawlStatus.FAILED
                    crawl.error_message = str(e)
                    crawl.completed_at = datetime.utcnow()
                    await db.commit()
            except:
                pass
            
            import traceback
            traceback.print_exc()
