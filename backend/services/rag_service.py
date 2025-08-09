"""
RAG (Retrieval-Augmented Generation) service for site-aware chat
"""
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from datetime import datetime

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sentence_transformers import SentenceTransformer

from database.models import Site, Page, PageElement, PageEmbedding, Organization
from services.llm_service import LLMService

logger = logging.getLogger(__name__)

class RAGService:
    """Service for retrieval-augmented generation with site context"""
    
    def __init__(self):
        self.embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self.llm_service = LLMService()
        
    async def chat_with_site_context(
        self,
        query: str,
        site_id: Optional[str],
        conversation_history: List[Dict[str, str]],
        org: Organization,
        db_session: AsyncSession
    ) -> Dict[str, Any]:
        """
        Generate a response using RAG with site context
        
        Args:
            query: User's question/query
            site_id: Optional site to focus on
            conversation_history: Previous messages in conversation
            org: User's organization
            db_session: Database session
            
        Returns:
            Response with answer, sources, and suggestions
        """
        
        try:
            # 1. Generate query embedding
            query_embedding = self.embedding_model.encode(query)
            
            # 2. Retrieve relevant context
            context_chunks = await self._retrieve_relevant_context(
                query_embedding, site_id, org.id, db_session, top_k=5
            )
            
            # 3. Get site-level context if site_id provided
            site_context = None
            if site_id:
                site_context = await self._get_site_context(site_id, org.id, db_session)
            
            # 4. Build RAG prompt
            rag_prompt = await self._build_rag_prompt(
                query, context_chunks, site_context, conversation_history
            )
            
            # 5. Generate response
            response = await self.llm_service._call_llm(
                model="gpt-4-turbo",
                system_prompt=self._get_chat_system_prompt(),
                user_prompt=rag_prompt
            )
            
            # 6. Extract sources
            sources = []
            for chunk in context_chunks:
                if chunk['page_url'] not in [s['url'] for s in sources]:
                    sources.append({
                        'url': chunk['page_url'],
                        'title': chunk['page_title'],
                        'excerpt': chunk['content'][:200] + "...",
                        'relevance_score': float(chunk['similarity'])
                    })
            
            # 7. Generate follow-up suggestions
            suggestions = await self._generate_suggestions(query, site_context)
            
            return {
                'message': response.get('content', 'Sorry, I couldn\'t generate a response.'),
                'sources': sources,
                'suggestions': suggestions,
                'site_context': site_context['name'] if site_context else None,
                'tools_used': ['semantic_search', 'site_analysis'],
                'success': response.get('success', False)
            }
            
        except Exception as e:
            logger.error(f"RAG chat failed: {str(e)}")
            return {
                'message': f"Sorry, I encountered an error: {str(e)}",
                'sources': [],
                'suggestions': [],
                'success': False
            }
    
    async def _retrieve_relevant_context(
        self,
        query_embedding: np.ndarray,
        site_id: Optional[str],
        org_id: str,
        db_session: AsyncSession,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve most relevant content chunks using vector similarity"""
        
        try:
            # Build SQL query for vector similarity search
            where_clause = "WHERE s.org_id = :org_id"
            params = {"org_id": str(org_id)}
            
            if site_id:
                where_clause += " AND p.site_id = :site_id"
                params["site_id"] = str(site_id)
            
            # Use pgvector for similarity search
            query_sql = text(f"""
                SELECT 
                    pe.content_text,
                    pe.kind,
                    pe.chunk_index,
                    p.url as page_url,
                    elem.title as page_title,
                    p.word_count,
                    (pe.vector <-> :query_vector) as distance,
                    (1 - (pe.vector <-> :query_vector)) as similarity
                FROM page_embeddings pe
                JOIN pages p ON pe.page_id = p.id
                JOIN sites s ON p.site_id = s.id
                LEFT JOIN page_elements elem ON p.id = elem.page_id
                {where_clause}
                ORDER BY pe.vector <-> :query_vector
                LIMIT :limit
            """)
            
            params.update({
                "query_vector": query_embedding.tolist(),
                "limit": top_k
            })
            
            result = await db_session.execute(query_sql, params)
            rows = result.fetchall()
            
            context_chunks = []
            for row in rows:
                context_chunks.append({
                    'content': row.content_text,
                    'kind': row.kind,
                    'chunk_index': row.chunk_index,
                    'page_url': row.page_url,
                    'page_title': row.page_title or 'Untitled',
                    'word_count': row.word_count,
                    'distance': float(row.distance),
                    'similarity': float(row.similarity)
                })
            
            return context_chunks
            
        except Exception as e:
            logger.error(f"Failed to retrieve context: {str(e)}")
            return []
    
    async def _get_site_context(
        self, 
        site_id: str, 
        org_id: str, 
        db_session: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """Get high-level site context and statistics"""
        
        try:
            # Get site info
            result = await db_session.execute(
                select(Site).where(
                    Site.id == site_id,
                    Site.org_id == org_id
                )
            )
            site = result.scalar_one_or_none()
            
            if not site:
                return None
            
            # Get page statistics
            stats_query = text("""
                SELECT 
                    COUNT(*) as total_pages,
                    AVG(word_count) as avg_word_count,
                    COUNT(CASE WHEN elem.title IS NULL OR elem.title = '' THEN 1 END) as missing_titles,
                    COUNT(CASE WHEN elem.description IS NULL OR elem.description = '' THEN 1 END) as missing_descriptions,
                    COUNT(CASE WHEN p.status_code >= 400 THEN 1 END) as error_pages
                FROM pages p
                LEFT JOIN page_elements elem ON p.id = elem.page_id
                WHERE p.site_id = :site_id
            """)
            
            result = await db_session.execute(stats_query, {"site_id": site_id})
            stats = result.fetchone()
            
            # Get common page types/topics
            topics_query = text("""
                SELECT elem.h1, COUNT(*) as count
                FROM pages p
                JOIN page_elements elem ON p.id = elem.page_id
                WHERE p.site_id = :site_id AND elem.h1 IS NOT NULL
                GROUP BY elem.h1
                ORDER BY count DESC
                LIMIT 10
            """)
            
            result = await db_session.execute(topics_query, {"site_id": site_id})
            topics = [{"topic": row.h1, "count": row.count} for row in result.fetchall()]
            
            return {
                'name': site.name or site.domain,
                'domain': site.domain,
                'total_pages': stats.total_pages if stats else 0,
                'avg_word_count': int(stats.avg_word_count) if stats and stats.avg_word_count else 0,
                'missing_titles': stats.missing_titles if stats else 0,
                'missing_descriptions': stats.missing_descriptions if stats else 0,
                'error_pages': stats.error_pages if stats else 0,
                'common_topics': topics
            }
            
        except Exception as e:
            logger.error(f"Failed to get site context: {str(e)}")
            return None
    
    async def _build_rag_prompt(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        site_context: Optional[Dict[str, Any]],
        conversation_history: List[Dict[str, str]]
    ) -> str:
        """Build the RAG prompt with retrieved context"""
        
        # Format conversation history
        history_text = ""
        if conversation_history:
            for msg in conversation_history[-6:]:  # Last 6 messages
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                history_text += f"{role.title()}: {content}\n"
        
        # Format site context
        site_info = ""
        if site_context:
            site_info = f"""
SITE CONTEXT:
- Website: {site_context['name']} ({site_context['domain']})
- Total Pages: {site_context['total_pages']}
- Average Word Count: {site_context['avg_word_count']}
- Missing Titles: {site_context['missing_titles']}
- Missing Descriptions: {site_context['missing_descriptions']}
- Error Pages: {site_context['error_pages']}

COMMON TOPICS:
{chr(10).join([f"- {topic['topic']} ({topic['count']} pages)" for topic in site_context['common_topics'][:5]])}
"""
        
        # Format retrieved content
        context_text = ""
        if context_chunks:
            context_text = "RELEVANT CONTENT:\n\n"
            for i, chunk in enumerate(context_chunks, 1):
                context_text += f"{i}. From {chunk['page_title']} ({chunk['page_url']}):\n"
                context_text += f"   {chunk['content'][:500]}...\n\n"
        
        # Build complete prompt
        prompt = f"""Based on the following context about the website, please answer the user's question.

{site_info}

{context_text}

CONVERSATION HISTORY:
{history_text}

USER QUESTION: {query}

Please provide a helpful, accurate response based on the website content. If you reference specific pages, mention their URLs. Be specific and actionable in your SEO recommendations.

RESPONSE:"""
        
        return prompt
    
    def _get_chat_system_prompt(self) -> str:
        """Get the system prompt for the chat agent"""
        
        return """You are an expert SEO consultant and website analyst. You help users optimize their websites for search engines by:

1. Analyzing their website content and structure
2. Identifying SEO issues and opportunities  
3. Providing specific, actionable recommendations
4. Explaining technical concepts in understandable terms
5. Suggesting content improvements and optimizations

Guidelines:
- Always base your responses on the provided website data
- Be specific and cite page URLs when relevant
- Provide actionable recommendations, not just general advice
- Focus on high-impact improvements first
- Explain the "why" behind your recommendations
- If asked about competitor analysis or external data, clearly state limitations
- Keep responses concise but comprehensive

Available tools and data:
- Website crawl data (pages, titles, descriptions, content)
- SEO elements analysis (missing tags, word counts, etc.)
- Site structure and navigation
- Internal linking patterns
- Technical SEO issues

Respond in a helpful, professional tone as an SEO expert would."""
    
    async def _generate_suggestions(
        self, 
        query: str, 
        site_context: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Generate follow-up suggestions based on query and site context"""
        
        suggestions = []
        
        # Query-based suggestions
        query_lower = query.lower()
        if 'title' in query_lower:
            suggestions.append("Show me pages with missing titles")
            suggestions.append("How do I optimize title tags for SEO?")
        elif 'description' in query_lower:
            suggestions.append("Find pages with missing meta descriptions")
            suggestions.append("What's the ideal meta description length?")
        elif 'content' in query_lower:
            suggestions.append("Which pages have thin content?")
            suggestions.append("How can I improve content quality?")
        elif 'error' in query_lower or '404' in query_lower:
            suggestions.append("Show me all pages with errors")
            suggestions.append("How do I fix broken internal links?")
        
        # Site context-based suggestions
        if site_context:
            if site_context['missing_titles'] > 0:
                suggestions.append(f"Fix {site_context['missing_titles']} missing titles")
            if site_context['missing_descriptions'] > 0:
                suggestions.append(f"Add meta descriptions to {site_context['missing_descriptions']} pages")
            if site_context['error_pages'] > 0:
                suggestions.append(f"Investigate {site_context['error_pages']} error pages")
        
        # General SEO suggestions
        if len(suggestions) < 3:
            suggestions.extend([
                "Analyze my site's overall SEO health",
                "Find content optimization opportunities",
                "Check for technical SEO issues"
            ])
        
        return suggestions[:4]  # Return max 4 suggestions
    
    async def execute_seo_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        site_id: Optional[str],
        org: Organization,
        db_session: AsyncSession
    ) -> Dict[str, Any]:
        """Execute a specific SEO tool/function"""
        
        try:
            if tool_name == "site_search":
                return await self._tool_site_search(parameters, site_id, org.id, db_session)
            elif tool_name == "get_page":
                return await self._tool_get_page(parameters, org.id, db_session)
            elif tool_name == "char_count":
                return self._tool_char_count(parameters)
            elif tool_name == "word_count":
                return self._tool_word_count(parameters)
            elif tool_name == "schema_validate":
                return self._tool_schema_validate(parameters)
            elif tool_name == "compare_pages":
                return await self._tool_compare_pages(parameters, org.id, db_session)
            else:
                return {
                    "error": f"Unknown tool: {tool_name}",
                    "success": False
                }
                
        except Exception as e:
            logger.error(f"Tool execution failed for {tool_name}: {str(e)}")
            return {
                "error": str(e),
                "success": False
            }
    
    async def _tool_site_search(
        self, 
        parameters: Dict[str, Any], 
        site_id: Optional[str], 
        org_id: str, 
        db_session: AsyncSession
    ) -> Dict[str, Any]:
        """Search across all pages in a site using semantic search"""
        
        query = parameters.get('query', '')
        limit = min(parameters.get('limit', 10), 20)  # Max 20 results
        
        if not query:
            return {"error": "Query parameter required", "success": False}
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query)
        
        # Retrieve relevant pages
        context_chunks = await self._retrieve_relevant_context(
            query_embedding, site_id, org_id, db_session, top_k=limit
        )
        
        results = []
        for chunk in context_chunks:
            results.append({
                'url': chunk['page_url'],
                'title': chunk['page_title'],
                'excerpt': chunk['content'][:300] + "...",
                'relevance_score': chunk['similarity'],
                'word_count': chunk['word_count']
            })
        
        return {
            "results": results,
            "total": len(results),
            "query": query,
            "success": True
        }
    
    async def _tool_get_page(
        self, 
        parameters: Dict[str, Any], 
        org_id: str, 
        db_session: AsyncSession
    ) -> Dict[str, Any]:
        """Get detailed information about a specific page"""
        
        url = parameters.get('url', '')
        if not url:
            return {"error": "URL parameter required", "success": False}
        
        # Find page by URL
        result = await db_session.execute(
            select(Page, PageElement, Site)
            .outerjoin(PageElement, Page.id == PageElement.page_id)
            .join(Site, Page.site_id == Site.id)
            .where(
                Page.url == url,
                Site.org_id == org_id
            )
        )
        row = result.first()
        
        if not row:
            return {"error": "Page not found", "success": False}
        
        page, elements, site = row
        
        return {
            "url": page.url,
            "title": elements.title if elements else None,
            "description": elements.description if elements else None,
            "h1": elements.h1 if elements else None,
            "word_count": page.word_count,
            "status_code": page.status_code,
            "last_crawled": page.last_crawled_at.isoformat() if page.last_crawled_at else None,
            "site": site.domain,
            "success": True
        }
    
    def _tool_char_count(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Count characters in text"""
        
        text = parameters.get('text', '')
        return {
            "text": text[:100] + "..." if len(text) > 100 else text,
            "character_count": len(text),
            "success": True
        }
    
    def _tool_word_count(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Count words in text"""
        
        text = parameters.get('text', '')
        words = len(text.split())
        return {
            "text": text[:100] + "..." if len(text) > 100 else text,
            "word_count": words,
            "success": True
        }
    
    def _tool_schema_validate(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate JSON-LD schema markup"""
        
        schema_json = parameters.get('schema_json', {})
        
        try:
            # Basic validation
            if not isinstance(schema_json, dict):
                return {"error": "Schema must be a JSON object", "success": False}
            
            if '@type' not in schema_json:
                return {"error": "Schema missing @type property", "success": False}
            
            # Check for common required fields
            schema_type = schema_json.get('@type', '')
            issues = []
            
            if schema_type == 'Article':
                required = ['headline', 'author', 'datePublished']
                for field in required:
                    if field not in schema_json:
                        issues.append(f"Missing required field: {field}")
            
            return {
                "schema_type": schema_type,
                "valid": len(issues) == 0,
                "issues": issues,
                "success": True
            }
            
        except Exception as e:
            return {"error": f"Schema validation failed: {str(e)}", "success": False}
    
    async def _tool_compare_pages(
        self, 
        parameters: Dict[str, Any], 
        org_id: str, 
        db_session: AsyncSession
    ) -> Dict[str, Any]:
        """Compare two pages for SEO differences"""
        
        url_a = parameters.get('url_a', '')
        url_b = parameters.get('url_b', '')
        
        if not url_a or not url_b:
            return {"error": "Both url_a and url_b parameters required", "success": False}
        
        # Get both pages
        pages = {}
        for key, url in [('a', url_a), ('b', url_b)]:
            result = await db_session.execute(
                select(Page, PageElement, Site)
                .outerjoin(PageElement, Page.id == PageElement.page_id)
                .join(Site, Page.site_id == Site.id)
                .where(
                    Page.url == url,
                    Site.org_id == org_id
                )
            )
            row = result.first()
            
            if not row:
                return {"error": f"Page not found: {url}", "success": False}
            
            page, elements, site = row
            pages[key] = {
                'url': page.url,
                'title': elements.title if elements else None,
                'description': elements.description if elements else None,
                'h1': elements.h1 if elements else None,
                'word_count': page.word_count,
                'status_code': page.status_code
            }
        
        # Compare pages
        differences = []
        
        for field in ['title', 'description', 'h1', 'word_count']:
            val_a = pages['a'][field]
            val_b = pages['b'][field]
            
            if val_a != val_b:
                differences.append({
                    'field': field,
                    'page_a': val_a,
                    'page_b': val_b
                })
        
        return {
            "page_a": pages['a'],
            "page_b": pages['b'],
            "differences": differences,
            "success": True
        }


# Global service instance
rag_service = RAGService()
