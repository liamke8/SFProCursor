"""
FastAPI dependencies for authentication and authorization
"""
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from database.database import get_database
from database.models import User, Organization


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_database)
) -> User:
    """Get current authenticated user"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    # Extract external_id from token (simplified for demo)
    # In production, verify JWT token with Clerk/Supabase
    external_id = authorization.replace("Bearer ", "")
    
    result = await db.execute(
        select(User).where(User.external_id == external_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user


async def get_current_org(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
) -> Organization:
    """Get current user's organization"""
    
    result = await db.execute(
        select(Organization).where(Organization.id == current_user.org_id)
    )
    org = result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return org


def require_role(min_role: str):
    """Dependency factory for role-based access control"""
    
    role_hierarchy = {
        "editor": 1,
        "admin": 2,
        "owner": 3
    }
    
    def role_checker(current_user: User = Depends(get_current_user)):
        user_role_level = role_hierarchy.get(current_user.role.value, 0)
        required_level = role_hierarchy.get(min_role, 999)
        
        if user_role_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        return current_user
    
    return role_checker
