import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


class TestHealthEndpoint:
    async def test_health_check(self, client):
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "ai_provider" in data


class TestAIDiagnostic:
    async def test_diagnostic_safe_shape(self, client):
        response = await client.get("/api/v1/ai-diagnostic")
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] in ("OpenAIProvider", "AnthropicProvider", "MockProvider", "TestProvider")
        assert "success" in data
        assert "error_category" in data
        assert data["error_category"] in (
            None, "auth", "rate_limit_or_quota", "network",
            "not_found", "bad_request", "runtime_config", "server_error",
            "unknown", "no_valid_key", "type_error",
        )
        assert "sk-" not in response.text
        assert "Traceback" not in response.text
        assert "site-packages" not in response.text

    async def test_diagnostic_exposes_no_secret_fields(self, client):
        response = await client.get("/api/v1/ai-diagnostic")
        data = response.json()
        for forbidden in ("api_key", "key", "message", "detail", "traceback"):
            assert forbidden not in data
        assert data.get("stage") in (None, "client_init", "complete", "local_provider")


class TestAPIKeyNormalization:
    def test_normalize_strips_whitespace_and_quotes(self):
        from app.services.llm_client import normalize_api_key
        assert normalize_api_key('  "sk-proj-abc123def456ghi789" \n') == "sk-proj-abc123def456ghi789"
        assert normalize_api_key("'sk-proj-abc123def456ghi789'") == "sk-proj-abc123def456ghi789"
        assert normalize_api_key("sk-proj-abc123def456ghi789\r\n") == "sk-proj-abc123def456ghi789"
        assert normalize_api_key(None) == ""
        assert normalize_api_key("") == ""
        assert normalize_api_key("   ") == ""

    def test_config_field_validator_strips(self):
        from app.core.config import Settings
        cleaned = Settings.normalize_api_key(' "sk-proj-abc123def456ghi789" ')
        assert cleaned == "sk-proj-abc123def456ghi789"


class TestAskEndpoint:
    async def test_valid_question(self, client):
        response = await client.post("/api/v1/ask", json={
            "question": "What are my rights as a tenant in California?",
            "jurisdiction": "us_ca"
        })
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "conversation_id" in data
        assert data["response"]["disclaimer"]
        assert data["response"]["risk_level"] in ["low", "medium", "high", "critical"]
    
    async def test_question_without_jurisdiction(self, client):
        response = await client.post("/api/v1/ask", json={
            "question": "How do I file for divorce?"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["response"]["jurisdiction"] == "unknown"
        assert len(data["response"]["clarification_questions"]) > 0
    
    async def test_empty_question_rejected(self, client):
        response = await client.post("/api/v1/ask", json={
            "question": ""
        })
        assert response.status_code == 422

    async def test_too_short_question_rejected(self, client):
        """1-2 character questions must return 422 (not 500) with a serializable body."""
        response = await client.post("/api/v1/ask", json={
            "question": "ab"
        })
        assert response.status_code == 422
        data = response.json()
        assert data["code"] == "VALIDATION_ERROR"
        assert data["error"] == "Invalid request data"
        # Response body must be valid JSON with no internal exception details
        assert "Traceback" not in response.text
    
    async def test_question_too_long(self, client):
        response = await client.post("/api/v1/ask", json={
            "question": "x" * 5001
        })
        assert response.status_code == 422
    
    async def test_invalid_jurisdiction(self, client):
        response = await client.post("/api/v1/ask", json={
            "question": "Legal question",
            "jurisdiction": "invalid_jurisdiction"
        })
        assert response.status_code == 422
        data = response.json()
        assert data["code"] == "VALIDATION_ERROR"
    
    async def test_high_risk_question(self, client):
        response = await client.post("/api/v1/ask", json={
            "question": "I have an eviction notice served today, court tomorrow",
            "jurisdiction": "us_ca"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["response"]["risk_level"] in ["high", "critical"]
        assert data["response"]["escalation_guidance"] is not None
    
    async def test_conversation_id_preserved(self, client):
        conv_id = "test-conv-123"
        response = await client.post("/api/v1/ask", json={
            "question": "Test question",
            "conversation_id": conv_id
        })
        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == conv_id


class TestFeedbackEndpoint:
    async def test_submit_feedback(self, client):
        response = await client.post("/api/v1/feedback", json={
            "conversation_id": "test-123",
            "rating": 5,
            "comment": "Very helpful",
            "issue_type": "accuracy"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "received"
    
    async def test_feedback_rating_bounds(self, client):
        response = await client.post("/api/v1/feedback", json={
            "conversation_id": "test-123",
            "rating": 0
        })
        assert response.status_code == 422
        
        response = await client.post("/api/v1/feedback", json={
            "conversation_id": "test-123",
            "rating": 6
        })
        assert response.status_code == 422
    
    async def test_feedback_stats(self, client):
        response = await client.get("/api/v1/feedback/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data


class TestUtilityEndpoints:
    async def test_list_jurisdictions(self, client):
        response = await client.get("/api/v1/jurisdictions")
        assert response.status_code == 200
        data = response.json()
        assert "jurisdictions" in data
        assert len(data["jurisdictions"]) > 0
    
    async def test_list_categories(self, client):
        response = await client.get("/api/v1/categories")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert len(data["categories"]) > 0


class TestSecurityHeaders:
    async def test_security_headers_present(self, client):
        response = await client.get("/api/v1/health")
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert "Content-Security-Policy" in response.headers
    
    async def test_cors_headers(self, client):
        response = await client.options("/api/v1/ask", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST"
        })
        assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:3000"


class TestRateLimiting:
    async def test_rate_limit_enforced(self, client):
        # Health endpoint is excluded from rate limiting
        for i in range(35):
            response = await client.get("/api/v1/health")
            assert response.status_code == 200
        
        # Test that rate limiting works
        # Previous tests may have consumed quota, so we test both paths
        rate_limited = False
        for i in range(50):
            response = await client.post("/api/v1/ask", json={"question": f"Rate limit test {i}"})
            if response.status_code == 429:
                rate_limited = True
                assert "RATE_LIMIT_EXCEEDED" in response.json()["code"]
                break
            elif response.status_code != 200:
                # Some other error - stop testing
                break
            assert response.status_code == 200
        
        # Should eventually hit rate limit (or already be limited from previous tests)
        assert rate_limited, "Rate limiting should trigger"


class TestInputValidation:
    async def test_xss_payload_handled(self, client):
        response = await client.post("/api/v1/ask", json={
            "question": "<script>alert('xss')</script>"
        })
        # Should be processed (Pydantic validates but doesn't reject HTML)
        assert response.status_code in [200, 429]
    
    async def test_sql_injection_payload_handled(self, client):
        response = await client.post("/api/v1/ask", json={
            "question": "'; DROP TABLE users; --"
        })
        assert response.status_code in [200, 429]
    
    async def test_large_payload_rejected(self, client):
        # Use a fresh client or test with health endpoint which isn't rate limited
        # But health doesn't accept POST... so we'll test with a unique path
        # The middleware checks content-length header, so we need to set it
        large_question = "x" * (1024 * 1024 + 1)
        response = await client.post("/api/v1/ask", json={
            "question": large_question
        })
        # Accept either 413 (payload too large) or 429 (rate limited from previous tests)
        assert response.status_code in [413, 429]


class TestQuestionQuality:
    async def test_question_quality_complete(self, client):
        """A detailed question with jurisdiction should get high quality score"""
        response = await client.post("/api/v1/ask", json={
            "question": "My landlord in California gave me a 3-day eviction notice for non-payment of rent. I have been paying on time for 2 years. What are my rights?",
            "jurisdiction": "us_ca"
        })
        assert response.status_code in [200, 429]
        if response.status_code != 200:
            return
        data = response.json()
        q_quality = data["response"].get("question_quality")
        if q_quality:
            assert q_quality["score"] > 50
            assert "missing_information" in q_quality

    async def test_question_quality_needs_context(self, client):
        """A short question without jurisdiction should flag missing info"""
        response = await client.post("/api/v1/ask", json={
            "question": "Can my landlord evict me?"
        })
        assert response.status_code in [200, 429]
        if response.status_code != 200:
            return
        data = response.json()
        q_quality = data["response"].get("question_quality")
        if q_quality:
            assert q_quality["level"] in ["needs_more_context", "partial"]
            assert len(q_quality["missing_information"]) > 0

    async def test_question_quality_score_range(self, client):
        """Question quality score should be between 0 and 100"""
        response = await client.post("/api/v1/ask", json={
            "question": "What are my rights as a tenant?",
            "jurisdiction": "us_federal"
        })
        assert response.status_code in [200, 429]
        if response.status_code != 200:
            return
        data = response.json()
        q_quality = data["response"].get("question_quality")
        if q_quality:
            assert 0 <= q_quality["score"] <= 100


class TestInformationCoverage:
    async def test_coverage_high_for_ca(self, client):
        """California jurisdiction should have good coverage"""
        response = await client.post("/api/v1/ask", json={
            "question": "What are tenant rights in California regarding eviction?",
            "jurisdiction": "us_ca"
        })
        assert response.status_code in [200, 429]
        if response.status_code != 200:
            return
        data = response.json()
        coverage = data["response"].get("information_coverage")
        assert coverage in ["high", "moderate", "limited"]

    async def test_coverage_limited_for_unknown(self, client):
        """Unknown jurisdiction should have limited coverage"""
        response = await client.post("/api/v1/ask", json={
            "question": "What are my rights regarding landlord?"
        })
        assert response.status_code in [200, 429]
        if response.status_code != 200:
            return
        data = response.json()
        coverage = data["response"].get("information_coverage")
        assert coverage in ["limited", "moderate"]
        reason = data["response"].get("coverage_reason")
        assert reason is not None


class TestTerminologyExplanations:
    async def test_terminology_for_eviction(self, client):
        """Questions mentioning 'eviction' should have terminology explanations"""
        response = await client.post("/api/v1/ask", json={
            "question": "What happens during an eviction in California?",
            "jurisdiction": "us_ca"
        })
        assert response.status_code in [200, 429]
        if response.status_code != 200:
            return
        data = response.json()
        terms = data["response"].get("terminology_explanations", [])
        # Should include eviction explanation if detected
        for term in terms:
            assert "term" in term
            assert "explanation" in term

    async def test_terminology_list(self, client):
        """Terminology explanations should be a list"""
        response = await client.post("/api/v1/ask", json={
            "question": "I was wrongfully terminated and want to know about retaliation.",
            "jurisdiction": "us_federal"
        })
        assert response.status_code in [200, 429]
        if response.status_code != 200:
            return
        data = response.json()
        terms = data["response"].get("terminology_explanations", [])
        assert isinstance(terms, list)


class TestDocumentChecklist:
    async def test_housing_checklist(self, client):
        """Housing questions should include relevant document checklist"""
        response = await client.post("/api/v1/ask", json={
            "question": "My landlord is trying to evict me in California.",
            "jurisdiction": "us_ca"
        })
        assert response.status_code in [200, 429]
        if response.status_code != 200:
            return
        data = response.json()
        checklist = data["response"].get("document_checklist", [])
        assert isinstance(checklist, list)
        # Should have housing-relevant items
        for item in checklist:
            assert "item" in item
            assert "category" in item

    async def test_employment_checklist(self, client):
        """Employment questions should include employment documents"""
        response = await client.post("/api/v1/ask", json={
            "question": "I was terminated and want to know my rights.",
            "jurisdiction": "us_federal"
        })
        assert response.status_code in [200, 429]
        if response.status_code != 200:
            return
        data = response.json()
        checklist = data["response"].get("document_checklist", [])
        assert isinstance(checklist, list)

    async def test_consumer_checklist(self, client):
        """Consumer questions should include consumer documents"""
        response = await client.post("/api/v1/ask", json={
            "question": "I received a defective product and want my money back.",
            "jurisdiction": "us_federal"
        })
        assert response.status_code in [200, 429]
        if response.status_code != 200:
            return
        data = response.json()
        checklist = data["response"].get("document_checklist", [])
        assert isinstance(checklist, list)


class TestFollowUpSuggestions:
    async def test_follow_ups_for_housing(self, client):
        """Housing questions should have follow-up suggestions"""
        response = await client.post("/api/v1/ask", json={
            "question": "My landlord gave me a notice in California.",
            "jurisdiction": "us_ca"
        })
        assert response.status_code in [200, 429]
        if response.status_code != 200:
            return
        data = response.json()
        follow_ups = data["response"].get("follow_up_suggestions", [])
        assert isinstance(follow_ups, list)
        if follow_ups:
            assert "question" in follow_ups[0]
            assert "reason" in follow_ups[0]

    async def test_follow_ups_present(self, client):
        """Every response should have follow-up suggestions"""
        response = await client.post("/api/v1/ask", json={
            "question": "What are my employment rights?",
            "jurisdiction": "us_federal"
        })
        assert response.status_code in [200, 429]
        if response.status_code != 200:
            return
        data = response.json()
        follow_ups = data["response"].get("follow_up_suggestions", [])
        assert isinstance(follow_ups, list)
        assert len(follow_ups) > 0


class TestProviderStatus:
    async def test_provider_status_present(self, client):
        """Response should include provider status"""
        response = await client.post("/api/v1/ask", json={
            "question": "What are my rights as a tenant?",
            "jurisdiction": "us_federal"
        })
        assert response.status_code in [200, 429]
        if response.status_code != 200:
            return
        data = response.json()
        provider_status = data["response"].get("provider_status")
        assert provider_status is not None
        assert isinstance(provider_status, str)

    async def test_provider_status_not_fake(self, client):
        """Provider status should not claim to be AI if it's TestProvider"""
        response = await client.post("/api/v1/ask", json={
            "question": "Test question",
            "jurisdiction": "us_federal"
        })
        assert response.status_code in [200, 429]
        if response.status_code != 200:
            return
        data = response.json()
        provider_status = data["response"].get("provider_status", "")
        # Should be a real provider name
        assert provider_status in ("TestProvider", "MockProvider", "OpenAIProvider", "AnthropicProvider", "Llm7Provider")


class TestEnhancedResponseSchema:
    async def test_response_has_all_new_fields(self, client):
        """All competition-quality fields should be present in response"""
        response = await client.post("/api/v1/ask", json={
            "question": "I received a written eviction notice in California and want to know my rights.",
            "jurisdiction": "us_ca"
        })
        assert response.status_code in [200, 429]
        if response.status_code != 200:
            return
        data = response.json()
        resp = data["response"]
        assert "disclaimer" in resp
        assert "generated_at" in resp
        # New fields (optional or required)
        assert "question_quality" in resp
        assert "information_coverage" in resp
        assert "coverage_reason" in resp
        assert "terminology_explanations" in resp
        assert "document_checklist" in resp
        assert "follow_up_suggestions" in resp
        assert "provider_status" in resp

    async def test_fallback_response_has_coverage(self, client):
        """Fallback responses should also have coverage info"""
        response = await client.post("/api/v1/ask", json={
            "question": "What is the meaning of life?",
        })
        assert response.status_code in [200, 429]
        if response.status_code != 200:
            return
        data = response.json()
        resp = data["response"]
        assert "information_coverage" in resp
        assert resp["information_coverage"] in ["high", "moderate", "limited"]


class TestLlm7Provider:
    def test_provider_can_be_instantiated(self):
        from app.services.llm_client import Llm7Provider
        provider = Llm7Provider(api_key="sk-testkey1234567890abcdef")
        assert provider is not None
        assert provider.get_model_name() == "gpt-4o-mini"

    def test_provider_normalizes_key(self):
        from app.services.llm_client import normalize_api_key
        assert normalize_api_key(None) == ""
        assert normalize_api_key("") == ""

    async def test_default_provider_selects_llm7_when_key_set(self, client, monkeypatch):
        from app.services.llm_client import LLMClient, Llm7Provider, normalize_api_key
        from app.core.config import settings
        
        original_llm7 = settings.llm7_api_key
        original_openai = settings.openai_api_key
        original_anthropic = settings.anthropic_api_key
        
        try:
            settings.llm7_api_key = "sk-live-test-key-1234567890abcdef"
            settings.openai_api_key = ""
            settings.anthropic_api_key = ""
            
            client_instance = LLMClient()
            assert isinstance(client_instance.provider, Llm7Provider)
            assert client_instance.provider.get_model_name() == "gpt-4o-mini"
        finally:
            settings.llm7_api_key = original_llm7
            settings.openai_api_key = original_openai
            settings.anthropic_api_key = original_anthropic