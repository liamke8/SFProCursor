"""
FastAPI main application
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import os

from database.database import init_database, close_database
from api.routes import auth, sites, crawls, pages, templates, runs, chat, exports


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    await init_database()
    yield
    # Shutdown
    await close_database()


app = FastAPI(
    title="SEO Automation Platform API",
    description="AI-powered SEO automation platform for content optimization at scale",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.vercel.app"]
)

# Include API routes
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(sites.router, prefix="/api/sites", tags=["sites"])
app.include_router(crawls.router, prefix="/api/crawls", tags=["crawls"])
app.include_router(pages.router, prefix="/api/pages", tags=["pages"])
app.include_router(templates.router, prefix="/api/templates", tags=["templates"])
app.include_router(runs.router, prefix="/api/runs", tags=["prompt-runs"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(exports.router, prefix="/api/exports", tags=["exports"])


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "SEO Automation Platform API", "status": "healthy"}


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False
    )
