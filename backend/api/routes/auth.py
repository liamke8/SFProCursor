"""
Authentication routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from database.database import get_database
from database.models import User, Organization, UserRole
from api.dependencies import get_current_user, get_current_org

router = APIRouter()

class UserCreate(BaseModel):
    email: str
    name: str
    external_id: str
    org_name: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: UserRole
    org_id: str
    
    class Config:
        from_attributes = True

class OrganizationResponse(BaseModel):
    id: str
    name: str
    plan: str
    credits_balance: int
    
    class Config:
        from_attributes = True

@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_database)
):
    """Register a new user and optionally create organization"""
    
    # Check if user already exists
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )
    
    # Create organization if provided
    org = None
    if user_data.org_name:
        org = Organization(
            name=user_data.org_name,
            credits_balance=1000  # Initial credits
        )
        db.add(org)
        await db.flush()
    else:
        # Default to first organization for now
        result = await db.execute(select(Organization).limit(1))
        org = result.scalar_one_or_none()
        
        if not org:
            org = Organization(
                name="Default Organization",
                credits_balance=1000
            )
            db.add(org)
            await db.flush()
    
    # Create user
    user = User(
        email=user_data.email,
        name=user_data.name,
        external_id=user_data.external_id,
        org_id=org.id,
        role=UserRole.OWNER if user_data.org_name else UserRole.EDITOR
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return UserResponse.from_orm(user)

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return UserResponse.from_orm(current_user)

@router.get("/org", response_model=OrganizationResponse)
async def get_current_organization(
    org: Organization = Depends(get_current_org)
):
    """Get current organization information"""
    return OrganizationResponse.from_orm(org)
