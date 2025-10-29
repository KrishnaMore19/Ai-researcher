# app/services/llm_service.py
import asyncio
import logging
from typing import Optional, Dict, List
import httpx
import re
from app.core.config import settings
from app.utils.prompt_templates import get_prompt_template

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMService:
    """
    Production-ready async LLM service supporting multiple models, RAG, and advanced features.
    
    NEW FEATURES:
    - 🆕 Multiple summarization types (short, detailed, bullet, section)
    - 🆕 Dynamic model selection based on query type
    - 🆕 Query classification
    - 🆕 Document domain detection
    """

    def __init__(self):
        self.models = {
            "llama": {
                "name": settings.LLAMA_MODEL,
                "api_key": settings.LLAMA_API_KEY,
                "strengths": ["factual", "technical", "medical", "legal"]
            },
            "dolphin": {
                "name": settings.DOLPHIN_MODEL,
                "api_key": settings.DOLPHIN_API_KEY,
                "strengths": ["creative", "conversational", "general"]
            },
            "gemma": {
                "name": settings.GEMMA_MODEL,
                "api_key": settings.GEMMA_API_KEY,
                "strengths": ["analytical", "comparison", "summarization"]
            }
        }
        
        logger.info("LLM Service initialized with models:")
        for model_key, model_info in self.models.items():
            has_key = bool(model_info["api_key"] and len(model_info["api_key"]) > 10)
            logger.info(f"  {model_key}: {model_info['name']} (Key: {'✓' if has_key else '✗'})")

    def get_model(self, model_name: str) -> Dict[str, str]:
        if model_name not in self.models:
            raise ValueError(f"Unknown model: {model_name}")
        return self.models[model_name]

    # ==============================
    # 🆕 DYNAMIC MODEL SELECTION
    # ==============================

    async def select_best_model(
        self,
        query: str,
        document_content: str = "",
        document_domain: Optional[str] = None
    ) -> str:
        """
        Automatically select the best model based on:
        1. Query type (factual, creative, analytical)
        2. Document domain (medical, legal, technical, general)
        
        Returns: model name ("llama", "dolphin", or "gemma")
        """
        # Classify query type
        query_type = self._classify_query(query)
        
        # Detect document domain if not provided
        if not document_domain and document_content:
            document_domain = self._detect_domain(document_content)
        
        logger.info(f"Auto-selecting model: query_type={query_type}, domain={document_domain}")
        
        # Selection logic
        if query_type == "factual":
            if document_domain in ["medical", "legal", "technical"]:
                return "llama"  # Best for factual + specialized domains
            return "gemma"  # Good for general factual queries
        
        elif query_type == "creative":
            return "dolphin"  # Best for creative/conversational
        
        elif query_type == "analytical" or query_type == "comparison":
            return "gemma"  # Best for analysis and comparisons
        
        else:
            return "llama"  # Default fallback

    def _classify_query(self, query: str) -> str:
        """
        Classify query into types: factual, creative, analytical, comparison
        """
        query_lower = query.lower()
        
        # Comparison indicators
        if any(word in query_lower for word in ["compare", "difference", "vs", "versus", "contrast", "similar"]):
            return "comparison"
        
        # Analytical indicators
        if any(word in query_lower for word in ["analyze", "analyze", "explain why", "reasoning", "evaluate"]):
            return "analytical"
        
        # Creative indicators
        if any(word in query_lower for word in ["write", "create", "generate", "imagine", "story", "poem"]):
            return "creative"
        
        # Factual indicators (questions, definitions, summaries)
        if any(word in query_lower for word in ["what", "who", "when", "where", "define", "summarize", "list"]):
            return "factual"
        
        return "general"

    def _detect_domain(self, content: str) -> str:
        """
        Detect document domain based on content keywords
        """
        content_lower = content.lower()
        
        # Medical domain
        medical_keywords = ["patient", "treatment", "diagnosis", "clinical", "therapy", "medical", "disease", "symptom"]
        if sum(1 for kw in medical_keywords if kw in content_lower) >= 3:
            return "medical"
        
        # Legal domain
        legal_keywords = ["court", "law", "legal", "statute", "regulation", "contract", "plaintiff", "defendant"]
        if sum(1 for kw in legal_keywords if kw in content_lower) >= 3:
            return "legal"
        
        # Technical/Engineering domain
        technical_keywords = ["algorithm", "implementation", "system", "architecture", "performance", "optimization"]
        if sum(1 for kw in technical_keywords if kw in content_lower) >= 3:
            return "technical"
        
        # Scientific domain
        scientific_keywords = ["research", "experiment", "hypothesis", "methodology", "results", "conclusion"]
        if sum(1 for kw in scientific_keywords if kw in content_lower) >= 3:
            return "scientific"
        
        return "general"

    # ==============================
    # 🆕 ADVANCED SUMMARIZATION
    # ==============================

    async def generate_summary(
        self,
        content: str,
        summary_type: str = "short",  # short, detailed, bullet, section
        model_name: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate document summary with different styles
        
        Args:
            content: Document content to summarize
            summary_type: "short", "detailed", "bullet", "section"
            model_name: Optional model override (auto-selects if None)
            max_tokens: Optional token limit override
        
        Returns:
            Formatted summary string
        """
        # Auto-select model if not provided
        if not model_name:
            model_name = await self.select_best_model(
                query="summarize this document",
                document_content=content
            )
        
        logger.info(f"Generating {summary_type} summary with {model_name}")
        
        # Get appropriate prompt template
        prompt_templates = {
            "short": """Provide a concise 3-5 sentence summary of the key points:

{content}

Summary:""",
            
            "detailed": """Provide a comprehensive summary including:
1. Main objective/purpose
2. Methodology or approach
3. Key findings or arguments
4. Conclusions
5. Limitations (if any)

Document:
{content}

Detailed Summary:""",
            
            "bullet": """Summarize the following document as clear bullet points. Focus on:
- Main topics and themes
- Key findings or arguments
- Important data or statistics
- Conclusions or recommendations

Document:
{content}

Bullet Point Summary:""",
            
            "section": """Break down this document into sections with summaries:

# Introduction / Background
# Methods / Approach
# Key Findings / Results
# Discussion / Analysis
# Conclusions / Future Work

Document:
{content}

Section-wise Breakdown:"""
        }
        
        prompt = prompt_templates.get(summary_type, prompt_templates["short"]).format(content=content)
        
        # Set appropriate max_tokens based on summary type
        if not max_tokens:
            token_limits = {
                "short": 200,
                "detailed": 800,
                "bullet": 500,
                "section": 1000
            }
            max_tokens = token_limits.get(summary_type, 500)
        
        # Generate summary
        model = self.get_model(model_name)
        summary = await self._call_model_api(
            model_name=model["name"],
            api_key=model["api_key"],
            prompt=prompt,
            temperature=0.3,  # Lower temperature for more focused summaries
            max_tokens=max_tokens
        )
        
        return summary

    # ==============================
    # EXISTING METHODS (Enhanced)
    # ==============================

    async def generate_response(
        self,
        prompt_name: str,
        content: str,
        model_name: str = "llama",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        context: str = "",
        auto_select_model: bool = False  # 🆕 NEW parameter
    ) -> str:
        """
        Generate a response from the selected model using a prompt template.
        
        🆕 NEW: Set auto_select_model=True to automatically choose best model
        """
        try:
            # Auto-select model if requested
            if auto_select_model:
                original_model = model_name
                model_name = await self.select_best_model(content, context)
                logger.info(f"Auto-selected {model_name} (was {original_model})")
            
            model = self.get_model(model_name)
            prompt_template = get_prompt_template(prompt_name)
            prompt = prompt_template.format(content=content, query=content, context=context)

            temperature = temperature or settings.TEMPERATURE
            max_tokens = max_tokens or settings.MAX_TOKENS

            response = await self._call_model_api(
                model_name=model["name"],
                api_key=model["api_key"],
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response
        except Exception as e:
            logger.error(f"Failed to generate LLM response: {e}")
            return f"Error generating response: {str(e)}"

    async def _call_model_api(
        self,
        model_name: str,
        api_key: str,
        prompt: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """Call OpenRouter API to get real LLM response."""
        if not api_key or len(api_key) < 10:
            logger.error("Invalid API key: Key is missing or too short")
            return "Error: Invalid or missing API key. Please check your .env file."
        
        if not model_name:
            logger.error("Invalid model name: Model name is empty")
            return "Error: Invalid model name"
        
        logger.info(f"Calling OpenRouter API with model: {model_name}")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:8000",
                    "X-Title": "Research Assistant"
                }
                
                payload = {
                    "model": model_name,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
                
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    error_text = response.text
                    logger.error(f"OpenRouter API error {response.status_code}: {error_text}")
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("error", {}).get("message", error_text)
                        return f"API Error ({response.status_code}): {error_msg}"
                    except:
                        return f"API Error ({response.status_code}): {error_text[:200]}"
                    
        except httpx.TimeoutException as e:
            logger.error(f"OpenRouter API timeout: {e}")
            return "Error: API request timed out (60 seconds)."
        except httpx.RequestError as e:
            logger.error(f"OpenRouter API request failed: {e}")
            return f"Error: Connection failed. {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error calling LLM API: {e}", exc_info=True)
            return f"Error: {str(e)}"

    async def get_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text."""
        await asyncio.sleep(0.01)
        import random
        return [random.random() for _ in range(settings.EMBEDDING_DIM)]

    async def generate_rag_response(
        self,
        query: str,
        context_chunks: List[str],
        model_name: str = "llama",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """RAG pipeline: Use provided context chunks to generate LLM answer."""
        context = "\n\n".join(context_chunks)
        
        prompt_template = get_prompt_template("conversation")
        prompt = prompt_template.format(content=query, query=query, context=context)

        temperature = temperature or settings.TEMPERATURE
        max_tokens = max_tokens or settings.MAX_TOKENS

        answer = await self._call_model_api(
            model_name=self.get_model(model_name)["name"],
            api_key=self.get_model(model_name)["api_key"],
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return answer


# Singleton instance for app
llm_service = LLMService()