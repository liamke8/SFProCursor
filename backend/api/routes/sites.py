"""
Sites management routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from datetime import datetime

from database.database import get_database
from database.models import Site, Organization, User
from api.dependencies import get_current_user, get_current_org

router = APIRouter()

class SiteCreate(BaseModel):
    domain: str
    name: Optional[str] = None
    robots_policy: str = "respect"

class SiteUpdate(BaseModel):
    name: Optional[str] = None
    robots_policy: Optional[str] = None

class SiteResponse(BaseModel):
    id: str
    domain: str
    name: Optional[str]
    robots_policy: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[SiteResponse])
async def list_sites(
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_database)
):
    """List all sites for current organization"""
    
    result = await db.execute(
        select(Site).where(Site.org_id == org.id).order_by(Site.created_at.desc())
    )
    sites = result.scalars().all()
    
    return [SiteResponse.from_orm(site) for site in sites]

@router.post("/", response_model=SiteResponse)
async def create_site(
    site_data: SiteCreate,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_database)
):
    """Create a new site"""
    
    # Check if site with domain already exists in org
    result = await db.execute(
        select(Site).where(
            Site.org_id == org.id,
            Site.domain == site_data.domain
        )
    )
    existing_site = result.scalar_one_or_none()
    
    if existing_site:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Site with this domain already exists"
        )
    
    # Create new site
    site = Site(
        org_id=org.id,
        domain=site_data.domain,
        name=site_data.name or site_data.domain,
        robots_policy=site_data.robots_policy
    )
    
    db.add(site)
    await db.commit()
    await db.refresh(site)
    
    return SiteResponse.from_orm(site)

@router.get("/{site_id}", response_model=SiteResponse)
async def get_site(
    site_id: str,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_database)
):
    """Get site by ID"""
    
    result = await db.execute(
        select(Site).where(
            Site.id == site_id,
            Site.org_id == org.id
        )
    )
    site = result.scalar_one_or_none()
    
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found"
        )
    
    return SiteResponse.from_orm(site)

@router.put("/{site_id}", response_model=SiteResponse)
async def update_site(
    site_id: str,
    site_data: SiteUpdate,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_database)
):
    """Update site"""
    
    result = await db.execute(
        select(Site).where(
            Site.id == site_id,
            Site.org_id == org.id
        )
    )
    site = result.scalar_one_or_none()
    
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found"
        )
    
    # Update fields
    if site_data.name is not None:
        site.name = site_data.name
    if site_data.robots_policy is not None:
        site.robots_policy = site_data.robots_policy
    
    site.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(site)
    
    return SiteResponse.from_orm(site)

@router.delete("/{site_id}")
async def delete_site(
    site_id: str,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_database)
):
    """Delete site"""
    
    result = await db.execute(
        select(Site).where(
            Site.id == site_id,
            Site.org_id == org.id
        )
    )
    site = result.scalar_one_or_none()
    
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found"
        )
    
    await db.delete(site)
    await db.commit()
    
    return {"message": "Site deleted successfully"}
