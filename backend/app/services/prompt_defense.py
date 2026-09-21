import re
import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class InjectionAttempt:
    detected: bool
    patterns_matched: List[str]
    risk_score: float
    sanitized_content: str


class PromptInjectionDefense:
    """
    Defends against prompt injection attacks by detecting and sanitizing
    malicious instructions in user-provided content.
    
    This maintains a strict trust boundary:
    SYSTEM INSTRUCTIONS > APPLICATION RULES > VERIFIED RETRIEVED INFORMATION > USER CONTENT
    """
    
    # Patterns that indicate potential prompt injection attempts
    INJECTION_PATTERNS = [
        # Direct instruction override attempts
        (r"(?i)ignore\s+(?:previous|prior|above|all)\s+instructions?", "instruction_override"),
        (r"(?i)forget\s+(?:previous|prior|above|all)\s+instructions?", "instruction_override"),
        (r"(?i)disregard\s+(?:previous|prior|above|all)\s+instructions?", "instruction_override"),
        (r"(?i)override\s+(?:system|previous|prior)\s+(?:instructions?|prompt)", "instruction_override"),
        (r"(?i)new\s+(?:system|master)\s+(?:instructions?|prompt)", "instruction_override"),
        
        # Role manipulation
        (r"(?i)act\s+as\s+(?:an?\s+)?(?:unrestricted|unfiltered|unlimited)\s+(?:lawyer|attorney|legal\s+expert)", "role_manipulation"),
        (r"(?i)you\s+are\s+(?:now\s+)?(?:an?\s+)?(?:unrestricted|unfiltered|unlimited)", "role_manipulation"),
        (r"(?i)pretend\s+(?:to\s+be|you\s+are)\s+(?:an?\s+)?(?:lawyer|attorney|judge)", "role_manipulation"),
        (r"(?i)roleplay\s+(?:as|an?)\s+(?:lawyer|attorney|legal)", "role_manipulation"),
        
        # Safety rule bypass
        (r"(?i)ignore\s+(?:safety|security|content)\s+(?:rules?|guidelines?|policies?)", "safety_bypass"),
        (r"(?i)bypass\s+(?:safety|security|content)\s+(?:rules?|guidelines?|policies?)", "safety_bypass"),
        (r"(?i)disable\s+(?:safety|security|content)\s+(?:rules?|guidelines?|policies?)", "safety_bypass"),
        (r"(?i)no\s+(?:safety|security|content)\s+(?:rules?|guidelines?|policies?)", "safety_bypass"),
        
        # System prompt extraction
        (r"(?i)(?:show|reveal|display|print|output)\s+(?:your\s+)?(?:system\s+)?(?:prompt|instructions?)", "prompt_extraction"),
        (r"(?i)what\s+(?:is|are)\s+(?:your\s+)?(?:system\s+)?(?:prompt|instructions?)", "prompt_extraction"),
        (r"(?i)repeat\s+(?:your\s+)?(?:system\s+)?(?:prompt|instructions?)", "prompt_extraction"),
        
        # Secret/API key extraction
        (r"(?i)(?:show|reveal|display|print|output)\s+(?:your\s+)?(?:api\s+)?(?:keys?|tokens?|secrets?|passwords?)", "secret_extraction"),
        (r"(?i)what\s+(?:is|are)\s+(?:your\s+)?(?:api\s+)?(?:keys?|tokens?|secrets?|passwords?)", "secret_extraction"),
        
        # Document as instruction
        (r"(?i)use\s+(?:this|the\s+(?:following|below))\s+(?:document|text|content)\s+as\s+(?:your\s+)?(?:system\s+)?(?:instruction|prompt)", "document_as_instruction"),
        (r"(?i)(?:this|the\s+(?:following|below))\s+(?:document|text|content)\s+is\s+(?:your\s+)?(?:new\s+)?(?:system\s+)?(?:instruction|prompt)", "document_as_instruction"),
        
        # Chain of thought extraction
        (r"(?i)show\s+(?:me\s+)?your\s+(?:reasoning|thinking|chain\s+of\s+thought)", "cot_extraction"),
        (r"(?i)explain\s+(?:your\s+)?(?:reasoning|thinking|thought\s+process)", "cot_extraction"),
        
        # Jailbreak patterns
        (r"(?i)DAN\s+(?:mode|prompt)", "jailbreak"),
        (r"(?i)developer\s+mode", "jailbreak"),
        (r"(?i)unrestricted\s+mode", "jailbreak"),
        (r"(?i)simulate\s+(?:an?\s+)?(?:unrestricted|unfiltered)", "jailbreak"),
        
        # Hypothetical framing to bypass rules
        (r"(?i)in\s+a\s+hypothetical\s+(?:scenario|situation|case)", "hypothetical_bypass"),
        (r"(?i)imagine\s+(?:you\s+are|a\s+world\s+where)", "hypothetical_bypass"),
        (r"(?i)for\s+(?:educational|research|academic)\s+purposes\s+only", "hypothetical_bypass"),
        
        # Encoding/obfuscation attempts
        (r"(?i)base64|rot13|encode|decode|obfuscat", "encoding_obfuscation"),
        
        # Multi-turn injection setup
        (r"(?i)from\s+now\s+on|going\s+forward|henceforth", "persistent_injection"),
    ]
    
    # High-risk patterns that should trigger immediate rejection
    CRITICAL_PATTERNS = [
        r"(?i)ignore\s+all\s+(?:previous|prior)\s+instructions",
        r"(?i)you\s+are\s+now\s+(?:unrestricted|unfiltered|unlimited)",
        r"(?i)act\s+as\s+(?:an?\s+)?(?:unrestricted|unfiltered)\s+(?:lawyer|attorney)",
        r"(?i)show\s+(?:me\s+)?your\s+system\s+prompt",
        r"(?i)reveal\s+(?:your\s+)?(?:api\s+)?keys?",
    ]
    
    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode
        self._compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), category) 
            for pattern, category in self.INJECTION_PATTERNS
        ]
        self._critical_patterns = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in self.CRITICAL_PATTERNS
        ]
    
    def scan(self, content: str) -> InjectionAttempt:
        """
        Scan content for prompt injection attempts.
        
        Args:
            content: The user-provided content to scan
            
        Returns:
            InjectionAttempt with detection results
        """
        if not content:
            return InjectionAttempt(
                detected=False,
                patterns_matched=[],
                risk_score=0.0,
                sanitized_content=content
            )
        
        patterns_matched = []
        critical_matches = []
        
        for pattern, category in self._compiled_patterns:
            if pattern.search(content):
                patterns_matched.append(category)
        
        for pattern in self._critical_patterns:
            if pattern.search(content):
                critical_matches.append(pattern.pattern)
        
        # Calculate risk score
        risk_score = min(len(patterns_matched) * 0.15 + len(critical_matches) * 0.5, 1.0)
        detected = len(patterns_matched) > 0
        
        # Sanitize content by removing/neutralizing matched patterns
        sanitized = self._sanitize(content, patterns_matched)
        
        if detected:
            logger.warning(
                f"Prompt injection detected | patterns={patterns_matched} "
                f"critical={len(critical_matches) > 0} risk_score={risk_score:.2f}"
            )
        
        return InjectionAttempt(
            detected=detected,
            patterns_matched=patterns_matched,
            risk_score=risk_score,
            sanitized_content=sanitized
        )
    
    def _sanitize(self, content: str, matched_categories: List[str]) -> str:
        """
        Sanitize content by neutralizing detected injection patterns.
        In strict mode, critical patterns cause the content to be heavily sanitized.
        """
        sanitized = content
        
        # Remove or neutralize critical patterns
        if "instruction_override" in matched_categories or "role_manipulation" in matched_categories:
            if self.strict_mode:
                # In strict mode, replace the entire content with a safe placeholder
                return "[Content removed due to detected prompt injection attempt]"
            else:
                # In lenient mode, remove specific phrases
                sanitized = re.sub(
                    r"(?i)ignore\s+(?:previous|prior|above|all)\s+instructions?",
                    "[instruction override removed]",
                    sanitized
                )
                sanitized = re.sub(
                    r"(?i)act\s+as\s+(?:an?\s+)?(?:unrestricted|unfiltered|unlimited)",
                    "[role manipulation removed]",
                    sanitized
                )
        
        if "safety_bypass" in matched_categories:
            sanitized = re.sub(
                r"(?i)(?:ignore|bypass|disable)\s+(?:safety|security|content)\s+(?:rules?|guidelines?|policies?)",
                "[safety bypass attempt removed]",
                sanitized
            )
        
        if "prompt_extraction" in matched_categories or "secret_extraction" in matched_categories:
            if self.strict_mode:
                return "[Content removed due to sensitive information request]"
        
        if "document_as_instruction" in matched_categories:
            sanitized = re.sub(
                r"(?i)use\s+(?:this|the\s+(?:following|below))\s+(?:document|text|content)\s+as\s+(?:your\s+)?(?:system\s+)?(?:instruction|prompt)",
                "[document-as-instruction attempt removed]",
                sanitized
            )
        
        return sanitized
    
    def validate_system_prompt_integrity(self, system_prompt: str, user_content: str) -> bool:
        """
        Verify that user content doesn't contain instructions that could override
        the system prompt. This is a secondary defense layer.
        """
        # Check if user content tries to reference or modify system prompt concepts
        dangerous_phrases = [
            "system prompt",
            "system instruction",
            "master prompt",
            "your instructions",
            "your rules",
            "your guidelines",
        ]
        
        user_lower = user_content.lower()
        for phrase in dangerous_phrases:
            if phrase in user_lower:
                # Check if it's in a suspicious context (not just mentioning it)
                context_patterns = [
                    rf"(?i){re.escape(phrase)}\s+(?:is|are|should|must|will)\s+",
                    rf"(?i)(?:change|modify|override|ignore|forget)\s+{re.escape(phrase)}",
                ]
                for pattern in context_patterns:
                    if re.search(pattern, user_content):
                        return False
        
        return True


def create_prompt_defense(strict_mode: bool = True) -> PromptInjectionDefense:
    """Factory function for creating prompt injection defense"""
    return PromptInjectionDefense(strict_mode=strict_mode)


def sanitize_user_input(content: str, strict: bool = True) -> Tuple[str, InjectionAttempt]:
    """
    Convenience function to scan and sanitize user input.
    
    Returns:
        Tuple of (sanitized_content, injection_attempt)
    """
    defense = create_prompt_defense(strict_mode=strict)
    attempt = defense.scan(content)
    return attempt.sanitized_content, attempt