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
        assert data["provider"] in ("OpenAIProvider", "AnthropicProvider", "MockProvider")
        assert "success" in data
        assert "error_category" in data
        assert data["error_category"] in (
            None, "auth", "rate_limit_or_quota", "network",
            "not_found", "bad_request", "runtime_config", "server_error",
            "unknown", "no_valid_key",
        )
        assert "sk-" not in response.text
        assert "Traceback" not in response.text
        assert "site-packages" not in response.text

    async def test_diagnostic_exposes_no_secret_fields(self, client):
        response = await client.get("/api/v1/ai-diagnostic")
        data = response.json()
        for forbidden in ("api_key", "key", "message", "detail", "traceback"):
            assert forbidden not in data


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