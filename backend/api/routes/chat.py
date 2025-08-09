"""
SEO Chat Agent routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from database.database import get_database
from database.models import Organization, User, Site
from api.dependencies import get_current_user, get_current_org

router = APIRouter()

class ChatMessage(BaseModel):
    role: str  # user, assistant, system
    content: str
    timestamp: Optional[datetime] = None

class ChatRequest(BaseModel):
    message: str
    site_id: Optional[str] = None
    context_pages: Optional[List[str]] = None  # Page IDs for context
    history: Optional[List[ChatMessage]] = None

class ChatResponse(BaseModel):
    message: str
    sources: Optional[List[Dict[str, Any]]] = None
    suggestions: Optional[List[str]] = None
    tools_used: Optional[List[str]] = None

class ToolRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]
    site_id: Optional[str] = None

class ToolResponse(BaseModel):
    tool_name: str
    result: Dict[str, Any]
    success: bool
    error: Optional[str] = None

@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_database)
):
    """Chat with the SEO agent"""
    
    # Verify site access if provided
    if request.site_id:
        result = await db.execute(
            select(Site).where(
                Site.id == request.site_id,
                Site.org_id == org.id
            )
        )
        site = result.scalar_one_or_none()
        
        if not site:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Site not found"
            )
    
    # Use RAG service for site-aware responses
    from services.rag_service import rag_service
    
    try:
        response = await rag_service.chat_with_site_context(
            query=request.message,
            site_id=request.site_id,
            conversation_history=request.history or [],
            org=org,
            db_session=db
        )
        
        return ChatResponse(
            message=response['message'],
            sources=response.get('sources'),
            suggestions=response.get('suggestions'),
            tools_used=response.get('tools_used')
        )
        
    except Exception as e:
        logger.error(f"Chat failed: {str(e)}")
        return ChatResponse(
            message="I'm sorry, I encountered an error while processing your request. Please try again.",
            suggestions=[
                "Try asking about page optimization opportunities",
                "Request a content gap analysis", 
                "Ask for SEO scoring of specific pages"
            ]
        )

@router.post("/tools/{tool_name}", response_model=ToolResponse)
async def execute_tool(
    tool_name: str,
    request: ToolRequest,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_database)
):
    """Execute a specific SEO tool"""
    
    available_tools = [
        "site_search",
        "get_page",
        "serp_analysis",
        "char_count",
        "word_count",
        "schema_validate",
        "compare_pages"
    ]
    
    if tool_name not in available_tools:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tool '{tool_name}' not available. Available tools: {available_tools}"
        )
    
    # Verify site access if provided
    if request.site_id:
        result = await db.execute(
            select(Site).where(
                Site.id == request.site_id,
                Site.org_id == org.id
            )
        )
        site = result.scalar_one_or_none()
        
        if not site:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Site not found"
            )
    
    # Execute tool using RAG service
    from services.rag_service import rag_service
    
    try:
        result = await rag_service.execute_seo_tool(
            tool_name=tool_name,
            parameters=request.parameters,
            site_id=request.site_id,
            org=org,
            db_session=db
        )
        
        return ToolResponse(
            tool_name=tool_name,
            result=result,
            success=result.get('success', True),
            error=result.get('error')
        )
        
    except Exception as e:
        logger.error(f"Tool execution failed: {str(e)}")
        return ToolResponse(
            tool_name=tool_name,
            result={},
            success=False,
            error=str(e)
        )

@router.get("/tools")
async def list_tools():
    """List available SEO tools"""
    
    tools = [
        {
            "name": "site_search",
            "description": "Search across all pages in a site using semantic search",
            "parameters": ["query", "limit"]
        },
        {
            "name": "get_page",
            "description": "Get detailed information about a specific page",
            "parameters": ["url"]
        },
        {
            "name": "serp_analysis",
            "description": "Analyze search engine results for a query",
            "parameters": ["query", "locale"]
        },
        {
            "name": "char_count",
            "description": "Count characters in text",
            "parameters": ["text"]
        },
        {
            "name": "word_count",
            "description": "Count words in text",
            "parameters": ["text"]
        },
        {
            "name": "schema_validate",
            "description": "Validate JSON-LD schema markup",
            "parameters": ["schema_json"]
        },
        {
            "name": "compare_pages",
            "description": "Compare two pages for SEO differences",
            "parameters": ["url_a", "url_b"]
        }
    ]
    
    return {"tools": tools}

@router.get("/suggestions")
async def get_suggestions(
    site_id: Optional[str] = None,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_database)
):
    """Get quick action suggestions for SEO improvements"""
    
    # Verify site access if provided
    if site_id:
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
    
    # TODO: Generate actual suggestions based on site analysis
    
    suggestions = [
        {
            "title": "Find pages needing refresh",
            "description": "Identify pages with outdated content or missing elements",
            "action": "site_search",
            "parameters": {"query": "missing title OR missing description"}
        },
        {
            "title": "Generate tone guide",
            "description": "Create a brand voice guide based on existing content",
            "action": "analyze_tone",
            "parameters": {"sample_size": 10}
        },
        {
            "title": "Content gap analysis",
            "description": "Find content opportunities compared to competitors",
            "action": "gap_analysis",
            "parameters": {"competitor_domains": []}
        }
    ]
    
    return {"suggestions": suggestions}
