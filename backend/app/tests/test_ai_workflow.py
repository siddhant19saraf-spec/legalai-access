import pytest
from app.models.schemas import (
    Jurisdiction, RiskLevel, RequestType, LegalCategory,
    SourceType, Source, ClarificationQuestion, LegalResponse,
    AskRequest, AskResponse, FeedbackRequest, HealthResponse, ErrorResponse
)
from app.services.ai_workflow import (
    classify_request_type, classify_legal_category, detect_jurisdiction,
    assess_risk_level, retrieve_sources, generate_clarification_questions,
    DISCLAIMER
)


class TestRequestClassification:
    def test_deadline_inquiry(self):
        assert classify_request_type("What is the deadline to file an appeal?") == RequestType.DEADLINE_INQUIRY
        assert classify_request_type("Statute of limitations for personal injury") == RequestType.DEADLINE_INQUIRY
    
    def test_procedural_guidance(self):
        assert classify_request_type("How do I file for divorce?") == RequestType.PROCEDURAL_GUIDANCE
        assert classify_request_type("Steps to file a restraining order") == RequestType.PROCEDURAL_GUIDANCE
    
    def test_rights_explanation(self):
        assert classify_request_type("What are my rights as a tenant?") == RequestType.RIGHTS_EXPLANATION
        assert classify_request_type("Am I entitled to overtime pay?") == RequestType.RIGHTS_EXPLANATION
    
    def test_form_assistance(self):
        assert classify_request_type("Help me fill out Form I-485") == RequestType.FORM_ASSISTANCE
        assert classify_request_type("Complete the petition for custody") == RequestType.FORM_ASSISTANCE
    
    def test_general_info_fallback(self):
        assert classify_request_type("What is contract law?") == RequestType.GENERAL_INFO


class TestLegalCategoryClassification:
    def test_housing(self):
        assert classify_legal_category("My landlord is evicting me") == LegalCategory.HOUSING
        assert classify_legal_category("Security deposit dispute") == LegalCategory.HOUSING
    
    def test_employment(self):
        assert classify_legal_category("Wrongful termination claim") == LegalCategory.EMPLOYMENT
        assert classify_legal_category("Workplace discrimination") == LegalCategory.EMPLOYMENT
    
    def test_family(self):
        assert classify_legal_category("Child custody modification") == LegalCategory.FAMILY
        assert classify_legal_category("Divorce proceedings") == LegalCategory.FAMILY
    
    def test_criminal(self):
        assert classify_legal_category("Arrested for DUI") == LegalCategory.CRIMINAL
        assert classify_legal_category("Criminal charges filed") == LegalCategory.CRIMINAL
    
    def test_immigration(self):
        assert classify_legal_category("Visa application denied") == LegalCategory.IMMIGRATION
        assert classify_legal_category("Asylum seeker rights") == LegalCategory.IMMIGRATION
    
    def test_other_fallback(self):
        assert classify_legal_category("Random question about law") == LegalCategory.OTHER


class TestJurisdictionDetection:
    def test_california(self):
        assert detect_jurisdiction("California eviction laws") == Jurisdiction.US_CA
        assert detect_jurisdiction("CA tenant rights") == Jurisdiction.US_CA
    
    def test_new_york(self):
        assert detect_jurisdiction("New York employment law") == Jurisdiction.US_NY
        assert detect_jurisdiction("NY landlord tenant") == Jurisdiction.US_NY
    
    def test_texas(self):
        assert detect_jurisdiction("Texas family law") == Jurisdiction.US_TX
    
    def test_uk(self):
        assert detect_jurisdiction("UK employment rights") == Jurisdiction.UK
    
    def test_unknown(self):
        assert detect_jurisdiction("General legal question") == Jurisdiction.UNKNOWN


class TestRiskAssessment:
    def test_critical_risk(self):
        assert assess_risk_level("I have a court date tomorrow", RequestType.DEADLINE_INQUIRY, LegalCategory.CRIMINAL) == RiskLevel.CRITICAL
        assert assess_risk_level("Eviction notice served today", RequestType.GENERAL_INFO, LegalCategory.HOUSING) == RiskLevel.CRITICAL
        assert assess_risk_level("Domestic violence emergency", RequestType.GENERAL_INFO, LegalCategory.FAMILY) == RiskLevel.CRITICAL
    
    def test_high_risk(self):
        assert assess_risk_level("Criminal charge filed against me", RequestType.GENERAL_INFO, LegalCategory.CRIMINAL) == RiskLevel.HIGH
        assert assess_risk_level("Asylum application denied", RequestType.GENERAL_INFO, LegalCategory.IMMIGRATION) == RiskLevel.HIGH
        assert assess_risk_level("Lawsuit served", RequestType.GENERAL_INFO, LegalCategory.CONSUMER) == RiskLevel.HIGH
    
    def test_medium_risk(self):
        assert assess_risk_level("Contract dispute with landlord", RequestType.GENERAL_INFO, LegalCategory.HOUSING) == RiskLevel.MEDIUM
        assert assess_risk_level("Wage theft complaint", RequestType.GENERAL_INFO, LegalCategory.EMPLOYMENT) == RiskLevel.MEDIUM
    
    def test_low_risk(self):
        assert assess_risk_level("What is a lease agreement?", RequestType.GENERAL_INFO, LegalCategory.HOUSING) == RiskLevel.LOW
        assert assess_risk_level("What is contract law?", RequestType.GENERAL_INFO, LegalCategory.OTHER) == RiskLevel.LOW


class TestSourceRetrieval:
    def test_ca_sources(self):
        sources = retrieve_sources("eviction", Jurisdiction.US_CA, LegalCategory.HOUSING)
        assert len(sources) > 0
        assert all(s.verified for s in sources)
        assert any(s.jurisdiction == Jurisdiction.US_CA for s in sources)
    
    def test_federal_sources_included(self):
        sources = retrieve_sources("discrimination", Jurisdiction.US_CA, LegalCategory.EMPLOYMENT)
        assert any(s.jurisdiction == Jurisdiction.US_FEDERAL for s in sources)
    
    def test_unknown_jurisdiction(self):
        sources = retrieve_sources("general question", Jurisdiction.UNKNOWN, LegalCategory.OTHER)
        assert len(sources) == 0


class TestClarificationQuestions:
    def test_jurisdiction_required(self):
        questions = generate_clarification_questions(
            "eviction help", RequestType.GENERAL_INFO, LegalCategory.HOUSING, Jurisdiction.UNKNOWN
        )
        assert any(q.required for q in questions)
        assert any("jurisdiction" in q.question.lower() or "location" in q.question.lower() for q in questions)
    
    def test_deadline_clarification(self):
        questions = generate_clarification_questions(
            "deadline to file", RequestType.DEADLINE_INQUIRY, LegalCategory.CIVIL_RIGHTS, Jurisdiction.US_CA
        )
        assert any("date" in q.question.lower() or "when" in q.question.lower() for q in questions)
    
    def test_eviction_notice_type(self):
        questions = generate_clarification_questions(
            "eviction notice", RequestType.GENERAL_INFO, LegalCategory.HOUSING, Jurisdiction.US_CA
        )
        assert any("notice" in q.question.lower() for q in questions)


class TestSchemas:
    def test_ask_request_validation(self):
        req = AskRequest(question="What are my rights?")
        assert req.question == "What are my rights?"
    
    def test_ask_request_min_length(self):
        with pytest.raises(ValueError):
            AskRequest(question="ab")
    
    def test_ask_request_max_length(self):
        with pytest.raises(ValueError):
            AskRequest(question="x" * 5001)
    
    def test_feedback_request_rating_bounds(self):
        with pytest.raises(ValueError):
            FeedbackRequest(conversation_id="123", rating=0)
        with pytest.raises(ValueError):
            FeedbackRequest(conversation_id="123", rating=6)
        # Valid
        FeedbackRequest(conversation_id="123", rating=5)
    
    def test_legal_response_structure(self):
        resp = LegalResponse(
            request_type=RequestType.GENERAL_INFO,
            risk_level=RiskLevel.LOW,
            legal_category=LegalCategory.OTHER,
            jurisdiction=Jurisdiction.US_FEDERAL,
            summary="Test summary",
            explanation="Test explanation",
            disclaimer=DISCLAIMER
        )
        assert resp.disclaimer == DISCLAIMER
        assert len(resp.disclaimer) > 50


class TestDisclaimer:
    def test_disclaimer_contains_key_elements(self):
        assert "general legal information" in DISCLAIMER.lower()
        assert "not constitute legal advice" in DISCLAIMER.lower()
        assert "attorney" in DISCLAIMER.lower()
        assert "attorney-client" in DISCLAIMER.lower()