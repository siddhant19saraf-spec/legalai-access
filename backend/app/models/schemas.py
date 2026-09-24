from enum import Enum
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime


class Jurisdiction(str, Enum):
    US_FEDERAL = "us_federal"
    US_CA = "us_ca"
    US_NY = "us_ny"
    US_TX = "us_tx"
    UK = "uk"
    CA_FEDERAL = "ca_federal"
    CA_ON = "ca_on"
    AU_FEDERAL = "au_federal"
    EU = "eu"
    INTERNATIONAL = "international"
    UNKNOWN = "unknown"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RequestType(str, Enum):
    GENERAL_INFO = "general_info"
    PROCEDURAL_GUIDANCE = "procedural_guidance"
    RIGHTS_EXPLANATION = "rights_explanation"
    DEADLINE_INQUIRY = "deadline_inquiry"
    DOCUMENT_REVIEW = "document_review"
    FORM_ASSISTANCE = "form_assistance"
    ESCALATION_NEEDED = "escalation_needed"
    UNSUPPORTED = "unsupported"


class LegalCategory(str, Enum):
    HOUSING = "housing"
    EMPLOYMENT = "employment"
    FAMILY = "family"
    CRIMINAL = "criminal"
    IMMIGRATION = "immigration"
    CONSUMER = "consumer"
    CIVIL_RIGHTS = "civil_rights"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    FINANCIAL = "financial"
    OTHER = "other"


class SourceType(str, Enum):
    STATUTE = "statute"
    REGULATION = "regulation"
    CASE_LAW = "case_law"
    GOVERNMENT_PUBLICATION = "government_publication"
    COURT_RULE = "court_rule"
    LEGAL_AID_RESOURCE = "legal_aid_resource"
    UNKNOWN = "unknown"


class Source(BaseModel):
    type: SourceType
    title: str
    citation: Optional[str] = None
    url: Optional[str] = None
    jurisdiction: Jurisdiction
    excerpt: Optional[str] = None
    verified: bool = False
    retrieval_date: datetime = Field(default_factory=datetime.utcnow)


class ClarificationQuestion(BaseModel):
    question: str
    reason: str
    required: bool = False


class CoverageLevel(str, Enum):
    HIGH = "high"
    MODERATE = "moderate"
    LIMITED = "limited"


class QuestionQuality(BaseModel):
    score: int = Field(ge=0, le=100)
    level: str = "needs_more_context"
    missing_information: List[str] = []
    is_complete: bool = False


class TerminologyExplanation(BaseModel):
    term: str
    explanation: str
    category: str = "general"


class DocumentChecklistItem(BaseModel):
    item: str
    category: str
    relevant: bool = True


class FollowUpSuggestion(BaseModel):
    question: str
    reason: str
    category: str = "general"


class LegalResponse(BaseModel):
    request_type: RequestType
    risk_level: RiskLevel
    legal_category: LegalCategory
    jurisdiction: Jurisdiction
    summary: str
    explanation: str
    sources: List[Source] = []
    clarification_questions: List[ClarificationQuestion] = []
    next_steps: List[str] = []
    escalation_guidance: Optional[str] = None
    uncertainty_notes: List[str] = []
    disclaimer: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    # Competition-quality additions
    question_quality: Optional[QuestionQuality] = None
    information_coverage: Optional[CoverageLevel] = None
    coverage_reason: Optional[str] = None
    terminology_explanations: List[TerminologyExplanation] = []
    document_checklist: List[DocumentChecklistItem] = []
    follow_up_suggestions: List[FollowUpSuggestion] = []
    provider_status: Optional[str] = None


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=5000)
    jurisdiction: Optional[Jurisdiction] = None
    context: Optional[str] = Field(default=None, max_length=2000)
    conversation_id: Optional[str] = None

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        # Basic sanitization - remove potential prompt injection attempts
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Question must be at least 3 characters")
        return v


class AskResponse(BaseModel):
    response: LegalResponse
    conversation_id: str


class FeedbackRequest(BaseModel):
    conversation_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=1000)
    issue_type: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    ai_provider: str


class ErrorResponse(BaseModel):
    error: str
    code: str
    details: Optional[Dict[str, Any]] = None