"""
Inline prompt defense and PII sanitization guardrails.
Protects LLM context boundaries and sanitizes sensitive credentials before multi-agent reasoning.
"""

import re
from typing import Tuple, List
from pydantic import BaseModel, Field


class GuardrailResult(BaseModel):
    is_safe: bool = True
    sanitized_text: str
    violations: List[str] = Field(default_factory=list)
    pii_redacted_count: int = 0


class GuardrailService:
    """
    Perimeter inspection service for input sanitization and prompt injection defense.
    """

    # Common injection & jailbreak patterns
    INJECTION_PATTERNS = [
        re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
        re.compile(r"disregard\s+the\s+above", re.IGNORECASE),
        re.compile(r"you\s+are\s+now\s+in\s+developer\s+mode", re.IGNORECASE),
        re.compile(r"system\s*prompt\s*override", re.IGNORECASE),
        re.compile(r"show\s+me\s+your\s+(initial|system)\s+prompt", re.IGNORECASE),
        re.compile(r"<script.*?>.*?</script>", re.IGNORECASE | re.DOTALL),
    ]

    # Sensitive PII and credential patterns for masking
    PII_PATTERNS = [
        # API Keys & Secrets
        (re.compile(r"(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{82})"), "[REDACTED_GITHUB_TOKEN]"),
        (re.compile(r"(AIza[0-9A-Za-z-_]{35})"), "[REDACTED_GEMINI_KEY]"),
        (re.compile(r"(xox[baprs]-[0-9a-zA-Z]{10,48})"), "[REDACTED_SLACK_TOKEN]"),
        (re.compile(r"bearer\s+[a-zA-Z0-9_\-\.]{20,}", re.IGNORECASE), "Bearer [REDACTED_TOKEN]"),
        # Email Addresses
        (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"), "[REDACTED_EMAIL]"),
        # Phone numbers
        (re.compile(r"\b(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"), "[REDACTED_PHONE]"),
    ]

    @classmethod
    def sanitize(cls, text: str) -> GuardrailResult:
        """
        Scans input for prompt injections and redacts sensitive PII / secrets.
        """
        violations: List[str] = []
        is_safe = True

        # 1. Prompt Injection Detection
        for pattern in cls.INJECTION_PATTERNS:
            if pattern.search(text):
                violations.append(f"Prompt injection detected: pattern '{pattern.pattern}'")
                is_safe = False

        # 2. PII & Secret Redaction
        sanitized = text
        redacted_count = 0
        for pattern, replacement in cls.PII_PATTERNS:
            matches = pattern.findall(sanitized)
            if matches:
                redacted_count += len(matches)
                sanitized = pattern.sub(replacement, sanitized)

        return GuardrailResult(
            is_safe=is_safe,
            sanitized_text=sanitized,
            violations=violations,
            pii_redacted_count=redacted_count,
        )
