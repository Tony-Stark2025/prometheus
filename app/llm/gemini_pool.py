"""
Gemini Multi-Model Quota Pool & Rate-Limit Cascade Engine.
Maximizes free-tier throughput by cascading across Gemini 3.x Flash and Flash-Lite models,
rotating API keys, and semantically caching telemetry payloads.
"""

import hashlib
import json
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from app.config import settings

logger = logging.getLogger(__name__)


class TelemetryCache:
    """In-memory SHA-256 telemetry delta cache with configurable TTL."""

    def __init__(self, ttl_seconds: int = 900):
        self._ttl = ttl_seconds
        self._cache: Dict[str, Tuple[float, Any]] = {}

    def get(self, key_payload: str) -> Optional[Any]:
        hashed = hashlib.sha256(key_payload.encode("utf-8")).hexdigest()
        if hashed in self._cache:
            timestamp, data = self._cache[hashed]
            if time.time() - timestamp < self._ttl:
                logger.info(f"⚡ [TelemetryCache] Cache HIT for key {hashed[:8]} (saved 1 LLM call)")
                return data
            else:
                del self._cache[hashed]
        return None

    def set(self, key_payload: str, data: Any) -> None:
        hashed = hashlib.sha256(key_payload.encode("utf-8")).hexdigest()
        self._cache[hashed] = (time.time(), data)


class GeminiPoolClient:
    """
    Manages API keyrings and a multi-model fallback cascade across the Gemini 3.x series:
    gemini-3.7-flash -> gemini-3.6-flash -> gemini-3.5-flash -> gemini-3.5-flash-lite -> gemini-3.1-flash-lite
    """

    def __init__(self):
        self.cache = TelemetryCache(ttl_seconds=settings.cache_ttl_seconds)
        self._key_index = 0

    def _get_next_api_key(self) -> Optional[str]:
        keys = settings.get_all_api_keys()
        if not keys:
            return None
        key = keys[self._key_index % len(keys)]
        self._key_index += 1
        return key

    async def generate_structured_synthesis(
        self,
        prompt: str,
        cache_key: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Executes structured generation using the Gemini model cascade.
        Automatically retries across model tiers upon rate-limiting (429).
        """
        # 1. Check Telemetry Cache
        if cache_key:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        keys = settings.get_all_api_keys()
        if not keys:
            logger.info("No GEMINI_API_KEY found; proceeding with deterministic heuristic engine.")
            return None

        # 2. Iterate through Model Cascade Tiers
        models_to_try = list(settings.gemini_model_cascade)
        last_error = None

        for model_name in models_to_try:
            api_key = self._get_next_api_key()
            try:
                logger.info(f"🤖 [GeminiPool] Invocating model tier '{model_name}'...")
                
                # Import Google GenAI SDK
                from google import genai
                from google.genai import types

                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.2,
                    ),
                )

                if response.text:
                    parsed = json.loads(response.text)
                    logger.info(f"✓ [GeminiPool] Success from model tier '{model_name}'.")
                    if cache_key:
                        self.cache.set(cache_key, parsed)
                    return parsed

            except Exception as e:
                error_msg = str(e)
                last_error = e
                # Check for rate-limiting (429 or ResourceExhausted)
                if "429" in error_msg or "ResourceExhausted" in error_msg or "quota" in error_msg.lower():
                    logger.warning(
                        f"⚠️ [GeminiPool] Rate limit (429) hit on '{model_name}'. "
                        f"Cascading to next model tier..."
                    )
                    continue
                else:
                    logger.warning(f"⚠️ [GeminiPool] Model '{model_name}' encountered error: {e}. Cascading...")
                    continue

        logger.error(f"❌ [GeminiPool] All model tiers exhausted. Falling back to heuristic reasoning. Last error: {last_error}")
        return None


# Global singleton instance
gemini_pool = GeminiPoolClient()
