"""
Prompt runs routes for bulk generation
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from database.database import get_database
from database.models import (
    PromptRun, PromptTemplate, RowGeneration, 
    PromptRunStatus, Organization, User, Page, Site
)
from api.dependencies import get_current_user, get_current_org

router = APIRouter()

class RunCreate(BaseModel):
    template_id: str
    page_ids: List[str]
    config: Optional[Dict[str, Any]] = None
    variants: int = 1
    context_columns: List[str] = ["title", "h1", "content_md"]

class RunResponse(BaseModel):
    id: str
    template_id: str
    status: PromptRunStatus
    total_rows: int
    completed_rows: int
    failed_rows: int
    config: Optional[Dict[str, Any]]
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class GenerationResponse(BaseModel):
    id: str
    page_id: str
    input_context_json: Dict[str, Any]
    output_json: Dict[str, Any]
    tokens_in: int
    tokens_out: int
    variant: int
    model_used: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[RunResponse])
async def list_runs(
    template_id: Optional[str] = None,
    status: Optional[PromptRunStatus] = None,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_database)
):
    """List prompt runs"""
    
    query = (
        select(PromptRun)
        .join(PromptTemplate)
        .where(
            (PromptTemplate.org_id == org.id) | (PromptTemplate.is_builtin == True)
        )
    )
    
    if template_id:
        query = query.where(PromptRun.template_id == template_id)
    
    if status:
        query = query.where(PromptRun.status == status)
    
    query = query.order_by(PromptRun.created_at.desc())
    
    result = await db.execute(query)
    runs = result.scalars().all()
    
    return [RunResponse.from_orm(run) for run in runs]

@router.post("/", response_model=RunResponse)
async def create_run(
    run_data: RunCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_database)
):
    """Create a new prompt run"""
    
    # Verify template exists and is accessible
    result = await db.execute(
        select(PromptTemplate).where(
            PromptTemplate.id == run_data.template_id,
            (PromptTemplate.org_id == org.id) | (PromptTemplate.is_builtin == True)
        )
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Verify pages belong to organization
    result = await db.execute(
        select(Page)
        .join(Site)
        .where(
            Page.id.in_(run_data.page_ids),
            Site.org_id == org.id
        )
    )
    pages = result.scalars().all()
    
    if len(pages) != len(run_data.page_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Some pages not found or not accessible"
        )
    
    # Create prompt run
    prompt_run = PromptRun(
        template_id=run_data.template_id,
        user_id=current_user.id,
        status=PromptRunStatus.PENDING,
        total_rows=len(pages) * run_data.variants,
        config={
            "variants": run_data.variants,
            "context_columns": run_data.context_columns,
            **(run_data.config or {})
        }
    )
    
    db.add(prompt_run)
    await db.commit()
    await db.refresh(prompt_run)
    
    # Start generation in background
    background_tasks.add_task(
        execute_prompt_run,
        prompt_run.id,
        run_data.page_ids,
        run_data.variants,
        run_data.context_columns
    )
    
    return RunResponse.from_orm(prompt_run)

@router.get("/{run_id}", response_model=RunResponse)
async def get_run(
    run_id: str,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_database)
):
    """Get run by ID"""
    
    result = await db.execute(
        select(PromptRun)
        .join(PromptTemplate)
        .where(
            PromptRun.id == run_id,
            (PromptTemplate.org_id == org.id) | (PromptTemplate.is_builtin == True)
        )
    )
    run = result.scalar_one_or_none()
    
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found"
        )
    
    return RunResponse.from_orm(run)

@router.get("/{run_id}/generations", response_model=List[GenerationResponse])
async def get_run_generations(
    run_id: str,
    page_id: Optional[str] = None,
    variant: Optional[int] = None,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_database)
):
    """Get generations for a run"""
    
    # Verify run exists and is accessible
    result = await db.execute(
        select(PromptRun)
        .join(PromptTemplate)
        .where(
            PromptRun.id == run_id,
            (PromptTemplate.org_id == org.id) | (PromptTemplate.is_builtin == True)
        )
    )
    run = result.scalar_one_or_none()
    
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found"
        )
    
    # Get generations
    query = select(RowGeneration).where(RowGeneration.prompt_run_id == run_id)
    
    if page_id:
        query = query.where(RowGeneration.page_id == page_id)
    
    if variant is not None:
        query = query.where(RowGeneration.variant == variant)
    
    query = query.order_by(RowGeneration.created_at.desc())
    
    result = await db.execute(query)
    generations = result.scalars().all()
    
    return [GenerationResponse.from_orm(gen) for gen in generations]

@router.post("/{run_id}/cancel")
async def cancel_run(
    run_id: str,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_database)
):
    """Cancel a running prompt run"""
    
    result = await db.execute(
        select(PromptRun)
        .join(PromptTemplate)
        .where(
            PromptRun.id == run_id,
            (PromptTemplate.org_id == org.id) | (PromptTemplate.is_builtin == True)
        )
    )
    run = result.scalar_one_or_none()
    
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found"
        )
    
    if run.status not in [PromptRunStatus.PENDING, PromptRunStatus.RUNNING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel run that is not pending or running"
        )
    
    run.status = PromptRunStatus.FAILED  # Use FAILED for cancelled runs
    run.completed_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": "Run cancelled successfully"}

async def execute_prompt_run(
    run_id: str,
    page_ids: List[str],
    variants: int,
    context_columns: List[str]
):
    """Background task to execute prompt run"""
    from services.llm_service import llm_service
    from database.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        try:
            # Get the prompt run to find the template
            result = await db.execute(
                select(PromptRun).where(PromptRun.id == run_id)
            )
            prompt_run = result.scalar_one_or_none()
            
            if not prompt_run:
                print(f"Prompt run {run_id} not found")
                return
            
            # Execute the LLM service
            await llm_service.execute_prompt_run(
                run_id=run_id,
                template_id=prompt_run.template_id,
                page_ids=page_ids,
                context_columns=context_columns,
                variants=variants,
                db_session=db
            )
            
            print(f"Completed prompt run {run_id} for {len(page_ids)} pages")
            
        except Exception as e:
            print(f"Failed to execute prompt run {run_id}: {str(e)}")
            import traceback
            traceback.print_exc()
