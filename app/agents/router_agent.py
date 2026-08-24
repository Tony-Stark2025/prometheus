"""
Router & Guardrail Agent for Prometheus.
Enforces organizational perimeter security, token scope checking, and inline prompt defense.
"""

from typing import Dict, Any, Optional
from app.security.abac_guard import ABACGuard, UserContext
from app.security.guardrails import GuardrailService, GuardrailResult


class RouterAgent:
    """
    Sub-agent 1: Router & Guardrail Agent
    First line of defense for user queries, scheduled cron jobs, and webhooks.
    """

    name: str = "RouterAndGuardrailAgent"
    role: str = "Perimeter Security & ABAC Routing"

    @classmethod
    async def process_request(
        cls,
        user: UserContext,
        raw_query: str,
    ) -> Dict[str, Any]:
        """
        Validates user context, filters prompt injection, sanitizes PII, and returns authorization envelope.
        """
        # 1. Guardrail / Prompt Defense
        guardrail_result: GuardrailResult = GuardrailService.sanitize(raw_query)
        if not guardrail_result.is_safe:
            return {
                "status": "rejected",
                "reason": "Security guardrail violation",
                "violations": guardrail_result.violations,
                "sanitized_query": guardrail_result.sanitized_text,
            }

        # 2. ABAC & Authentication Check
        if not user.is_authenticated:
            return {
                "status": "unauthorized",
                "reason": "User is not authenticated",
                "violations": ["Authentication required"],
            }

        return {
            "status": "authorized",
            "user_id": user.user_id,
            "username": user.username,
            "org_scopes": list(user.org_scopes),
            "sanitized_query": guardrail_result.sanitized_text,
            "pii_redacted_count": guardrail_result.pii_redacted_count,
        }
