"""
Vertex AI & Gemini Enterprise Agent Platform LLM Engine.
Unified exclusively on Gemini 3.7 Flash for all agents with non-blocking async execution (client.aio),
timeout protection, and SHA-256 telemetry delta caching. Zero model cascading.
"""

import asyncio
import hashlib
import json
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from prometheus.config import settings

logger = logging.getLogger(__name__)


class TelemetryCache:
    """In-memory SHA-256 telemetry delta cache with configurable TTL."""

    def __init__(self, ttl_seconds: int = 900):
        self._ttl = ttl_seconds
        self._cache: Dict[str, Tuple[float, Any]] = {}

    @classmethod
    def _hash_key(cls, prompt: str, payload: Any) -> str:
        content = prompt + str(payload)
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def get(self, key_payload: str) -> Optional[Any]:
        hashed = hashlib.sha256(key_payload.encode("utf-8")).hexdigest()
        for k in (key_payload, hashed):
            if k in self._cache:
                timestamp, data = self._cache[k]
                if time.time() - timestamp < self._ttl:
                    logger.info(f"⚡ [TelemetryCache] Cache HIT for key {k[:8]} (saved 1 LLM call)")
                    return data
                else:
                    del self._cache[k]
        return None

    def set(self, key_payload: str, data: Any) -> None:
        hashed = hashlib.sha256(key_payload.encode("utf-8")).hexdigest()
        self._cache[key_payload] = (time.time(), data)
        self._cache[hashed] = (time.time(), data)


class GeminiEnterpriseEngine:
    """
    Enterprise Vertex AI LLM Engine for Prometheus.
    Standardized exclusively on Gemini 3.7 Flash without multi-model cascades.
    """

    def __init__(self):
        self.cache = TelemetryCache(ttl_seconds=settings.cache_ttl_seconds)

    def _get_vertex_client(self) -> Optional[Any]:
        """Initializes the unified Google GenAI client targeting Vertex AI / Agent Platform."""
        try:
            from google import genai
            client_kwargs: Dict[str, Any] = {
                "vertexai": True,
                "location": settings.gcp_location,
            }
            if settings.gcp_project_id:
                client_kwargs["project"] = settings.gcp_project_id
            return genai.Client(**client_kwargs)
        except Exception as e:
            logger.info(f"ℹ️ [VertexAI] Google Cloud credentials not active locally ({e}). Using deterministic reasoning engine.")
            return None

    async def generate_structured_synthesis(
        self,
        prompt: str,
        cache_key: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Executes structured JSON reasoning using Gemini 3.7 Flash on Vertex AI.
        Uses non-blocking asyncio with timeout guards.
        """
        # 1. Check Telemetry Cache
        if cache_key:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        client = self._get_vertex_client()
        if not client:
            return None

        # 2. Execute Gemini 3.7 Flash
        model_name = settings.gemini_model
        from google.genai import types

        try:
            logger.info(f"🤖 [VertexAI/AgentPlatform] Invoking '{model_name}' via client.aio...")
            
            async def _call_model():
                return await client.aio.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.2,
                    ),
                )

            response = await asyncio.wait_for(
                _call_model(),
                timeout=settings.gemini_request_timeout_seconds,
            )

            if response and response.text:
                parsed = json.loads(response.text)
                logger.info(f"✓ [VertexAI/AgentPlatform] Synthesis completed with '{model_name}'.")
                if cache_key:
                    self.cache.set(cache_key, parsed)
                return parsed

        except asyncio.TimeoutError:
            logger.warning(f"⚠️ [VertexAI/AgentPlatform] Request timed out ({settings.gemini_request_timeout_seconds}s) on '{model_name}'.")
        except Exception as e:
            logger.warning(f"⚠️ [VertexAI/AgentPlatform] Error with '{model_name}': {e}.")

        logger.info("⚡ [VertexAI/AgentPlatform] Falling back to deterministic heuristic correlation engine.")
        return None


# Global singleton instances and backward compatibility aliases
GeminiPoolClient = GeminiEnterpriseEngine
gemini_engine = GeminiEnterpriseEngine()
gemini_pool = gemini_engine
