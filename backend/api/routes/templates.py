"""
Prompt templates routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from database.database import get_database
from database.models import PromptTemplate, Organization, User
from api.dependencies import get_current_user, get_current_org

router = APIRouter()

class TemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    system_prompt: str
    user_prompt: str
    output_schema: Optional[Dict[str, Any]] = None
    model: str = "gpt-3.5-turbo"
    vars_json: Optional[Dict[str, Any]] = None

class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    user_prompt: Optional[str] = None
    output_schema: Optional[Dict[str, Any]] = None
    model: Optional[str] = None
    vars_json: Optional[Dict[str, Any]] = None

class TemplateResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    system_prompt: str
    user_prompt: str
    output_schema: Optional[Dict[str, Any]]
    model: str
    vars_json: Optional[Dict[str, Any]]
    version: int
    is_builtin: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[TemplateResponse])
async def list_templates(
    include_builtin: bool = True,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_database)
):
    """List prompt templates"""
    
    query = select(PromptTemplate).where(PromptTemplate.org_id == org.id)
    
    if include_builtin:
        # Also include built-in templates
        query = query.union(
            select(PromptTemplate).where(PromptTemplate.is_builtin == True)
        )
    
    query = query.order_by(PromptTemplate.name)
    
    result = await db.execute(query)
    templates = result.scalars().all()
    
    return [TemplateResponse.from_orm(template) for template in templates]

@router.post("/", response_model=TemplateResponse)
async def create_template(
    template_data: TemplateCreate,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_database)
):
    """Create a new prompt template"""
    
    template = PromptTemplate(
        org_id=org.id,
        name=template_data.name,
        description=template_data.description,
        system_prompt=template_data.system_prompt,
        user_prompt=template_data.user_prompt,
        output_schema=template_data.output_schema,
        model=template_data.model,
        vars_json=template_data.vars_json or {}
    )
    
    db.add(template)
    await db.commit()
    await db.refresh(template)
    
    return TemplateResponse.from_orm(template)

@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: str,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_database)
):
    """Get template by ID"""
    
    result = await db.execute(
        select(PromptTemplate).where(
            PromptTemplate.id == template_id,
            (PromptTemplate.org_id == org.id) | (PromptTemplate.is_builtin == True)
        )
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    return TemplateResponse.from_orm(template)

@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: str,
    template_data: TemplateUpdate,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_database)
):
    """Update template"""
    
    result = await db.execute(
        select(PromptTemplate).where(
            PromptTemplate.id == template_id,
            PromptTemplate.org_id == org.id,
            PromptTemplate.is_builtin == False  # Can't update built-in templates
        )
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found or cannot be updated"
        )
    
    # Update fields
    update_data = template_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)
    
    template.updated_at = datetime.utcnow()
    template.version += 1
    
    await db.commit()
    await db.refresh(template)
    
    return TemplateResponse.from_orm(template)

@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_database)
):
    """Delete template"""
    
    result = await db.execute(
        select(PromptTemplate).where(
            PromptTemplate.id == template_id,
            PromptTemplate.org_id == org.id,
            PromptTemplate.is_builtin == False  # Can't delete built-in templates
        )
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found or cannot be deleted"
        )
    
    await db.delete(template)
    await db.commit()
    
    return {"message": "Template deleted successfully"}
