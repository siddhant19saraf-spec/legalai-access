import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.api.middleware import RateLimitMiddleware, SecurityHeadersMiddleware, InputSanitizationMiddleware
from app.api.routes import router as api_router


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("Starting LegalAid AI backend...")
    logger.info(f"AI Provider: {'OpenAI' if settings.openai_api_key else 'Anthropic'}")
    logger.info(f"CORS Origins: {settings.cors_origins}")
    yield
    logger.info("Shutting down LegalAid AI backend...")


app = FastAPI(
    title="LegalAid AI API",
    description="AI-powered legal information platform for the Hack2Skill PromptWars challenge",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
    max_age=3600,
)


# Custom middleware (order matters - innermost first)
app.add_middleware(InputSanitizationMiddleware)
app.add_middleware(RateLimitMiddleware, requests=settings.rate_limit_requests, window_seconds=settings.rate_limit_window_seconds)
app.add_middleware(SecurityHeadersMiddleware)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "Invalid request data",
            "code": "VALIDATION_ERROR",
            "details": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "An unexpected error occurred",
            "code": "INTERNAL_ERROR"
        }
    )


# Include API routes
app.include_router(api_router)


# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "LegalAid AI",
        "version": "1.0.0",
        "description": "AI-powered legal information platform",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=settings.log_level.lower() == "debug",
        log_level=settings.log_level.lower()
    )