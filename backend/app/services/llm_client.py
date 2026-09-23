import asyncio
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None
    latency_ms: int = 0


@dataclass
class LLMMessage:
    role: str
    content: str


class LLMProvider(ABC):
    @abstractmethod
    async def complete(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.1,
        max_tokens: int = 2000,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        pass


def normalize_api_key(api_key: Optional[str]) -> str:
    if not api_key or not isinstance(api_key, str):
        return ""
    k = api_key.strip()
    if len(k) >= 2 and k[0] == k[-1] and k[0] in ('"', "'"):
        k = k[1:-1].strip()
    return k.strip('"').strip("'").strip()


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = normalize_api_key(api_key)
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                raise RuntimeError("openai package not installed. Run: pip install openai")
        return self._client

    async def complete(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.1,
        max_tokens: int = 2000,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        import time
        start = time.time()
        
        client = self._get_client()
        
        formatted_messages = [{"role": m.role, "content": m.content} for m in messages]
        
        kwargs = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if response_format:
            kwargs["response_format"] = response_format
        
        response = await client.chat.completions.create(**kwargs)
        
        latency_ms = int((time.time() - start) * 1000)
        
        usage = None
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        
        return LLMResponse(
            content=response.choices[0].message.content or "",
            model=self.model,
            usage=usage,
            latency_ms=latency_ms,
        )

    def get_model_name(self) -> str:
        return self.model


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307"):
        self.api_key = normalize_api_key(api_key)
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic
                self._client = AsyncAnthropic(api_key=self.api_key)
            except ImportError:
                raise RuntimeError("anthropic package not installed. Run: pip install anthropic")
        return self._client

    async def complete(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.1,
        max_tokens: int = 2000,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        import time
        start = time.time()
        
        client = self._get_client()
        
        system_message = None
        user_messages = []
        
        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                user_messages.append({"role": msg.role, "content": msg.content})
        
        kwargs = {
            "model": self.model,
            "messages": user_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if system_message:
            kwargs["system"] = system_message
        
        if response_format and response_format.get("type") == "json_object":
            kwargs["messages"].append({
                "role": "user",
                "content": "Respond with valid JSON only."
            })
        
        response = await client.messages.create(**kwargs)
        
        latency_ms = int((time.time() - start) * 1000)
        
        content = ""
        for block in response.content:
            if block.type == "text":
                content += block.text
        
        usage = None
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            }
        
        return LLMResponse(
            content=content,
            model=self.model,
            usage=usage,
            latency_ms=latency_ms,
        )

    def get_model_name(self) -> str:
        return self.model


class MockProvider(LLMProvider):
    """Mock provider for testing without API keys"""
    
    def __init__(self, model: str = "mock-model"):
        self.model = model
        self.call_count = 0

    async def complete(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.1,
        max_tokens: int = 2000,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        self.call_count += 1
        await asyncio.sleep(0.01)  # Simulate network latency
        
        last_user_message = ""
        for msg in reversed(messages):
            if msg.role == "user":
                last_user_message = msg.content
                break
        
        # Generate a structured mock response based on the prompt
        if "RESPONSE FORMAT (JSON)" in last_user_message:
            return LLMResponse(
                content='{"summary": "Mock legal information summary for your question.", "explanation": "This is a mock response for testing. In production, this would be generated by the actual LLM with proper legal analysis.", "next_steps": ["Consult with a qualified attorney", "Gather relevant documents", "Contact legal aid if needed"], "escalation_guidance": null, "uncertainty_notes": ["Mock response - not real legal advice", "Laws vary by jurisdiction"]}',
                model=self.model,
                usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
                latency_ms=10,
            )
        
        return LLMResponse(
            content="Mock response for: " + last_user_message[:100],
            model=self.model,
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            latency_ms=10,
        )

    def get_model_name(self) -> str:
        return self.model


class LLMClient:
    """Main client for interacting with LLM providers with resilience"""
    
    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        timeout_seconds: float = 30.0,
        max_retries: int = 2,
        retry_delay_seconds: float = 1.0,
    ):
        self.provider = provider
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds
        
        if provider is None:
            self.provider = self._create_default_provider()

    def _create_default_provider(self) -> LLMProvider:
        openai_key = normalize_api_key(settings.openai_api_key)
        anthropic_key = normalize_api_key(settings.anthropic_api_key)

        is_valid_openai = bool(openai_key) and not openai_key.startswith("test-") and len(openai_key) > 20
        is_valid_anthropic = bool(anthropic_key) and not anthropic_key.startswith("test-") and len(anthropic_key) > 20

        if is_valid_openai:
            return OpenAIProvider(openai_key, settings.openai_model)
        elif is_valid_anthropic:
            return AnthropicProvider(anthropic_key, settings.anthropic_model)
        else:
            logger.warning("No valid AI provider API key configured, using mock provider")
            return MockProvider()

    async def complete_with_retry(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.1,
        max_tokens: int = 2000,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                response = await asyncio.wait_for(
                    self.provider.complete(
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        response_format=response_format,
                    ),
                    timeout=self.timeout_seconds,
                )
                
                if attempt > 0:
                    logger.info(f"LLM request succeeded on retry {attempt}")
                
                return response
                
            except asyncio.TimeoutError:
                last_error = TimeoutError(f"LLM request timed out after {self.timeout_seconds}s")
                logger.warning(f"LLM request timeout (attempt {attempt + 1}/{self.max_retries + 1})")
                
            except Exception as e:
                last_error = e
                logger.warning(f"LLM request failed (attempt {attempt + 1}/{self.max_retries + 1}): {type(e).__name__}: {e}")
            
            if attempt < self.max_retries:
                await asyncio.sleep(self.retry_delay_seconds * (attempt + 1))
        
        logger.error(f"LLM request failed after {self.max_retries + 1} attempts")
        raise last_error or RuntimeError("LLM request failed")


def get_llm_client() -> LLMClient:
    """Factory function for dependency injection"""
    return LLMClient()


async def close_llm_client():
    """Cleanup function for provider clients"""
    pass