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