import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from app.models.schemas import RiskLevel, LegalCategory, Jurisdiction

logger = logging.getLogger(__name__)


class SafetyCheckType(Enum):
    PROMPT_INJECTION = "prompt_injection"
    FABRICATED_CITATION = "fabricated_citation"
    DEFINITIVE_LEGAL_ADVICE = "definitive_legal_advice"
    MISSING_DISCLAIMER = "missing_disclaimer"
    MISSING_ESCALATION = "missing_escalation"
    MISSING_UNCERTAINTY = "missing_uncertainty"
    INAPPROPRIATE_RISK_GUIDANCE = "inappropriate_risk_guidance"
    UNAUTHORIZED_PRACTICE = "unauthorized_practice"


class SafetyAction(Enum):
    ALLOW = "allow"
    WARN = "warn"
    MODIFY = "modify"
    BLOCK = "block"
    FALLBACK = "fallback"


@dataclass
class SafetyCheckResult:
    check_type: SafetyCheckType
    passed: bool
    action: SafetyAction
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    
    def __init__(self, check_type: SafetyCheckType, passed: bool, action: SafetyAction, 
                 message: str, details: Optional[Dict[str, Any]] = None):
        self.check_type = check_type
        self.passed = passed
        self.action = action
        self.message = message
        self.details = details or {}


@dataclass
class SafetyAssessment:
    overall_passed: bool
    overall_action: SafetyAction
    checks: List[SafetyCheckResult]
    fallback_response: Optional[str] = None
    
    def __init__(self, checks: List[SafetyCheckResult]):
        self.checks = checks
        self.overall_passed = all(c.passed for c in checks)
        self.overall_action = self._determine_overall_action(checks)
    
    def _determine_overall_action(self, checks: List[SafetyCheckResult]) -> SafetyAction:
        actions = [c.action for c in checks]
        
        if SafetyAction.BLOCK in actions:
            return SafetyAction.BLOCK
        if SafetyAction.FALLBACK in actions:
            return SafetyAction.FALLBACK
        if SafetyAction.MODIFY in actions:
            return SafetyAction.MODIFY
        if SafetyAction.WARN in actions:
            return SafetyAction.WARN
        return SafetyAction.ALLOW


class SafetyLayer:
    """
    Safety layer that performs comprehensive checks on AI responses.
    
    This is the final gate before returning a response to the user.
    """
    
    # Patterns for definitive legal advice (should not be present)
    DEFINITIVE_PATTERNS = [
        (r"(?i)you\s+(?:will|shall)\s+win", "guaranteed_outcome"),
        (r"(?i)you\s+cannot\s+lose", "guaranteed_outcome"),
        (r"(?i)guaranteed\s+(?:win|victory|success)", "guaranteed_outcome"),
        (r"(?i)definitely\s+(?:have|are|will)", "definitive_statement"),
        (r"(?i)certainly\s+(?:have|are|will)", "definitive_statement"),
        (r"(?i)the\s+court\s+will\s+(?:rule|decide|grant)", "predictive_court"),
        (r"(?i)you\s+have\s+the\s+right\s+to\s+(?:win|recover|collect)", "definitive_right"),
        (r"(?i)you\s+are\s+entitled\s+to\s+(?:win|recover)", "definitive_entitlement"),
        (r"(?i)this\s+(?:guarantees|ensures)\s+", "guaranteed_outcome"),
    ]
    
    # Patterns that might indicate unauthorized practice of law
    UPL_PATTERNS = [
        (r"(?i)I\s+(?:represent|act\s+as)\s+your\s+(?:lawyer|attorney|counsel)", "impersonation"),
        (r"(?i)my\s+legal\s+advice\s+(?:is|to)", "giving_advice"),
        (r"(?i)you\s+should\s+(?:file|sue|appeal)\s+(?:immediately|now)", "specific_action"),
        (r"(?i)the\s+(?:best|correct|right)\s+legal\s+(?:strategy|approach)", "specific_strategy"),
    ]
    
    def __init__(self):
        self._definitive_patterns = [
            (re.compile(pattern, re.IGNORECASE), category) 
            for pattern, category in self.DEFINITIVE_PATTERNS
        ]
        self._upl_patterns = [
            (re.compile(pattern, re.IGNORECASE), category) 
            for pattern, category in self.UPL_PATTERNS
        ]
    
    def assess(self, response_content: str, context: Dict[str, Any]) -> SafetyAssessment:
        """
        Perform comprehensive safety assessment.
        
        Args:
            response_content: The AI response content to check
            context: Context including risk_level, jurisdiction, etc.
            
        Returns:
            SafetyAssessment with results of all checks
        """
        checks = []
        
        risk_level = context.get("risk_level", "LOW")
        jurisdiction = context.get("jurisdiction")
        has_disclaimer = context.get("has_disclaimer", False)
        has_escalation = context.get("has_escalation", False)
        has_uncertainty = context.get("has_uncertainty", False)
        provided_sources = context.get("sources", [])
        
        # 1. Check for definitive legal advice
        checks.append(self._check_definitive_advice(response_content, risk_level))
        
        # 2. Check for unauthorized practice of law
        checks.append(self._check_unauthorized_practice(response_content))
        
        # 3. Check disclaimer presence
        checks.append(self._check_disclaimer(response_content, has_disclaimer, risk_level))
        
        # 4. Check escalation for high risk
        checks.append(self._check_escalation(response_content, has_escalation, risk_level))
        
        # 5. Check uncertainty notes for high risk
        checks.append(self._check_uncertainty(response_content, has_uncertainty, risk_level))
        
        # 6. Check for fabricated citations
        checks.append(self._check_fabricated_citations(response_content, provided_sources))
        
        # 7. Check risk-appropriate guidance
        checks.append(self._check_risk_guidance(response_content, risk_level))
        
        # 8. Check for prompt injection in response (shouldn't happen but defense in depth)
        checks.append(self._check_prompt_injection_in_response(response_content))
        
        return SafetyAssessment(checks)
    
    def _check_definitive_advice(self, content: str, risk_level: str) -> SafetyCheckResult:
        """Check for definitive legal advice that should not be given"""
        matched = []
        for pattern, category in self._definitive_patterns:
            if pattern.search(content):
                matched.append(category)
        
        if matched:
            action = SafetyAction.FALLBACK if risk_level in ("HIGH", "CRITICAL") else SafetyAction.MODIFY
            return SafetyCheckResult(
                check_type=SafetyCheckType.DEFINITIVE_LEGAL_ADVICE,
                passed=False,
                action=action,
                message=f"Definitive legal advice detected: {', '.join(matched)}",
                details={"matched_categories": matched, "risk_level": risk_level}
            )
        
        return SafetyCheckResult(
            check_type=SafetyCheckType.DEFINITIVE_LEGAL_ADVICE,
            passed=True,
            action=SafetyAction.ALLOW,
            message="No definitive legal advice detected",
        )
    
    def _check_unauthorized_practice(self, content: str) -> SafetyCheckResult:
        """Check for unauthorized practice of law indicators"""
        matched = []
        for pattern, category in self._upl_patterns:
            if pattern.search(content):
                matched.append(category)
        
        if matched:
            return SafetyCheckResult(
                check_type=SafetyCheckType.UNAUTHORIZED_PRACTICE,
                passed=False,
                action=SafetyAction.MODIFY,
                message=f"Potential unauthorized practice indicators: {', '.join(matched)}",
                details={"matched_categories": matched}
            )
        
        return SafetyCheckResult(
            check_type=SafetyCheckType.UNAUTHORIZED_PRACTICE,
            passed=True,
            action=SafetyAction.ALLOW,
            message="No UPL indicators detected",
        )
    
    def _check_disclaimer(self, content: str, has_disclaimer: bool, risk_level: str) -> SafetyCheckResult:
        """Check for required disclaimer"""
        if not has_disclaimer:
            action = SafetyAction.FALLBACK if risk_level in ("HIGH", "CRITICAL") else SafetyAction.MODIFY
            return SafetyCheckResult(
                check_type=SafetyCheckType.MISSING_DISCLAIMER,
                passed=False,
                action=action,
                message="Required legal disclaimer is missing",
                details={"risk_level": risk_level}
            )
        
        # Check if disclaimer is in the content
        disclaimer_keywords = ["legal advice", "attorney", "lawyer", "qualified"]
        content_lower = content.lower()
        found = any(kw in content_lower for kw in disclaimer_keywords)
        
        if not found:
            return SafetyCheckResult(
                check_type=SafetyCheckType.MISSING_DISCLAIMER,
                passed=False,
                action=SafetyAction.MODIFY,
                message="Disclaimer keywords not found in response",
                details={"risk_level": risk_level}
            )
        
        return SafetyCheckResult(
            check_type=SafetyCheckType.MISSING_DISCLAIMER,
            passed=True,
            action=SafetyAction.ALLOW,
            message="Disclaimer present",
        )
    
    def _check_escalation(self, content: str, has_escalation: bool, risk_level: str) -> SafetyCheckResult:
        """Check for required escalation guidance for high-risk matters"""
        if risk_level in ("HIGH", "CRITICAL") and not has_escalation:
            return SafetyCheckResult(
                check_type=SafetyCheckType.MISSING_ESCALATION,
                passed=False,
                action=SafetyAction.FALLBACK,
                message=f"High-risk ({risk_level}) matter requires escalation guidance",
                details={"risk_level": risk_level}
            )
        
        return SafetyCheckResult(
            check_type=SafetyCheckType.MISSING_ESCALATION,
            passed=True,
            action=SafetyAction.ALLOW,
            message="Escalation check passed",
        )
    
    def _check_uncertainty(self, content: str, has_uncertainty: bool, risk_level: str) -> SafetyCheckResult:
        """Check for uncertainty communication"""
        if risk_level in ("HIGH", "CRITICAL") and not has_uncertainty:
            return SafetyCheckResult(
                check_type=SafetyCheckType.MISSING_UNCERTAINTY,
                passed=False,
                action=SafetyAction.FALLBACK,
                message=f"High-risk ({risk_level}) matter requires uncertainty communication",
                details={"risk_level": risk_level}
            )
        
        # Check if response communicates uncertainty appropriately
        uncertainty_phrases = [
            "may", "might", "could", "possibly", "potentially",
            "generally", "typically", "often", "usually",
            "uncertain", "unclear", "depends", "varies"
        ]
        
        content_lower = content.lower()
        has_uncertainty_language = any(phrase in content_lower for phrase in uncertainty_phrases)
        
        if risk_level in ("HIGH", "CRITICAL") and not has_uncertainty_language:
            return SafetyCheckResult(
                check_type=SafetyCheckType.MISSING_UNCERTAINTY,
                passed=False,
                action=SafetyAction.WARN,
                message="High-risk response should communicate uncertainty",
                details={"risk_level": risk_level}
            )
        
        return SafetyCheckResult(
            check_type=SafetyCheckType.MISSING_UNCERTAINTY,
            passed=True,
            action=SafetyAction.ALLOW,
            message="Uncertainty check passed",
        )
    
    def _check_fabricated_citations(self, content: str, provided_sources: List[Any]) -> SafetyCheckResult:
        """Check for potentially fabricated legal citations"""
        # Patterns for legal citations
        citation_patterns = [
            r"\b\d+\s+U\.S\.C\.\s+§\s+\d+[a-z]?(?:\(\w+\))?",
            r"\b\d+\s+C\.F\.R\.\s+§\s+\d+",
            r"\b\d+\s+[A-Z][a-z]+\s+\d+\s+\(\d{4}\)",
            r"\b[A-Z][a-z]+\s+v\.\s+[A-Z][a-z]+",
        ]
        
        found_citations = []
        for pattern in citation_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            found_citations.extend(matches)
        
        if found_citations and not provided_sources:
            return SafetyCheckResult(
                check_type=SafetyCheckType.FABRICATED_CITATION,
                passed=False,
                action=SafetyAction.MODIFY,
                message="Citations found but no verified sources provided",
                details={"citations": found_citations[:5]}
            )
        
        # If we have sources, check if citations match (simplified)
        if found_citations and provided_sources:
            # In production, would do proper cross-reference
            pass
        
        return SafetyCheckResult(
            check_type=SafetyCheckType.FABRICATED_CITATION,
            passed=True,
            action=SafetyAction.ALLOW,
            message="Citation check passed",
        )
    
    def _check_risk_guidance(self, content: str, risk_level: str) -> SafetyCheckResult:
        """Check that guidance is appropriate for risk level"""
        content_lower = content.lower()
        
        if risk_level in ("HIGH", "CRITICAL"):
            # Should encourage attorney consultation
            attorney_keywords = ["attorney", "lawyer", "legal counsel", "legal professional"]
            has_attorney_rec = any(kw in content_lower for kw in attorney_keywords)
            
            if not has_attorney_rec:
                return SafetyCheckResult(
                    check_type=SafetyCheckType.INAPPROPRIATE_RISK_GUIDANCE,
                    passed=False,
                    action=SafetyAction.MODIFY,
                    message="High-risk response should recommend attorney consultation",
                    details={"risk_level": risk_level}
                )
        
        return SafetyCheckResult(
            check_type=SafetyCheckType.INAPPROPRIATE_RISK_GUIDANCE,
            passed=True,
            action=SafetyAction.ALLOW,
            message="Risk-appropriate guidance check passed",
        )
    
    def _check_prompt_injection_in_response(self, content: str) -> SafetyCheckResult:
        """Defense in depth: check response doesn't contain injection artifacts"""
        injection_indicators = [
            "ignore previous instructions",
            "system prompt",
            "as an ai",
            "i cannot",
            "i'm not able",
        ]
        
        content_lower = content.lower()
        for indicator in injection_indicators:
            if indicator in content_lower:
                return SafetyCheckResult(
                    check_type=SafetyCheckType.PROMPT_INJECTION,
                    passed=False,
                    action=SafetyAction.BLOCK,
                    message=f"Potential injection artifact in response: {indicator}",
                    details={"indicator": indicator}
                )
        
        return SafetyCheckResult(
            check_type=SafetyCheckType.PROMPT_INJECTION,
            passed=True,
            action=SafetyAction.ALLOW,
            message="No injection artifacts in response",
        )


class SafetyModificator:
    """Modifies responses to address safety issues"""
    
    @staticmethod
    def add_disclaimer(response: str, jurisdiction: Jurisdiction) -> str:
        """Add standard disclaimer to response"""
        from app.services.ai_workflow import DISCLAIMER
        return f"{response}\n\n{DISCLAIMER}"
    
    @staticmethod
    def add_escalation(response: str, risk_level: RiskLevel, jurisdiction: Jurisdiction) -> str:
        """Add escalation guidance"""
        if risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            escalation = (
                f"\n\n⚠️ **Important**: This appears to be a {risk_level.value}-risk legal matter. "
                "You should consult with a qualified attorney as soon as possible. "
                "Consider contacting: local legal aid organizations, bar association referral services, "
                "or public defender offices (for criminal matters). "
                "Do not rely solely on this information for decisions affecting your legal rights."
            )
            return f"{response}{escalation}"
        return response
    
    @staticmethod
    def add_uncertainty(response: str, risk_level: RiskLevel) -> str:
        """Add uncertainty notes"""
        if risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            uncertainty = (
                "\n\n**Limitations**: This information is AI-generated and may not reflect the most current "
                "legal developments. Laws vary by jurisdiction and specific facts can significantly "
                "change the analysis. Please verify with a qualified attorney."
            )
            return f"{response}{uncertainty}"
        return response
    
    @staticmethod
    def remove_definitive_language(response: str) -> str:
        """Remove or soften definitive legal language"""
        # Replace definitive phrases with qualified versions
        replacements = {
            r"(?i)\byou will win\b": "you may have a strong case",
            r"(?i)\byou cannot lose\b": "the outcome is uncertain",
            r"(?i)\bguaranteed\b": "likely",
            r"(?i)\bdefinitely\b": "likely",
            r"(?i)\bcertainly\b": "probably",
            r"(?i)\bthe court will\b": "the court may",
            r"(?i)\byou have the right to\b": "you may have the right to",
            r"(?i)\byou are entitled to\b": "you may be entitled to",
        }
        
        modified = response
        for pattern, replacement in replacements.items():
            modified = re.sub(pattern, replacement, modified)
        
        return modified
    
    @staticmethod
    def apply_fallback(
        question: str,
        risk_level: RiskLevel,
        jurisdiction: Jurisdiction,
        error_reason: str
    ) -> str:
        """Generate a safe fallback response"""
        from app.services.ai_workflow import DISCLAIMER
        
        if risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            return (
                f"I'm unable to provide a complete analysis of your legal question at this time. "
                f"This appears to be a {risk_level.value}-risk legal matter that requires professional attention.\n\n"
                f"You should consult with a qualified attorney as soon as possible. "
                f"Consider contacting: local legal aid organizations, bar association referral services, "
                f"or public defender offices (for criminal matters).\n\n"
                f"{DISCLAIMER}"
            )
        else:
            return (
                f"I'm unable to provide a complete analysis of your legal question at this time. "
                f"Here is general guidance: consult with a qualified attorney in your jurisdiction, "
                f"gather relevant documents, and consider contacting legal aid organizations.\n\n"
                f"{DISCLAIMER}"
            )


def create_safety_layer() -> SafetyLayer:
    """Factory function for safety layer"""
    return SafetyLayer()


def create_safety_modificator() -> SafetyModificator:
    """Factory function for safety modificator"""
    return SafetyModificator()