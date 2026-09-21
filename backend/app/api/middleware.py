import uuid
import time
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests: int = 30, window_seconds: int = 60):
        super().__init__(app)
        self.requests = requests
        self.window_seconds = window_seconds
        self.clients: Dict[str, list] = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/healthz", "/api/v1/health", "/api/v1/healthz"]:
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        if forwarded := request.headers.get("X-Forwarded-For"):
            client_ip = forwarded.split(",")[0].strip()
        
        now = time.time()
        # Clean old entries
        self.clients[client_ip] = [
            timestamp for timestamp in self.clients[client_ip]
            if now - timestamp < self.window_seconds
        ]
        
        # Check limit
        if len(self.clients[client_ip]) >= self.requests:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "code": "RATE_LIMIT_EXCEEDED",
                    "details": {
                        "limit": self.requests,
                        "window_seconds": self.window_seconds,
                        "retry_after": int(self.window_seconds - (now - self.clients[client_ip][0]))
                    }
                },
                headers={"Retry-After": str(self.window_seconds)}
            )
        
        # Record request
        self.clients[client_ip].append(now)
        
        response = await call_next(request)
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.requests)
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, self.requests - len(self.clients[client_ip]))
        )
        response.headers["X-RateLimit-Reset"] = str(int(now + self.window_seconds))
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # CSP - restrictive but allows necessary resources
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' http://localhost:8000 http://127.0.0.1:8000; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        
        # HSTS for production (only if HTTPS)
        # response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """Basic input validation and sanitization"""
    
    MAX_BODY_SIZE = 1024 * 1024  # 1MB
    
    async def dispatch(self, request: Request, call_next):
        # Check content length
        content_length = request.headers.get("Content-Length")
        if content_length and int(content_length) > self.MAX_BODY_SIZE:
            return JSONResponse(
                status_code=413,
                content={
                    "error": "Request body too large",
                    "code": "PAYLOAD_TOO_LARGE",
                    "details": {"max_size_bytes": self.MAX_BODY_SIZE}
                }
            )
        
        return await call_next(request)