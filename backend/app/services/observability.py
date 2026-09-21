import json
import logging
import time
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar

import structlog

# Context variables for request tracing
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
conversation_id_var: ContextVar[str] = ContextVar("conversation_id", default="")
user_id_var: ContextVar[str] = ContextVar("user_id", default="")

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# Standard logger for compatibility
logger = logging.getLogger(__name__)


@dataclass
class RequestMetrics:
    request_id: str
    endpoint: str
    method: str
    start_time: float
    end_time: Optional[float] = None
    status_code: Optional[int] = None
    latency_ms: Optional[int] = None
    ai_latency_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    risk_level: Optional[str] = None
    legal_category: Optional[str] = None
    jurisdiction: Optional[str] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    
    def finish(self, status_code: int, error: Optional[str] = None):
        self.end_time = time.time()
        self.status_code = status_code
        self.latency_ms = int((self.end_time - self.start_time) * 1000)
        self.error = error
        if error:
            self.error_type = type(error).__name__ if isinstance(error, Exception) else "Error"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "endpoint": self.endpoint,
            "method": self.method,
            "status_code": self.status_code,
            "latency_ms": self.latency_ms,
            "ai_latency_ms": self.ai_latency_ms,
            "tokens_used": self.tokens_used,
            "risk_level": self.risk_level,
            "legal_category": self.legal_category,
            "jurisdiction": self.jurisdiction,
            "error": self.error,
            "error_type": self.error_type,
        }


def get_request_logger() -> structlog.BoundLogger:
    """Get a logger with request context"""
    return structlog.get_logger().bind(
        request_id=request_id_var.get(""),
        conversation_id=conversation_id_var.get(""),
        user_id=user_id_var.get(""),
    )


def set_request_context(
    request_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
    user_id: Optional[str] = None
):
    """Set context variables for request tracing"""
    if request_id:
        request_id_var.set(request_id)
    if conversation_id:
        conversation_id_var.set(conversation_id)
    if user_id:
        user_id_var.set(user_id)


def clear_request_context():
    """Clear context variables"""
    request_id_var.set("")
    conversation_id_var.set("")
    user_id_var.set("")


class ObservabilityMixin:
    """Mixin to add observability to services"""
    
    def _log_ai_request(
        self,
        prompt_length: int,
        model: str,
        risk_level: Optional[str] = None,
        jurisdiction: Optional[str] = None,
    ):
        logger = get_request_logger()
        logger.info(
            "ai_request_started",
            prompt_length=prompt_length,
            model=model,
            risk_level=risk_level,
            jurisdiction=jurisdiction,
        )
    
    def _log_ai_response(
        self,
        latency_ms: int,
        tokens_used: Optional[int] = None,
        success: bool = True,
        error: Optional[str] = None,
    ):
        logger = get_request_logger()
        if success:
            logger.info(
                "ai_request_completed",
                latency_ms=latency_ms,
                tokens_used=tokens_used,
            )
        else:
            logger.error(
                "ai_request_failed",
                latency_ms=latency_ms,
                error=error,
            )
    
    def _log_classification(
        self,
        request_type: str,
        legal_category: str,
        risk_level: str,
        jurisdiction: str,
        confidence: Optional[float] = None,
    ):
        logger = get_request_logger()
        logger.info(
            "request_classified",
            request_type=request_type,
            legal_category=legal_category,
            risk_level=risk_level,
            jurisdiction=jurisdiction,
            confidence=confidence,
        )
    
    def _log_source_retrieval(
        self,
        source_count: int,
        jurisdiction: str,
        legal_category: str,
    ):
        logger = get_request_logger()
        logger.info(
            "sources_retrieved",
            source_count=source_count,
            jurisdiction=jurisdiction,
            legal_category=legal_category,
        )
    
    def _log_validation(
        self,
        passed: bool,
        errors: Optional[list] = None,
        warnings: Optional[list] = None,
    ):
        logger = get_request_logger()
        if passed:
            logger.info("output_validation_passed", warnings=warnings)
        else:
            logger.warning("output_validation_failed", errors=errors, warnings=warnings)
    
    def _log_safety_check(
        self,
        check_type: str,
        passed: bool,
        details: Optional[Dict] = None,
    ):
        logger = get_request_logger()
        if passed:
            logger.info("safety_check_passed", check_type=check_type, details=details)
        else:
            logger.warning("safety_check_failed", check_type=check_type, details=details)
    
    def _log_rate_limit(
        self,
        client_ip: str,
        endpoint: str,
        limit: int,
        remaining: int,
    ):
        logger = get_request_logger()
        logger.warning(
            "rate_limit_approaching",
            client_ip=client_ip,
            endpoint=endpoint,
            limit=limit,
            remaining=remaining,
        )


T = TypeVar("T")


def trace_operation(operation_name: str):
    """Decorator to trace an operation with timing and logging"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            logger = get_request_logger()
            start = time.time()
            request_id = request_id_var.get("")
            
            logger.debug(
                f"operation_started",
                operation=operation_name,
                request_id=request_id,
            )
            
            try:
                result = await func(*args, **kwargs)
                latency = int((time.time() - start) * 1000)
                logger.debug(
                    f"operation_completed",
                    operation=operation_name,
                    latency_ms=latency,
                    request_id=request_id,
                )
                return result
            except Exception as e:
                latency = int((time.time() - start) * 1000)
                logger.error(
                    f"operation_failed",
                    operation=operation_name,
                    latency_ms=latency,
                    error=str(e),
                    error_type=type(e).__name__,
                    request_id=request_id,
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            logger = get_request_logger()
            start = time.time()
            request_id = request_id_var.get("")
            
            logger.debug(
                f"operation_started",
                operation=operation_name,
                request_id=request_id,
            )
            
            try:
                result = func(*args, **kwargs)
                latency = int((time.time() - start) * 1000)
                logger.debug(
                    f"operation_completed",
                    operation=operation_name,
                    latency_ms=latency,
                    request_id=request_id,
                )
                return result
            except Exception as e:
                latency = int((time.time() - start) * 1000)
                logger.error(
                    f"operation_failed",
                    operation=operation_name,
                    latency_ms=latency,
                    error=str(e),
                    error_type=type(e).__name__,
                    request_id=request_id,
                )
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def log_api_request(endpoint: str, method: str, status_code: int, latency_ms: int):
    """Log API request metrics"""
    logger = get_request_logger()
    logger.info(
        "api_request",
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        latency_ms=latency_ms,
    )


def log_ai_request(prompt_length: int, model: str, risk_level: Optional[str] = None, jurisdiction: Optional[str] = None):
    """Log AI request"""
    logger = get_request_logger()
    logger.info(
        "ai_request_started",
        prompt_length=prompt_length,
        model=model,
        risk_level=risk_level,
        jurisdiction=jurisdiction,
    )


def log_ai_response(latency_ms: int, tokens_used: Optional[int] = None, success: bool = True, error: Optional[str] = None):
    """Log AI response"""
    logger = get_request_logger()
    if success:
        logger.info(
            "ai_request_completed",
            latency_ms=latency_ms,
            tokens_used=tokens_used,
        )
    else:
        logger.error(
            "ai_request_failed",
            latency_ms=latency_ms,
            error=error,
        )


def log_classification(request_type: str, legal_category: str, risk_level: str, jurisdiction: str, confidence: Optional[float] = None):
    """Log classification results"""
    logger = get_request_logger()
    logger.info(
        "request_classified",
        request_type=request_type,
        legal_category=legal_category,
        risk_level=risk_level,
        jurisdiction=jurisdiction,
        confidence=confidence,
    )


def log_source_retrieval(source_count: int, jurisdiction: str, legal_category: str):
    """Log source retrieval"""
    logger = get_request_logger()
    logger.info(
        "sources_retrieved",
        source_count=source_count,
        jurisdiction=jurisdiction,
        legal_category=legal_category,
    )


def log_validation(passed: bool, errors: Optional[list] = None, warnings: Optional[list] = None):
    """Log validation result"""
    logger = get_request_logger()
    if passed:
        logger.info("output_validation_passed", warnings=warnings)
    else:
        logger.warning("output_validation_failed", errors=errors, warnings=warnings)


def log_safety_check(check_type: str, passed: bool, details: Optional[Dict] = None):
    """Log safety check"""
    logger = get_request_logger()
    if passed:
        logger.info("safety_check_passed", check_type=check_type, details=details)
    else:
        logger.warning("safety_check_failed", check_type=check_type, details=details)


def log_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    level: str = "error"
):
    """Log error with context"""
    logger = get_request_logger()
    log_method = getattr(logger, level, logger.error)
    log_method(
        "error_occurred",
        error=str(error),
        error_type=type(error).__name__,
        context=context or {},
    )


def create_metrics_collector() -> "MetricsCollector":
    """Factory for metrics collector"""
    return MetricsCollector()


class MetricsCollector:
    """Collects and aggregates metrics for monitoring"""
    
    def __init__(self):
        self._counters: Dict[str, int] = {}
        self._histograms: Dict[str, list] = {}
        self._gauges: Dict[str, float] = {}
    
    def increment(self, name: str, labels: Optional[Dict[str, str]] = None, value: int = 1):
        key = self._make_key(name, labels)
        self._counters[key] = self._counters.get(key, 0) + value
    
    def observe(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        key = self._make_key(name, labels)
        if key not in self._histograms:
            self._histograms[key] = []
        self._histograms[key].append(value)
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        key = self._make_key(name, labels)
        self._gauges[key] = value
    
    def _make_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def get_metrics(self) -> Dict[str, Any]:
        return {
            "counters": self._counters,
            "histograms": {
                k: {
                    "count": len(v),
                    "sum": sum(v),
                    "min": min(v) if v else 0,
                    "max": max(v) if v else 0,
                    "avg": sum(v) / len(v) if v else 0,
                }
                for k, v in self._histograms.items()
            },
            "gauges": self._gauges,
        }
    
    def reset(self):
        self._counters.clear()
        self._histograms.clear()
        self._gauges.clear()


# Global metrics collector instance
metrics = MetricsCollector()