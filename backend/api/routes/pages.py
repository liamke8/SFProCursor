"""
Pages management routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from database.database import get_database
from database.models import Site, Page, PageElement, Organization
from api.dependencies import get_current_user, get_current_org

router = APIRouter()

class PageResponse(BaseModel):
    id: str
    site_id: str
    url: str
    status_code: Optional[int]
    canonical: Optional[str]
    meta_robots: Optional[str]
    word_count: int
    last_crawled_at: datetime
    
    # Page elements
    title: Optional[str] = None
    description: Optional[str] = None
    h1: Optional[str] = None
    h2_json: Optional[List[str]] = None
    
    class Config:
        from_attributes = True

class PageListResponse(BaseModel):
    pages: List[PageResponse]
    total: int
    page: int
    per_page: int
    total_pages: int

class PageFilters(BaseModel):
    site_id: Optional[str] = None
    status_code: Optional[int] = None
    missing_title: Optional[bool] = None
    missing_description: Optional[bool] = None
    word_count_min: Optional[int] = None
    word_count_max: Optional[int] = None
    search: Optional[str] = None

@router.get("/", response_model=PageListResponse)
async def list_pages(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    site_id: Optional[str] = Query(None),
    status_code: Optional[int] = Query(None),
    missing_title: Optional[bool] = Query(None),
    missing_description: Optional[bool] = Query(None),
    word_count_min: Optional[int] = Query(None),
    word_count_max: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_database)
):
    """List pages with filtering and pagination"""
    
    # Base query
    query = (
        select(Page, PageElement)
        .outerjoin(PageElement, Page.id == PageElement.page_id)
        .join(Site, Page.site_id == Site.id)
        .where(Site.org_id == org.id)
    )
    
    # Apply filters
    filters = []
    
    if site_id:
        filters.append(Page.site_id == site_id)
    
    if status_code:
        filters.append(Page.status_code == status_code)
    
    if missing_title:
        if missing_title:
            filters.append(or_(PageElement.title.is_(None), PageElement.title == ''))
        else:
            filters.append(and_(PageElement.title.isnot(None), PageElement.title != ''))
    
    if missing_description:
        if missing_description:
            filters.append(or_(PageElement.description.is_(None), PageElement.description == ''))
        else:
            filters.append(and_(PageElement.description.isnot(None), PageElement.description != ''))
    
    if word_count_min:
        filters.append(Page.word_count >= word_count_min)
    
    if word_count_max:
        filters.append(Page.word_count <= word_count_max)
    
    if search:
        search_filter = or_(
            Page.url.ilike(f'%{search}%'),
            PageElement.title.ilike(f'%{search}%'),
            PageElement.h1.ilike(f'%{search}%')
        )
        filters.append(search_filter)
    
    if filters:
        query = query.where(and_(*filters))
    
    # Get total count
    count_query = select(func.count(Page.id)).select_from(
        Page.join(Site, Page.site_id == Site.id)
        .outerjoin(PageElement, Page.id == PageElement.page_id)
    ).where(Site.org_id == org.id)
    
    if filters:
        count_query = count_query.where(and_(*filters))
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)
    
    # Order by last crawled
    query = query.order_by(Page.last_crawled_at.desc())
    
    # Execute query
    result = await db.execute(query)
    rows = result.all()
    
    # Format response
    pages = []
    for page_row, element_row in rows:
        page_data = {
            'id': str(page_row.id),
            'site_id': str(page_row.site_id),
            'url': page_row.url,
            'status_code': page_row.status_code,
            'canonical': page_row.canonical,
            'meta_robots': page_row.meta_robots,
            'word_count': page_row.word_count,
            'last_crawled_at': page_row.last_crawled_at,
        }
        
        if element_row:
            page_data.update({
                'title': element_row.title,
                'description': element_row.description,
                'h1': element_row.h1,
                'h2_json': element_row.h2_json,
            })
        
        pages.append(PageResponse(**page_data))
    
    total_pages = (total + per_page - 1) // per_page
    
    return PageListResponse(
        pages=pages,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )

@router.get("/{page_id}", response_model=PageResponse)
async def get_page(
    page_id: str,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_database)
):
    """Get page by ID with all details"""
    
    result = await db.execute(
        select(Page, PageElement)
        .outerjoin(PageElement, Page.id == PageElement.page_id)
        .join(Site, Page.site_id == Site.id)
        .where(
            Page.id == page_id,
            Site.org_id == org.id
        )
    )
    row = result.first()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found"
        )
    
    page_row, element_row = row
    
    page_data = {
        'id': str(page_row.id),
        'site_id': str(page_row.site_id),
        'url': page_row.url,
        'status_code': page_row.status_code,
        'canonical': page_row.canonical,
        'meta_robots': page_row.meta_robots,
        'word_count': page_row.word_count,
        'last_crawled_at': page_row.last_crawled_at,
    }
    
    if element_row:
        page_data.update({
            'title': element_row.title,
            'description': element_row.description,
            'h1': element_row.h1,
            'h2_json': element_row.h2_json,
        })
    
    return PageResponse(**page_data)

@router.get("/{page_id}/content")
async def get_page_content(
    page_id: str,
    format: str = Query("markdown", enum=["html", "markdown"]),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_database)
):
    """Get page content in HTML or Markdown format"""
    
    result = await db.execute(
        select(Page)
        .join(Site, Page.site_id == Site.id)
        .where(
            Page.id == page_id,
            Site.org_id == org.id
        )
    )
    page = result.scalar_one_or_none()
    
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found"
        )
    
    if format == "html":
        content = page.content_html
    else:
        content = page.content_md
    
    return {"content": content, "format": format}

@router.get("/{page_id}/elements")
async def get_page_elements(
    page_id: str,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_database)
):
    """Get all page elements including structured data"""
    
    result = await db.execute(
        select(Page, PageElement)
        .outerjoin(PageElement, Page.id == PageElement.page_id)
        .join(Site, Page.site_id == Site.id)
        .where(
            Page.id == page_id,
            Site.org_id == org.id
        )
    )
    row = result.first()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found"
        )
    
    page_row, element_row = row
    
    if not element_row:
        return {"message": "No elements found for this page"}
    
    return {
        "basic": {
            "title": element_row.title,
            "description": element_row.description,
            "h1": element_row.h1,
            "h2_list": element_row.h2_json,
        },
        "structured_data": {
            "open_graph": element_row.og_json,
            "schema": element_row.schema_json,
        },
        "media": {
            "images": element_row.images_json,
            "links": element_row.links_json,
        }
    }
