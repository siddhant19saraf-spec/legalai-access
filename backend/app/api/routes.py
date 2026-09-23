import uuid
import logging
from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    AskRequest, AskResponse, FeedbackRequest, HealthResponse,
    Jurisdiction
)
from app.services.ai_workflow import process_legal_question

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["legal-assistance"])


# In-memory feedback storage (replace with database in production)
feedback_store: list = []


@router.get("/health", response_model=HealthResponse)
async def health_check():
    from app.core.config import settings
    ai_provider = "openai" if settings.openai_api_key else "anthropic"
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        ai_provider=ai_provider
    )


def _categorize_llm_error(exc: Exception) -> str:
    name = type(exc).__name__
    status = getattr(exc, "status_code", None)
    if status in (401, 403) or "Auth" in name or "Permission" in name:
        return "auth"
    if status == 429 or "RateLimit" in name:
        return "rate_limit_or_quota"
    if "Connection" in name or "Timeout" in name or "Network" in name:
        return "network"
    if status == 404 or "NotFound" in name:
        return "not_found"
    if status == 400 or "BadRequest" in name:
        return "bad_request"
    if isinstance(exc, RuntimeError):
        return "runtime_config"
    if status and int(status) >= 500:
        return "server_error"
    return "unknown"


@router.get("/ai-diagnostic")
async def ai_diagnostic():
    """Attempt one minimal completion; return provider + error category only.

    Never returns API keys, raw exception messages, or stack traces.
    """
    from app.services.llm_client import get_llm_client, MockProvider, LLMMessage

    client = get_llm_client()
    provider = client.provider
    provider_name = type(provider).__name__

    if isinstance(provider, MockProvider):
        return {
            "provider": provider_name,
            "model": provider.get_model_name(),
            "success": False,
            "error_category": "no_valid_key",
            "error_type": None,
            "status_code": None,
        }

    try:
        resp = await provider.complete(
            messages=[LLMMessage(role="user", content='Reply with only valid JSON: {"ok":true}')],
            temperature=0.0,
            max_tokens=32,
            response_format={"type": "json_object"},
        )
        return {
            "provider": provider_name,
            "model": provider.get_model_name(),
            "success": True,
            "error_category": None,
            "error_type": None,
            "status_code": None,
            "latency_ms": resp.latency_ms,
        }
    except Exception as e:
        return {
            "provider": provider_name,
            "model": provider.get_model_name(),
            "success": False,
            "error_category": _categorize_llm_error(e),
            "error_type": type(e).__name__,
            "status_code": getattr(e, "status_code", None),
        }


@router.post("/ask", response_model=AskResponse)
async def ask_legal_question(request: AskRequest):
    """
    Process a legal question through the AI workflow.
    
    This endpoint:
    1. Validates and sanitizes input
    2. Classifies request type and risk level
    3. Detects jurisdiction
    4. Retrieves relevant verified sources
    5. Generates AI response with safety checks
    6. Returns structured response with disclaimers
    """
    conversation_id = request.conversation_id or str(uuid.uuid4())
    
    try:
        # Validate jurisdiction if provided
        jurisdiction = request.jurisdiction
        if jurisdiction and jurisdiction not in Jurisdiction:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid jurisdiction",
                    "code": "INVALID_JURISDICTION",
                    "details": {"valid_values": [j.value for j in Jurisdiction]}
                }
            )
        
        # Process through AI workflow
        response = await process_legal_question(
            request=request,
            conversation_id=conversation_id
        )
        
        logger.info(
            f"Processed legal question | conversation_id={conversation_id} "
            f"risk={response.risk_level.value} category={response.legal_category.value}"
        )
        
        return AskResponse(
            response=response,
            conversation_id=conversation_id
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail={"error": str(e), "code": "VALIDATION_ERROR"}
        )
    except Exception as e:
        logger.error(f"Error processing question: {e}", exc_info=True)
        # Don't expose internal errors
        raise HTTPException(
            status_code=500,
            detail={
                "error": "An error occurred processing your question. Please try again.",
                "code": "INTERNAL_ERROR"
            }
        )


@router.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    """Submit feedback for a conversation"""
    try:
        feedback_entry = {
            "conversation_id": feedback.conversation_id,
            "rating": feedback.rating,
            "comment": feedback.comment,
            "issue_type": feedback.issue_type,
            "timestamp": __import__("datetime").datetime.utcnow().isoformat()
        }
        feedback_store.append(feedback_entry)
        
        logger.info(f"Feedback received | conversation_id={feedback.conversation_id} rating={feedback.rating}")
        
        return {"status": "received", "message": "Thank you for your feedback"}
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        return {"status": "error", "message": "Unable to submit feedback. Please try again."}


@router.get("/feedback/stats")
async def get_feedback_stats():
    """Get feedback statistics (admin endpoint)"""
    try:
        if not feedback_store:
            return {"total": 0, "average_rating": 0, "ratings_distribution": {}}
        
        ratings = [f["rating"] for f in feedback_store]
        distribution = {}
        for r in range(1, 6):
            distribution[str(r)] = ratings.count(r)
        
        return {
            "total": len(feedback_store),
            "average_rating": round(sum(ratings) / len(ratings), 2),
            "ratings_distribution": distribution
        }
    except Exception as e:
        logger.error(f"Error getting feedback stats: {e}")
        return {"total": 0, "average_rating": 0, "ratings_distribution": {}}


@router.get("/jurisdictions")
async def list_jurisdictions():
    """List supported jurisdictions"""
    try:
        return {
            "jurisdictions": [
                {"value": j.value, "label": j.value.replace("_", " ").title()}
                for j in Jurisdiction
                if j != Jurisdiction.UNKNOWN
            ]
        }
    except Exception as e:
        logger.error(f"Error listing jurisdictions: {e}")
        return {"jurisdictions": []}


@router.get("/categories")
async def list_categories():
    """List legal categories"""
    try:
        from app.models.schemas import LegalCategory
        return {
            "categories": [
                {"value": c.value, "label": c.value.replace("_", " ").title()}
                for c in LegalCategory
            ]
        }
    except Exception as e:
        logger.error(f"Error listing categories: {e}")
        return {"categories": []}