import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

from app.models.schemas import (
    Jurisdiction, RiskLevel, RequestType, LegalCategory,
    SourceType, Source, ClarificationQuestion, LegalResponse
)

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    parsed_data: Optional[Dict[str, Any]] = None


class OutputValidator:
    """
    Validates AI-generated responses before returning to user.
    
    Ensures:
    1. JSON structure matches expected schema
    2. Required fields are present
    3. No fabricated legal citations
    3. Risk-appropriate content
    4. Disclaimer present
    """
    
    # Required fields in AI response
    REQUIRED_FIELDS = [
        "summary",
        "explanation", 
        "next_steps",
        "escalation_guidance",
        "uncertainty_notes"
    ]
    
    # Patterns that indicate fabricated content
    FABRICATION_PATTERNS = [
        # Fake statute citations
        (r"\b\d+\s+U\.S\.C\.\s+§\s+\d+[a-z]?(?:\(\w+\))?", "fake_us_code"),
        (r"\b\d+\s+C\.F\.R\.\s+§\s+\d+", "fake_cfr"),
        # Fake case citations
        (r"\b\d+\s+[A-Z][a-z]+\s+\d+\s+\(\d{4}\)", "fake_case_citation"),
        (r"\b[A-Z][a-z]+\s+v\.\s+[A-Z][a-z]+", "fake_case_name"),
        # Fake government URLs
        (r"https?://(?:www\.)?(?:gov|state|federal)\.[a-z]{2,}/[^\s]*statute", "fake_gov_url"),
        # Fake legal deadlines
        (r"(?i)\b(?:statute of limitations|deadline|filing deadline)\s+(?:is|:)\s+\d+\s+(?:days?|months?|years?)", "potential_fake_deadline"),
        # Made up legal sections
        (r"(?i)section\s+\d+(?:\.\d+)*(?:\([a-z]\))?(?:\s+of\s+(?:the\s+)?(?:act|code|statute))?", "potential_fake_section"),
    ]
    
    def __init__(self):
        self._fabrication_patterns = [
            (re.compile(pattern, re.IGNORECASE), category)
            for pattern, category in self.FABRICATION_PATTERNS
        ]
    
    def validate(self, ai_content: str, context: Dict[str, Any]) -> ValidationResult:
        """
        Validate AI response content.
        
        Args:
            ai_content: Raw AI response content
            context: Context including risk_level, jurisdiction, sources, etc.
            
        Returns:
            ValidationResult with validation status and any errors/warnings
        """
        errors = []
        warnings = []
        parsed_data = None
        
        # 1. Parse JSON
        try:
            parsed_data = json.loads(ai_content)
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON: {e}")
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                parsed_data=None
            )
        
        # 2. Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in parsed_data:
                errors.append(f"Missing required field: {field}")
            elif parsed_data[field] is None:
                if field != "escalation_guidance":  # This can be null
                    warnings.append(f"Field '{field}' is null")
        
        if errors:
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                parsed_data=parsed_data
            )
        
        # 3. Validate field types and content
        self._validate_field_types(parsed_data, errors, warnings)
        
        # 4. Check for fabricated content
        self._check_fabrication(parsed_data, errors, warnings)
        
        # 5. Validate risk-appropriate content
        risk_level = context.get("risk_level")
        if risk_level:
            self._validate_risk_appropriateness(parsed_data, risk_level, errors, warnings)
        
        # 6. Verify sources match provided sources
        provided_sources = context.get("sources", [])
        self._validate_sources(parsed_data, provided_sources, errors, warnings)
        
        # 7. Check disclaimer presence
        if "disclaimer" not in context or not context.get("disclaimer"):
            warnings.append("No disclaimer provided in context")
        
        is_valid = len(errors) == 0
        
        if not is_valid:
            logger.warning(f"Output validation failed | errors={errors} warnings={warnings}")
        elif warnings:
            logger.info(f"Output validation passed with warnings | warnings={warnings}")
        else:
            logger.debug("Output validation passed")
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            parsed_data=parsed_data
        )
    
    def _validate_field_types(self, data: Dict[str, Any], errors: List[str], warnings: List[str]):
        """Validate field types and basic constraints"""
        
        # summary: string, reasonable length
        summary = data.get("summary", "")
        if not isinstance(summary, str):
            errors.append("summary must be a string")
        elif len(summary) < 10:
            warnings.append("summary is very short")
        elif len(summary) > 1000:
            warnings.append("summary is very long")
        
        # explanation: string
        explanation = data.get("explanation", "")
        if not isinstance(explanation, str):
            errors.append("explanation must be a string")
        elif len(explanation) < 20:
            warnings.append("explanation is very short")
        
        # next_steps: list of strings
        next_steps = data.get("next_steps", [])
        if not isinstance(next_steps, list):
            errors.append("next_steps must be a list")
        else:
            for i, step in enumerate(next_steps):
                if not isinstance(step, str):
                    errors.append(f"next_steps[{i}] must be a string")
            if len(next_steps) == 0:
                warnings.append("No next steps provided")
            elif len(next_steps) > 10:
                warnings.append("Many next steps provided")
        
        # escalation_guidance: string or null
        escalation = data.get("escalation_guidance")
        if escalation is not None and not isinstance(escalation, str):
            errors.append("escalation_guidance must be a string or null")
        
        # uncertainty_notes: list of strings
        uncertainty = data.get("uncertainty_notes", [])
        if not isinstance(uncertainty, list):
            errors.append("uncertainty_notes must be a list")
        else:
            for i, note in enumerate(uncertainty):
                if not isinstance(note, str):
                    errors.append(f"uncertainty_notes[{i}] must be a string")
            if len(uncertainty) == 0:
                warnings.append("No uncertainty notes provided")
    
    def _check_fabrication(self, data: Dict[str, Any], errors: List[str], warnings: List[str]):
        """Check for potentially fabricated legal citations"""
        
        text_to_check = " ".join([
            str(data.get("summary", "")),
            str(data.get("explanation", "")),
            " ".join(data.get("next_steps", [])),
            str(data.get("escalation_guidance", "")),
            " ".join(data.get("uncertainty_notes", [])),
        ])
        
        for pattern, category in self._fabrication_patterns:
            matches = pattern.findall(text_to_check)
            if matches:
                # If we have verified sources, check if the citation matches
                # For now, flag as warning - in production would cross-reference
                warnings.append(f"Potential fabricated content detected: {category} - matches: {matches[:3]}")
    
    def _validate_risk_appropriateness(
        self, 
        data: Dict[str, Any], 
        risk_level: str, 
        errors: List[str], 
        warnings: List[str]
    ):
        """Validate that response is appropriate for the risk level"""
        
        escalation = data.get("escalation_guidance")
        uncertainty = data.get("uncertainty_notes", [])
        explanation = data.get("explanation", "")
        
        if risk_level in ("HIGH", "CRITICAL"):
            # High risk MUST have escalation guidance
            if not escalation:
                errors.append(f"High/Critical risk requires escalation_guidance")
            
            # High risk MUST have uncertainty notes
            if not uncertainty or len(uncertainty) == 0:
                errors.append(f"High/Critical risk requires uncertainty_notes")
            
            # Check for overly definitive language
            definitive_phrases = [
                "you will win",
                "you cannot lose",
                "guaranteed",
                "definitely",
                "certainly will",
                "the court will",
                "you have the right to",
            ]
            explanation_lower = explanation.lower()
            for phrase in definitive_phrases:
                if phrase in explanation_lower:
                    warnings.append(f"Potentially definitive language in high-risk response: '{phrase}'")
        
        elif risk_level == "MEDIUM":
            # Medium risk SHOULD have escalation guidance
            if not escalation:
                warnings.append("Medium risk should have escalation_guidance")
            
            if not uncertainty:
                warnings.append("Medium risk should have uncertainty_notes")
    
    def _validate_sources(
        self, 
        data: Dict[str, Any], 
        provided_sources: List[Any], 
        errors: List[str], 
        warnings: List[str]
    ):
        """Validate that cited sources match provided verified sources"""
        
        # Check if response references sources that weren't provided
        # This is a simplified check - in production would be more sophisticated
        explanation = data.get("explanation", "").lower()
        
        # Look for citations in the explanation
        citation_pattern = re.compile(r'\b\d+\s+[A-Z][a-z]+\s+\d+', re.IGNORECASE)
        found_citations = citation_pattern.findall(explanation)
        
        if found_citations and not provided_sources:
            warnings.append("Response contains citations but no verified sources were provided")
    
    def validate_legal_response(self, response: LegalResponse, context: Dict[str, Any]) -> ValidationResult:
        """Validate a fully constructed LegalResponse object"""
        errors = []
        warnings = []
        
        # Check disclaimer
        if not response.disclaimer or len(response.disclaimer) < 50:
            warnings.append("Disclaimer missing or too short")
        
        # Check risk-appropriate escalation
        if response.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            if not response.escalation_guidance:
                errors.append("High/Critical risk requires escalation_guidance")
        
        # Check sources are from verified list
        for source in response.sources:
            if not source.verified:
                warnings.append(f"Unverified source included: {source.title}")
        
        # Check uncertainty notes
        if response.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            if not response.uncertainty_notes or len(response.uncertainty_notes) == 0:
                errors.append("High/Critical risk requires uncertainty_notes")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            parsed_data=response.model_dump()
        )


class FallbackResponseGenerator:
    """Generates safe fallback responses when validation fails"""
    
    @staticmethod
    def generate_fallback(
        question: str,
        risk_level: RiskLevel,
        jurisdiction: Jurisdiction,
        error_reason: str
    ) -> LegalResponse:
        """Generate a safe fallback response"""
        
        from app.services.ai_workflow import DISCLAIMER
        
        if risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            summary = (
                "I'm unable to provide a complete analysis of your legal question at this time. "
                "This appears to be a high-risk legal matter that requires professional attention."
            )
            escalation_guidance = (
                f"This is a {risk_level.value}-risk legal matter. You should consult with a qualified "
                "attorney as soon as possible. Consider contacting: local legal aid organizations, "
                "bar association referral services, or public defender offices (for criminal matters)."
            )
        else:
            summary = (
                "I'm unable to provide a complete analysis of your legal question at this time. "
                "Here is general guidance for your situation."
            )
            escalation_guidance = None
        
        return LegalResponse(
            request_type=RequestType.GENERAL_INFO,
            risk_level=risk_level,
            legal_category=LegalCategory.OTHER,
            jurisdiction=jurisdiction,
            summary=summary,
            explanation=(
                f"I encountered an issue while processing your question: {error_reason}. "
                "Please try rephrasing your question or consult with a qualified attorney "
                "for specific legal guidance."
            ),
            sources=[],
            clarification_questions=[],
            next_steps=[
                "Consult with a qualified attorney in your jurisdiction",
                "Gather relevant documents and evidence",
                "Consider contacting legal aid organizations"
            ],
            escalation_guidance=escalation_guidance,
            uncertainty_notes=[
                "This is a fallback response due to a processing error",
                "The information provided may be incomplete",
                "Please verify with a qualified legal professional"
            ],
            disclaimer=DISCLAIMER
        )


def create_output_validator() -> OutputValidator:
    """Factory function for output validator"""
    return OutputValidator()