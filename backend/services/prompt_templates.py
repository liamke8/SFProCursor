"""
Built-in SEO prompt templates
"""
from typing import Dict, List, Any
from database.models import PromptTemplate

# Built-in SEO prompt templates
BUILTIN_TEMPLATES = [
    {
        "id": "title-generator",
        "name": "Title Tag Generator",
        "description": "Generate optimized page titles for better SEO and click-through rates",
        "system_prompt": """You are an expert SEO copywriter. Your task is to create compelling, SEO-optimized page titles that:

1. Are 50-60 characters long (optimal for search results)
2. Include the primary keyword naturally
3. Are compelling and click-worthy
4. Accurately represent the page content
5. Include the brand name when appropriate

Guidelines:
- Put the most important keywords at the beginning
- Use power words that encourage clicks
- Avoid keyword stuffing
- Make it human-readable and engaging
- Include modifiers like "2025", "Guide", "Best", etc. when relevant""",
        "user_prompt": """Create an optimized title tag for this page:

URL: {url}
Current Title: {title}
H1: {h1}
Content Summary: {content_excerpt}
Primary Keywords: {keywords}
Brand: {brand}

Requirements:
- Length: 50-60 characters
- Include primary keyword naturally
- Make it compelling and click-worthy
- Brand inclusion: {brand_position}

Return ONLY a JSON object with this structure:
{
  "title": "The optimized title",
  "length": 57,
  "rationale": "Explanation of why this title works",
  "keyword_placement": "primary",
  "alternatives": ["Alternative 1", "Alternative 2"]
}""",
        "output_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "maxLength": 60},
                "length": {"type": "integer"},
                "rationale": {"type": "string"},
                "keyword_placement": {"type": "string"},
                "alternatives": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 3
                }
            },
            "required": ["title", "length", "rationale"]
        },
        "vars_json": {
            "url": "Page URL",
            "title": "Current title",
            "h1": "Main heading", 
            "content_excerpt": "First 500 chars of content",
            "keywords": "Target keywords",
            "brand": "Brand name",
            "brand_position": "start|end|none"
        },
        "model": "gpt-4-turbo"
    },
    
    {
        "id": "meta-description",
        "name": "Meta Description Generator", 
        "description": "Write compelling meta descriptions that improve click-through rates",
        "system_prompt": """You are an expert SEO copywriter specializing in meta descriptions. Create descriptions that:

1. Are 140-155 characters long (optimal for search results)
2. Include the primary keyword naturally
3. Provide a clear value proposition
4. Include a call-to-action when appropriate
5. Accurately summarize the page content
6. Are compelling and encourage clicks

Guidelines:
- Front-load important keywords
- Use active voice
- Include numbers, benefits, or unique selling points
- End with a CTA when appropriate
- Avoid duplicate content
- Make every character count""",
        "user_prompt": """Create an optimized meta description for this page:

URL: {url}
Current Description: {description}
Title: {title}
H1: {h1}
Content Summary: {content_excerpt}
Target Keywords: {keywords}
Page Type: {page_type}

Requirements:
- Length: 140-155 characters
- Include primary keyword naturally
- Clear value proposition
- Compelling and click-worthy

Return ONLY a JSON object with this structure:
{
  "description": "The optimized meta description",
  "length": 147,
  "rationale": "Why this description works",
  "cta_included": true,
  "alternatives": ["Alternative 1", "Alternative 2"]
}""",
        "output_schema": {
            "type": "object",
            "properties": {
                "description": {"type": "string", "maxLength": 160},
                "length": {"type": "integer"},
                "rationale": {"type": "string"},
                "cta_included": {"type": "boolean"},
                "alternatives": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 3
                }
            },
            "required": ["description", "length", "rationale"]
        },
        "vars_json": {
            "url": "Page URL",
            "description": "Current meta description",
            "title": "Page title",
            "h1": "Main heading",
            "content_excerpt": "First 1000 chars of content", 
            "keywords": "Target keywords",
            "page_type": "homepage|product|blog|service"
        },
        "model": "gpt-4-turbo"
    },
    
    {
        "id": "keywords-extract",
        "name": "Primary Keywords Extractor",
        "description": "Identify and extract primary and secondary keywords from page content",
        "system_prompt": """You are an expert SEO keyword analyst. Your task is to identify the most relevant keywords for a page based on its content, structure, and context.

Guidelines:
1. Identify 1 primary keyword (most important)
2. Find 3-5 secondary keywords (supporting topics)
3. Consider search intent (informational, commercial, navigational, transactional)
4. Analyze keyword difficulty and search volume potential
5. Ensure keywords are relevant to the actual content
6. Focus on long-tail variations when appropriate""",
        "user_prompt": """Analyze this page and extract the most relevant keywords:

URL: {url}
Title: {title}
H1: {h1}
H2 Tags: {h2_tags}
Content: {content_excerpt}
Meta Description: {description}

Identify:
1. Primary keyword (most important for this page)
2. Secondary keywords (3-5 supporting keywords)
3. Search intent category
4. Keyword difficulty estimate

Return ONLY a JSON object with this structure:
{
  "primary": "main keyword phrase",
  "secondary": ["keyword 1", "keyword 2", "keyword 3"],
  "intent": "informational|commercial|navigational|transactional",
  "difficulty": "low|medium|high",
  "rationale": "Why these keywords were selected",
  "suggestions": ["Additional keyword opportunities"]
}""",
        "output_schema": {
            "type": "object",
            "properties": {
                "primary": {"type": "string"},
                "secondary": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 5
                },
                "intent": {
                    "type": "string",
                    "enum": ["informational", "commercial", "navigational", "transactional"]
                },
                "difficulty": {
                    "type": "string", 
                    "enum": ["low", "medium", "high"]
                },
                "rationale": {"type": "string"},
                "suggestions": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["primary", "secondary", "intent", "rationale"]
        },
        "vars_json": {
            "url": "Page URL",
            "title": "Page title",
            "h1": "Main heading",
            "h2_tags": "List of H2 headings",
            "content_excerpt": "First 2000 chars of content",
            "description": "Meta description"
        },
        "model": "gpt-4-turbo"
    },
    
    {
        "id": "content-score",
        "name": "SEO Content Scorer",
        "description": "Analyze and score page content for SEO effectiveness",
        "system_prompt": """You are an expert SEO auditor. Analyze page content and provide a comprehensive SEO score with specific recommendations.

Evaluation Criteria:
1. Title tag optimization (length, keywords, appeal)
2. Meta description quality (length, keywords, CTA)
3. Heading structure (H1, H2 hierarchy)
4. Content quality and length
5. Keyword usage and density
6. Internal linking opportunities
7. User experience factors

Scoring: 0-100 scale where:
- 90-100: Excellent
- 70-89: Good
- 50-69: Needs improvement
- Below 50: Poor""",
        "user_prompt": """Analyze and score this page for SEO effectiveness:

URL: {url}
Title: {title} (Length: {title_length})
Meta Description: {description} (Length: {description_length})
H1: {h1}
H2 Tags: {h2_tags}
Word Count: {word_count}
Content: {content_excerpt}

Provide scores for each element and overall recommendations.

Return ONLY a JSON object with this structure:
{
  "overall_score": 75,
  "scores": {
    "title": 80,
    "description": 70,
    "headings": 85,
    "content": 75,
    "keywords": 65
  },
  "issues": ["List of specific issues found"],
  "recommendations": ["Actionable improvement suggestions"],
  "priority": "high|medium|low"
}""",
        "output_schema": {
            "type": "object",
            "properties": {
                "overall_score": {"type": "integer", "minimum": 0, "maximum": 100},
                "scores": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "integer", "minimum": 0, "maximum": 100},
                        "description": {"type": "integer", "minimum": 0, "maximum": 100},
                        "headings": {"type": "integer", "minimum": 0, "maximum": 100},
                        "content": {"type": "integer", "minimum": 0, "maximum": 100},
                        "keywords": {"type": "integer", "minimum": 0, "maximum": 100}
                    }
                },
                "issues": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "recommendations": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "priority": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                }
            },
            "required": ["overall_score", "scores", "issues", "recommendations"]
        },
        "vars_json": {
            "url": "Page URL",
            "title": "Page title",
            "title_length": "Title character count",
            "description": "Meta description",
            "description_length": "Description character count",
            "h1": "Main heading",
            "h2_tags": "List of H2 headings",
            "word_count": "Total word count",
            "content_excerpt": "First 3000 chars of content"
        },
        "model": "gpt-4-turbo"
    },
    
    {
        "id": "schema-generator",
        "name": "JSON-LD Schema Generator",
        "description": "Generate structured data markup for better search engine understanding",
        "system_prompt": """You are an expert in structured data and JSON-LD schema markup. Generate valid, comprehensive schema that:

1. Follows schema.org standards exactly
2. Is relevant to the page content and type
3. Includes all available and appropriate properties
4. Uses proper data types and formats
5. Helps search engines understand the content better

Common schema types:
- Article (blog posts, news)
- Product (e-commerce items)
- Organization (company pages)
- Person (author profiles)
- FAQ (question/answer content)
- BreadcrumbList (navigation)
- LocalBusiness (local companies)""",
        "user_prompt": """Generate appropriate JSON-LD schema markup for this page:

URL: {url}
Page Type: {page_type}
Title: {title}
Description: {description}
Content: {content_excerpt}
Organization: {organization}
Author: {author}
Date Published: {date_published}
Date Modified: {date_modified}

Analyze the content and create the most appropriate schema type(s).

Return ONLY a JSON object with this structure:
{
  "schema_type": "Article",
  "schema_json": { /* Valid JSON-LD object */ },
  "validation": "valid|invalid",
  "recommendations": ["Additional schema opportunities"]
}""",
        "output_schema": {
            "type": "object", 
            "properties": {
                "schema_type": {"type": "string"},
                "schema_json": {"type": "object"},
                "validation": {
                    "type": "string",
                    "enum": ["valid", "invalid"]
                },
                "recommendations": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["schema_type", "schema_json", "validation"]
        },
        "vars_json": {
            "url": "Page URL",
            "page_type": "homepage|article|product|about|contact",
            "title": "Page title",
            "description": "Meta description",
            "content_excerpt": "First 2000 chars of content",
            "organization": "Organization name",
            "author": "Content author",
            "date_published": "Publication date",
            "date_modified": "Last modified date"
        },
        "model": "gpt-4-turbo"
    }
]

def get_builtin_templates() -> List[Dict[str, Any]]:
    """Get all built-in prompt templates"""
    return BUILTIN_TEMPLATES

def get_template_by_id(template_id: str) -> Dict[str, Any] | None:
    """Get a specific template by ID"""
    for template in BUILTIN_TEMPLATES:
        if template["id"] == template_id:
            return template
    return None

async def create_builtin_templates(db_session):
    """Create built-in templates in the database"""
    from sqlalchemy import select
    
    for template_data in BUILTIN_TEMPLATES:
        # Check if template already exists
        result = await db_session.execute(
            select(PromptTemplate).where(
                PromptTemplate.name == template_data["name"],
                PromptTemplate.is_builtin == True
            )
        )
        existing = result.scalar_one_or_none()
        
        if not existing:
            template = PromptTemplate(
                org_id=None,  # Built-in templates don't belong to an org
                name=template_data["name"],
                description=template_data["description"],
                system_prompt=template_data["system_prompt"],
                user_prompt=template_data["user_prompt"],
                output_schema=template_data["output_schema"],
                model=template_data["model"],
                vars_json=template_data["vars_json"],
                is_builtin=True
            )
            db_session.add(template)
    
    await db_session.commit()
