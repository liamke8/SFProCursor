"""
Database models for SEO automation platform
"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Float, 
    ForeignKey, JSON, Enum as SQLEnum, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
import uuid

Base = declarative_base()

class UserRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"

class CrawlMode(str, Enum):
    FULL = "full"
    CSV = "csv"

class CrawlStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class PromptRunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class PublishJobStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class CreditKind(str, Enum):
    CRAWL = "crawl"
    GENERATION = "generation"

class Organization(Base):
    __tablename__ = "organizations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    plan = Column(String(50), default="starter")
    credits_balance = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship("User", back_populates="organization")
    sites = relationship("Site", back_populates="organization")
    templates = relationship("PromptTemplate", back_populates="organization")
    credit_entries = relationship("CreditLedger", back_populates="organization")

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.EDITOR)
    external_id = Column(String(255), unique=True)  # Clerk/Supabase ID
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    prompt_runs = relationship("PromptRun", back_populates="user")

class Site(Base):
    __tablename__ = "sites"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    domain = Column(String(255), nullable=False)
    name = Column(String(255))
    robots_policy = Column(String(20), default="respect")  # respect, ignore
    wp_integration_id = Column(UUID(as_uuid=True), ForeignKey("wordpress_integrations.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="sites")
    crawls = relationship("Crawl", back_populates="site")
    pages = relationship("Page", back_populates="site")
    wp_integration = relationship("WordPressIntegration", back_populates="site")
    publish_jobs = relationship("PublishJob", back_populates="site")
    
    __table_args__ = (
        UniqueConstraint('org_id', 'domain', name='unique_org_domain'),
    )

class Crawl(Base):
    __tablename__ = "crawls"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    mode = Column(SQLEnum(CrawlMode), default=CrawlMode.FULL)
    total_pages = Column(Integer, default=0)
    pages_crawled = Column(Integer, default=0)
    pages_failed = Column(Integer, default=0)
    status = Column(SQLEnum(CrawlStatus), default=CrawlStatus.PENDING)
    config = Column(JSON)  # Store crawl configuration
    error_message = Column(Text)
    
    # Relationships
    site = relationship("Site", back_populates="crawls")

class Page(Base):
    __tablename__ = "pages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False)
    url = Column(Text, nullable=False)
    status_code = Column(Integer)
    canonical = Column(Text)
    meta_robots = Column(String(255))
    content_html = Column(Text)
    content_md = Column(Text)
    word_count = Column(Integer, default=0)
    last_crawled_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    site = relationship("Site", back_populates="pages")
    elements = relationship("PageElement", back_populates="page", uselist=False)
    embeddings = relationship("PageEmbedding", back_populates="page")
    generations = relationship("RowGeneration", back_populates="page")
    
    __table_args__ = (
        Index('idx_pages_site_url', 'site_id', 'url'),
        Index('idx_pages_status', 'status_code'),
    )

class PageElement(Base):
    __tablename__ = "page_elements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    page_id = Column(UUID(as_uuid=True), ForeignKey("pages.id"), nullable=False, unique=True)
    title = Column(String(255))
    description = Column(Text)
    h1 = Column(String(255))
    h2_json = Column(JSON)  # List of H2 tags
    og_json = Column(JSON)  # Open Graph tags
    schema_json = Column(JSON)  # JSON-LD schema
    links_json = Column(JSON)  # Internal/external links with text
    images_json = Column(JSON)  # Images with alt text
    
    # Relationships
    page = relationship("Page", back_populates="elements")

class PageEmbedding(Base):
    __tablename__ = "page_embeddings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    page_id = Column(UUID(as_uuid=True), ForeignKey("pages.id"), nullable=False)
    kind = Column(String(20), nullable=False)  # page, title, h1, chunk
    vector = Column(Vector(1024))  # Adjust dimension based on embedding model
    content_text = Column(Text)  # Original text that was embedded
    chunk_index = Column(Integer)  # For chunk embeddings
    
    # Relationships
    page = relationship("Page", back_populates="embeddings")
    
    __table_args__ = (
        Index('idx_embeddings_page_kind', 'page_id', 'kind'),
    )

class PromptTemplate(Base):
    __tablename__ = "prompt_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    system_prompt = Column(Text, nullable=False)
    user_prompt = Column(Text, nullable=False)
    output_schema = Column(JSON)  # JSON schema for validation
    model = Column(String(100), default="gpt-3.5-turbo")
    vars_json = Column(JSON)  # Available variables
    version = Column(Integer, default=1)
    is_builtin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="templates")
    runs = relationship("PromptRun", back_populates="template")

class PromptRun(Base):
    __tablename__ = "prompt_runs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = Column(UUID(as_uuid=True), ForeignKey("prompt_templates.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(SQLEnum(PromptRunStatus), default=PromptRunStatus.PENDING)
    total_rows = Column(Integer, default=0)
    completed_rows = Column(Integer, default=0)
    failed_rows = Column(Integer, default=0)
    config = Column(JSON)  # Run configuration (variants, temperature, etc.)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relationships
    template = relationship("PromptTemplate", back_populates="runs")
    user = relationship("User", back_populates="prompt_runs")
    generations = relationship("RowGeneration", back_populates="prompt_run")

class RowGeneration(Base):
    __tablename__ = "row_generations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prompt_run_id = Column(UUID(as_uuid=True), ForeignKey("prompt_runs.id"), nullable=False)
    page_id = Column(UUID(as_uuid=True), ForeignKey("pages.id"), nullable=False)
    input_context_json = Column(JSON)  # Context data used for generation
    output_json = Column(JSON)  # Generated output
    tokens_in = Column(Integer, default=0)
    tokens_out = Column(Integer, default=0)
    variant = Column(Integer, default=1)
    model_used = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    prompt_run = relationship("PromptRun", back_populates="generations")
    page = relationship("Page", back_populates="generations")

class WordPressIntegration(Base):
    __tablename__ = "wordpress_integrations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False)
    base_url = Column(String(255), nullable=False)
    api_key = Column(String(255), nullable=False)  # Encrypted
    seo_plugin_detected = Column(String(50))  # yoast, rankmath, aioseo, tsf
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    site = relationship("Site", back_populates="wp_integration", uselist=False)

class PublishJob(Base):
    __tablename__ = "publish_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False)
    page_id = Column(UUID(as_uuid=True), ForeignKey("pages.id"), nullable=False)
    cms = Column(String(20), default="wordpress")
    payload_json = Column(JSON)  # Data to publish
    status = Column(SQLEnum(PublishJobStatus), default=PublishJobStatus.PENDING)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relationships
    site = relationship("Site", back_populates="publish_jobs")

class CreditLedger(Base):
    __tablename__ = "credit_ledger"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    kind = Column(SQLEnum(CreditKind), nullable=False)
    amount = Column(Integer, nullable=False)  # Negative for usage, positive for additions
    model = Column(String(100))  # For generation credits
    page_count = Column(Integer)  # For crawl credits
    run_id = Column(UUID(as_uuid=True))  # Reference to crawl or prompt run
    description = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="credit_entries")
    
    __table_args__ = (
        Index('idx_credits_org_kind', 'org_id', 'kind'),
        Index('idx_credits_created', 'created_at'),
    )
