import json
import re
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from app.models.schemas import (
    Jurisdiction, RiskLevel, RequestType, LegalCategory,
    SourceType, Source, ClarificationQuestion, LegalResponse,
    AskRequest
)
from app.core.config import settings

from app.services.llm_client import (
    LLMClient, LLMMessage, get_llm_client, MockProvider
)
from app.services.prompt_defense import (
    PromptInjectionDefense, sanitize_user_input
)
from app.services.output_validator import (
    OutputValidator, ValidationResult, create_output_validator, FallbackResponseGenerator
)
from app.services.safety import (
    SafetyLayer, SafetyModificator, SafetyAssessment, SafetyAction, create_safety_layer, create_safety_modificator
)
from app.services.conversation import (
    ConversationManager, ConversationMessage, get_conversation_manager
)
from app.services.source_verifier import (
    SourceRepository, get_source_repository
)
from app.services.observability import (
    get_request_logger, set_request_context, log_api_request, log_error,
    trace_operation, log_ai_request, log_ai_response, log_classification,
    log_source_retrieval, log_validation, log_safety_check
)
from app.services.constants import (
    HIGH_RISK_KEYWORDS, REQUEST_TYPE_PATTERNS, LEGAL_CATEGORY_PATTERNS,
    JURISDICTION_PATTERNS, VERIFIED_SOURCES, DISCLAIMER,
    classify_request_type, classify_legal_category, detect_jurisdiction,
    assess_risk_level, retrieve_sources, generate_clarification_questions,
    build_ai_prompt
)

logger = get_request_logger()


# Re-export the core functions for backward compatibility
__all__ = [
    "process_legal_question",
    "classify_request_type",
    "classify_legal_category", 
    "detect_jurisdiction",
    "assess_risk_level",
    "retrieve_sources",
    "generate_clarification_questions",
    "build_ai_prompt",
    "HIGH_RISK_KEYWORDS",
    "REQUEST_TYPE_PATTERNS",
    "LEGAL_CATEGORY_PATTERNS",
    "JURISDICTION_PATTERNS",
    "VERIFIED_SOURCES",
    "DISCLAIMER",
]


# Initialize services
_llm_client = get_llm_client()
_prompt_defense = PromptInjectionDefense(strict_mode=True)
_output_validator = create_output_validator()
_safety_layer = create_safety_layer()
_safety_modificator = create_safety_modificator()
_conversation_manager = get_conversation_manager()
_source_repository = get_source_repository()


@trace_operation("process_legal_question")
async def process_legal_question(
    request: AskRequest,
    conversation_id: Optional[str] = None,
) -> LegalResponse:
    """
    Process a legal question through the complete AI pipeline.
    
    Pipeline:
    1. Input Validation & Sanitization
    2. Prompt Injection Defense
    3. Request Classification
    4. Jurisdiction Detection
    5. Risk Assessment
    6. Source Retrieval
    7. Clarification Questions
    8. AI Generation (with conversation context)
    9. Output Validation
    10. Safety Check
    11. Response Modification (if needed)
    12. Structured Response
    """
    # Generate request ID for tracing
    request_id = str(uuid.uuid4())[:8]
    conv_id = conversation_id or request.conversation_id or str(uuid.uuid4())
    
    # Set observability context
    set_request_context(request_id=request_id, conversation_id=conv_id)
    
    logger = get_request_logger()
    logger.info(
        "legal_question_received",
        question_length=len(request.question),
        jurisdiction=request.jurisdiction.value if request.jurisdiction else None,
        has_context=bool(request.context),
    )
    
    try:
        # Step 1: Input Validation (already done by Pydantic, but double-check)
        question = request.question.strip()
        if len(question) < 3:
            raise ValueError("Question must be at least 3 characters")
        
        # Step 2: Prompt Injection Defense
        sanitized_question, injection_attempt = sanitize_user_input(question, strict=True)
        
        if injection_attempt.detected and injection_attempt.risk_score > 0.7:
            logger.warning(
                "high_risk_injection_blocked",
                risk_score=injection_attempt.risk_score,
                patterns=injection_attempt.patterns_matched,
            )
            return _create_blocked_response(
                conv_id, request.jurisdiction, "Input blocked due to security policy"
            )
        
        # Use sanitized question
        question = sanitized_question
        
        # Sanitize context if provided
        context = request.context
        if context:
            sanitized_context, ctx_injection = sanitize_user_input(context, strict=True)
            if ctx_injection.detected and ctx_injection.risk_score > 0.5:
                logger.warning("context_injection_detected", patterns=ctx_injection.patterns_matched)
                context = sanitized_context
            else:
                context = sanitized_context
        
        # Get or create conversation
        conversation = _conversation_manager.get_or_create(conv_id)
        
        # Add user message to conversation
        _conversation_manager.add_user_message(
            conv_id, question, 
            metadata={"request_id": request_id, "context": context}
        )
        
        # Step 3: Request Classification
        request_type = classify_request_type(question)
        log_classification(
            request_type=request_type.value,
            legal_category="",  # Will be set below
            risk_level="",      # Will be set below
            jurisdiction=request.jurisdiction.value if request.jurisdiction else "unknown",
        )
        
        # Step 4: Jurisdiction Detection
        jurisdiction = request.jurisdiction
        if jurisdiction is None:
            jurisdiction = detect_jurisdiction(question, context)
        
        # Step 5: Legal Category Classification
        legal_category = classify_legal_category(question)
        
        # Step 6: Risk Assessment
        risk_level = assess_risk_level(question, request_type, legal_category)
        
        # Update classification log with complete info
        log_classification(
            request_type=request_type.value,
            legal_category=legal_category.value,
            risk_level=risk_level.value,
            jurisdiction=jurisdiction.value,
        )
        
        # Step 7: Source Retrieval
        sources = retrieve_sources(question, jurisdiction, legal_category)
        log_source_retrieval(
            source_count=len(sources),
            jurisdiction=jurisdiction.value,
            legal_category=legal_category.value,
        )
        
        # Step 8: Generate Clarification Questions
        clarification_questions = generate_clarification_questions(
            question, request_type, legal_category, jurisdiction
        )
        
        # Add clarification questions to conversation context if any
        if clarification_questions:
            for cq in clarification_questions:
                if cq.required:
                    _conversation_manager.add_clarification_pending(conv_id, cq.question)
        
        # Step 9: AI Generation
        # Get conversation context for LLM
        llm_messages, legal_context = _conversation_manager.get_context_for_query(
            conv_id, max_messages=5
        )
        
        # Build prompt
        prompt = build_ai_prompt(
            question, request_type, risk_level, legal_category,
            jurisdiction, sources, clarification_questions, context
        )
        
        # Add conversation context to prompt
        if llm_messages:
            context_section = "CONVERSATION CONTEXT:\n" + "\n".join([
                f"{msg['role']}: {msg['content']}" for msg in llm_messages
            ]) + "\n---\n"
            prompt = prompt.replace("USER QUESTION:", f"{context_section}USER QUESTION:")
        
        # Call LLM with structured output
        response_format = {"type": "json_object"}
        messages = [
            LLMMessage(role="system", content="You are a legal information assistant. Provide accurate, plain-language legal information with appropriate caveats. Always respond in valid JSON format."),
            LLMMessage(role="user", content=prompt),
        ]
        
        log_ai_request(len(prompt), settings.openai_model, risk_level.value, jurisdiction.value)
        
        try:
            llm_response = await _llm_client.complete_with_retry(
                messages=messages,
                temperature=0.1,
                max_tokens=2000,
                response_format=response_format,
            )
            
            log_ai_response(
                latency_ms=llm_response.latency_ms,
                tokens_used=llm_response.usage.get("total_tokens") if llm_response.usage else None,
                success=True,
            )
            
            ai_result = json.loads(llm_response.content)
            
        except json.JSONDecodeError as e:
            logger.error("llm_invalid_json", error=str(e))
            ai_result = _get_fallback_ai_result()
        except Exception as e:
            logger.error("llm_request_failed", error=str(e))
            ai_result = _get_fallback_ai_result()
        
        # Step 10: Output Validation
        validation_context = {
            "risk_level": risk_level.value,
            "jurisdiction": jurisdiction.value,
            "sources": sources,
            "has_disclaimer": True,
            "has_escalation": bool(ai_result.get("escalation_guidance")),
            "has_uncertainty": bool(ai_result.get("uncertainty_notes")),
        }
        
        validation_result = _output_validator.validate(
            json.dumps(ai_result), validation_context
        )
        
        log_validation(
            passed=validation_result.is_valid,
            errors=validation_result.errors,
            warnings=validation_result.warnings,
        )
        
        # If validation failed, use fallback
        if not validation_result.is_valid:
            logger.warning("validation_failed_using_fallback", errors=validation_result.errors)
            ai_result = _get_fallback_ai_result()
            validation_result = _output_validator.validate(
                json.dumps(ai_result), validation_context
            )
        
        # Build the response object
        escalation_guidance = ai_result.get("escalation_guidance")
        if risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL) and not escalation_guidance:
            escalation_guidance = (
                f"This appears to be a {risk_level.value}-risk legal matter. "
                "You should consult with a qualified attorney as soon as possible. "
                "Consider contacting: local legal aid organizations, bar association referral services, "
                "or public defender offices (for criminal matters). "
                "Do not rely solely on this information for decisions affecting your legal rights."
            )
        
        response = LegalResponse(
            request_type=request_type,
            risk_level=risk_level,
            legal_category=legal_category,
            jurisdiction=jurisdiction,
            summary=ai_result.get("summary", "Legal information summary unavailable."),
            explanation=ai_result.get("explanation", "Explanation unavailable."),
            sources=sources,
            clarification_questions=clarification_questions,
            next_steps=ai_result.get("next_steps", []),
            escalation_guidance=escalation_guidance,
            uncertainty_notes=ai_result.get("uncertainty_notes", []),
            disclaimer=DISCLAIMER,
        )
        
        # Step 11: Safety Check
        safety_context = {
            "risk_level": risk_level.value,
            "jurisdiction": jurisdiction.value,
            "has_disclaimer": True,
            "has_escalation": bool(escalation_guidance),
            "has_uncertainty": bool(response.uncertainty_notes),
            "sources": sources,
        }
        
        # Combine response content for safety check
        response_content = "\n".join([
            response.summary,
            response.explanation,
            "\n".join(response.next_steps),
            escalation_guidance or "",
            "\n".join(response.uncertainty_notes),
        ])
        
        safety_assessment = _safety_layer.assess(response_content, safety_context)
        
        log_safety_check(
            check_type="comprehensive",
            passed=safety_assessment.overall_passed,
            details={"action": safety_assessment.overall_action.value, "checks": len(safety_assessment.checks)}
        )
        
        # Step 12: Apply Safety Modifications
        if safety_assessment.overall_action == SafetyAction.MODIFY:
            response = _apply_safety_modifications(response, risk_level, jurisdiction)
        elif safety_assessment.overall_action == SafetyAction.FALLBACK:
            return _create_fallback_response(response, risk_level, jurisdiction, "Safety check required fallback")
        elif safety_assessment.overall_action == SafetyAction.BLOCK:
            return _create_blocked_response(conv_id, jurisdiction, "Response blocked by safety policy")
        
        # Add assistant message to conversation
        _conversation_manager.add_assistant_message(
            conv_id,
            f"{response.summary}\n{response.explanation}",
            response=response,
            metadata={"request_id": request_id}
        )
        
        # Clear clarifications if they were answered
        if clarification_questions:
            _conversation_manager.clear_clarifications(conv_id)
        
        logger.info(
            "legal_question_processed",
            conversation_id=conv_id,
            risk_level=risk_level.value,
            legal_category=legal_category.value,
            safety_action=safety_assessment.overall_action.value,
        )
        
        return response
        
    except Exception as e:
        logger.error("process_legal_question_failed", error=str(e), exc_info=True)
        return _create_error_response(conv_id, request.jurisdiction, str(e))


def _get_fallback_ai_result() -> Dict[str, Any]:
    """Get a safe fallback AI result"""
    return {
        "summary": "I'm unable to provide a detailed analysis at this time. Please consult with a qualified attorney for specific legal guidance.",
        "explanation": "The AI system encountered an issue generating a detailed response. For reliable legal information, please speak with a licensed attorney in your jurisdiction.",
        "next_steps": [
            "Consult with a qualified attorney in your jurisdiction",
            "Gather relevant documents and evidence",
            "Consider contacting legal aid organizations"
        ],
        "escalation_guidance": None,
        "uncertainty_notes": [
            "This is a fallback response due to a processing issue",
            "The information provided may be incomplete",
            "Please verify with a qualified legal professional"
        ]
    }


def _create_fallback_response(
    response: LegalResponse,
    risk_level: RiskLevel,
    jurisdiction: Jurisdiction,
    reason: str
) -> LegalResponse:
    """Create a fallback response"""
    from app.services.safety import SafetyModificator
    fallback_text = SafetyModificator.apply_fallback(
        "", risk_level, jurisdiction, reason
    )
    
    return LegalResponse(
        request_type=response.request_type,
        risk_level=response.risk_level,
        legal_category=response.legal_category,
        jurisdiction=response.jurisdiction,
        summary="I'm unable to provide a complete analysis at this time.",
        explanation=fallback_text,
        sources=response.sources,
        clarification_questions=response.clarification_questions,
        next_steps=response.next_steps,
        escalation_guidance=response.escalation_guidance,
        uncertainty_notes=response.uncertainty_notes + ["Fallback response used due to safety/validation issue"],
        disclaimer=DISCLAIMER,
    )


def _create_blocked_response(
    conversation_id: str,
    jurisdiction: Optional[Jurisdiction],
    reason: str
) -> LegalResponse:
    """Create a response for blocked requests"""
    from app.services.ai_workflow import DISCLAIMER
    from app.models.schemas import RiskLevel, RequestType, LegalCategory
    
    return LegalResponse(
        request_type=RequestType.UNSUPPORTED,
        risk_level=RiskLevel.LOW,
        legal_category=LegalCategory.OTHER,
        jurisdiction=jurisdiction or Jurisdiction.UNKNOWN,
        summary="Your request could not be processed due to security policy.",
        explanation=(
            f"This request was blocked for security reasons: {reason}. "
            "Please rephrase your question and try again. "
            "If you believe this was an error, please contact support."
        ),
        sources=[],
        clarification_questions=[],
        next_steps=["Try rephrasing your question", "Contact support if this persists"],
        escalation_guidance=None,
        uncertainty_notes=["Request blocked by security policy"],
        disclaimer=DISCLAIMER,
    )


def _create_error_response(
    conversation_id: str,
    jurisdiction: Optional[Jurisdiction],
    error: str
) -> LegalResponse:
    """Create an error response"""
    from app.services.ai_workflow import DISCLAIMER
    from app.models.schemas import RiskLevel, RequestType, LegalCategory
    
    return LegalResponse(
        request_type=RequestType.UNSUPPORTED,
        risk_level=RiskLevel.LOW,
        legal_category=LegalCategory.OTHER,
        jurisdiction=jurisdiction or Jurisdiction.UNKNOWN,
        summary="An error occurred while processing your question.",
        explanation=(
            "I encountered an unexpected error while processing your request. "
            "Please try again or contact support if the problem persists."
        ),
        sources=[],
        clarification_questions=[],
        next_steps=["Try again", "Contact support if the problem continues"],
        escalation_guidance=None,
        uncertainty_notes=[f"Processing error: {error}"],
        disclaimer=DISCLAIMER,
    )


def _apply_safety_modifications(
    response: LegalResponse,
    risk_level: RiskLevel,
    jurisdiction: Jurisdiction
) -> LegalResponse:
    """Apply safety modifications to response"""
    from app.services.safety import SafetyModificator
    from app.services.ai_workflow import DISCLAIMER
    
    modified = response
    
    # Ensure disclaimer is present
    if not modified.disclaimer or len(modified.disclaimer) < 50:
        modified.disclaimer = DISCLAIMER
    
    # Add escalation for high risk
    if risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL) and not modified.escalation_guidance:
        modified.escalation_guidance = SafetyModificator.add_escalation(
            "", risk_level, response.jurisdiction
        ).strip()
    
    # Add uncertainty notes for high risk
    if risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL) and not modified.uncertainty_notes:
        modified.uncertainty_notes = [
            "This information is AI-generated and may not reflect the most current legal developments.",
            "Laws vary by jurisdiction and specific facts can significantly change the analysis.",
            "Please verify with a qualified attorney."
        ]
    
    return modified


# Convenience function for backward compatibility
async def process_legal_question_simple(
    question: str,
    jurisdiction: Optional[Jurisdiction] = None,
    context: Optional[str] = None,
) -> LegalResponse:
    """Simple interface for backward compatibility"""
    request = AskRequest(
        question=question,
        jurisdiction=jurisdiction,
        context=context,
    )
    return await process_legal_question(request)