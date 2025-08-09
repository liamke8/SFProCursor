"""
LLM service for executing prompt templates
"""
import json
import logging
import os
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime

import openai
from anthropic import AsyncAnthropic
import litellm
from jsonschema import validate, ValidationError

from database.models import (
    PromptTemplate, PromptRun, RowGeneration, Page, PageElement,
    PromptRunStatus
)
from services.prompt_templates import get_template_by_id

logger = logging.getLogger(__name__)

class LLMService:
    """Service for executing LLM prompts with various providers"""
    
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        
        # Initialize clients if API keys are available
        if os.getenv("OPENAI_API_KEY"):
            openai.api_key = os.getenv("OPENAI_API_KEY")
            self.openai_client = openai
            
        if os.getenv("ANTHROPIC_API_KEY"):
            self.anthropic_client = AsyncAnthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )
    
    async def execute_prompt_run(
        self, 
        run_id: str, 
        template_id: str, 
        page_ids: List[str],
        context_columns: List[str],
        variants: int = 1,
        db_session = None
    ):
        """Execute a prompt run on multiple pages"""
        
        try:
            # Get the prompt run and template
            prompt_run = await db_session.get(PromptRun, run_id)
            if not prompt_run:
                raise ValueError(f"Prompt run {run_id} not found")
            
            # Update status to running
            prompt_run.status = PromptRunStatus.RUNNING
            await db_session.commit()
            
            # Get template (builtin or custom)
            template = await self._get_template(template_id, db_session)
            if not template:
                raise ValueError(f"Template {template_id} not found")
            
            # Process pages in batches to avoid overwhelming the API
            batch_size = 5
            completed_count = 0
            failed_count = 0
            
            for i in range(0, len(page_ids), batch_size):
                batch_page_ids = page_ids[i:i + batch_size]
                
                # Process batch concurrently
                tasks = []
                for page_id in batch_page_ids:
                    for variant in range(1, variants + 1):
                        task = self._process_single_page(
                            run_id, template, page_id, variant, 
                            context_columns, db_session
                        )
                        tasks.append(task)
                
                # Execute batch
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Count results
                for result in results:
                    if isinstance(result, Exception):
                        failed_count += 1
                        logger.error(f"Failed to process page: {result}")
                    else:
                        completed_count += 1
                
                # Update progress
                prompt_run.completed_rows = completed_count
                prompt_run.failed_rows = failed_count
                await db_session.commit()
                
                # Small delay between batches
                await asyncio.sleep(1)
            
            # Update final status
            if failed_count == 0:
                prompt_run.status = PromptRunStatus.COMPLETED
            else:
                prompt_run.status = PromptRunStatus.FAILED if completed_count == 0 else PromptRunStatus.COMPLETED
            
            prompt_run.completed_at = datetime.utcnow()
            await db_session.commit()
            
            logger.info(f"Prompt run {run_id} completed: {completed_count} success, {failed_count} failed")
            
        except Exception as e:
            logger.error(f"Prompt run {run_id} failed: {str(e)}")
            
            # Update status to failed
            if prompt_run:
                prompt_run.status = PromptRunStatus.FAILED
                prompt_run.completed_at = datetime.utcnow()
                await db_session.commit()
            
            raise e
    
    async def _process_single_page(
        self,
        run_id: str,
        template: PromptTemplate,
        page_id: str,
        variant: int,
        context_columns: List[str],
        db_session
    ) -> Dict[str, Any]:
        """Process a single page with a template"""
        
        try:
            # Get page data with elements
            page = await db_session.get(Page, page_id)
            if not page:
                raise ValueError(f"Page {page_id} not found")
            
            # Get page elements
            elements = await db_session.get(PageElement, page_id)
            
            # Build context from requested columns
            context = await self._build_page_context(page, elements, context_columns)
            
            # Prepare prompt with variables
            filled_prompt = await self._fill_prompt_variables(template, context)
            
            # Execute LLM call
            response = await self._call_llm(
                template.model,
                template.system_prompt,
                filled_prompt,
                template.output_schema
            )
            
            # Validate output against schema
            if template.output_schema:
                try:
                    validate(instance=response, schema=template.output_schema)
                except ValidationError as e:
                    logger.warning(f"Output validation failed for page {page_id}: {e}")
                    response["validation_error"] = str(e)
            
            # Create generation record
            generation = RowGeneration(
                prompt_run_id=run_id,
                page_id=page_id,
                input_context_json=context,
                output_json=response,
                tokens_in=self._estimate_tokens(filled_prompt),
                tokens_out=self._estimate_tokens(json.dumps(response)),
                variant=variant,
                model_used=template.model
            )
            
            db_session.add(generation)
            await db_session.commit()
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to process page {page_id} variant {variant}: {str(e)}")
            
            # Still save the generation with error info
            generation = RowGeneration(
                prompt_run_id=run_id,
                page_id=page_id,
                input_context_json=context if 'context' in locals() else {},
                output_json={"error": str(e), "success": False},
                tokens_in=0,
                tokens_out=0,
                variant=variant,
                model_used=template.model
            )
            
            db_session.add(generation)
            await db_session.commit()
            
            raise e
    
    async def _get_template(self, template_id: str, db_session) -> Optional[PromptTemplate]:
        """Get template from database or builtin templates"""
        
        # First try database
        template = await db_session.get(PromptTemplate, template_id)
        if template:
            return template
        
        # Try builtin templates
        builtin_template = get_template_by_id(template_id)
        if builtin_template:
            # Convert to PromptTemplate object
            return PromptTemplate(
                id=template_id,
                name=builtin_template["name"],
                description=builtin_template["description"],
                system_prompt=builtin_template["system_prompt"],
                user_prompt=builtin_template["user_prompt"],
                output_schema=builtin_template["output_schema"],
                model=builtin_template["model"],
                vars_json=builtin_template["vars_json"],
                is_builtin=True
            )
        
        return None
    
    async def _build_page_context(
        self, 
        page: Page, 
        elements: Optional[PageElement], 
        context_columns: List[str]
    ) -> Dict[str, Any]:
        """Build context dictionary from page data"""
        
        context = {
            "url": page.url,
            "word_count": page.word_count,
            "status_code": page.status_code,
            "canonical": page.canonical,
            "meta_robots": page.meta_robots,
        }
        
        if elements:
            context.update({
                "title": elements.title,
                "description": elements.description,
                "h1": elements.h1,
                "h2_tags": elements.h2_json or [],
                "og_json": elements.og_json or {},
                "schema_json": elements.schema_json or [],
                "links_json": elements.links_json or [],
                "images_json": elements.images_json or [],
            })
        
        # Add content excerpts
        if page.content_md:
            context["content_excerpt"] = page.content_md[:3000]  # First 3k chars
            context["content_md"] = page.content_md
        
        if page.content_html:
            context["content_html"] = page.content_html
        
        # Add computed fields
        context.update({
            "title_length": len(context.get("title", "") or ""),
            "description_length": len(context.get("description", "") or ""),
            "missing_title": not bool(context.get("title", "").strip()),
            "missing_description": not bool(context.get("description", "").strip()),
            "missing_h1": not bool(context.get("h1", "").strip()),
        })
        
        # Filter to requested columns if specified
        if context_columns:
            filtered_context = {}
            for column in context_columns:
                if column in context:
                    filtered_context[column] = context[column]
            return filtered_context
        
        return context
    
    async def _fill_prompt_variables(
        self, 
        template: PromptTemplate, 
        context: Dict[str, Any]
    ) -> str:
        """Fill prompt template with context variables"""
        
        prompt = template.user_prompt
        
        # Replace variables with context values
        for var_name, var_description in (template.vars_json or {}).items():
            placeholder = f"{{{var_name}}}"
            value = context.get(var_name, "")
            
            # Convert to string and handle None values
            if value is None:
                value = ""
            elif isinstance(value, (list, dict)):
                value = json.dumps(value, indent=2)
            else:
                value = str(value)
            
            prompt = prompt.replace(placeholder, value)
        
        return prompt
    
    async def _call_llm(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        output_schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Call LLM with the specified model and prompts"""
        
        try:
            # Prepare messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Use litellm for unified interface across providers
            response = await litellm.acompletion(
                model=model,
                messages=messages,
                temperature=0.3,  # Slightly creative but mostly deterministic
                max_tokens=2000,
                timeout=60,
                # Force JSON output for structured data
                response_format={"type": "json_object"} if output_schema else None
            )
            
            content = response.choices[0].message.content
            
            # Try to parse as JSON if we expect structured output
            if output_schema:
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    # Fallback if JSON parsing fails
                    return {
                        "content": content,
                        "error": "Failed to parse JSON response",
                        "success": False
                    }
            else:
                return {"content": content, "success": True}
                
        except Exception as e:
            logger.error(f"LLM call failed: {str(e)}")
            return {
                "error": str(e),
                "success": False
            }
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough estimate of token count (1 token ≈ 4 characters)"""
        return len(text) // 4


# Global service instance
llm_service = LLMService()
