import json
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Deque, Dict, List, Optional, Tuple

from app.models.schemas import (
    Jurisdiction, RiskLevel, RequestType, LegalCategory,
    Source, LegalResponse
)

logger = logging.getLogger(__name__)


@dataclass
class ConversationMessage:
    """A single message in the conversation"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Legal-specific metadata
    risk_level: Optional[RiskLevel] = None
    legal_category: Optional[LegalCategory] = None
    jurisdiction: Optional[Jurisdiction] = None
    request_type: Optional[RequestType] = None
    sources: List[Source] = field(default_factory=list)


@dataclass
class ConversationContext:
    """Managed conversation context for legal queries"""
    conversation_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    messages: Deque[ConversationMessage] = field(default_factory=lambda: deque(maxlen=20))
    current_jurisdiction: Optional[Jurisdiction] = None
    current_legal_category: Optional[LegalCategory] = None
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    
    # Legal context tracking
    active_legal_topics: List[str] = field(default_factory=list)
    pending_clarifications: List[str] = field(default_factory=list)
    risk_escalation_count: int = 0
    
    def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        risk_level: Optional[RiskLevel] = None,
        legal_category: Optional[LegalCategory] = None,
        jurisdiction: Optional[Jurisdiction] = None,
        request_type: Optional[RequestType] = None,
        sources: Optional[List[Source]] = None,
    ):
        """Add a message to the conversation"""
        message = ConversationMessage(
            role=role,
            content=content,
            metadata=metadata or {},
            risk_level=risk_level,
            legal_category=legal_category,
            jurisdiction=jurisdiction,
            request_type=request_type,
            sources=sources or [],
        )
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
        
        # Update context from legal metadata
        if jurisdiction:
            self.current_jurisdiction = jurisdiction
        if legal_category:
            self.current_legal_category = legal_category
            if legal_category.value not in self.active_legal_topics:
                self.active_legal_topics.append(legal_category.value)
        
        if risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            self.risk_escalation_count += 1
    
    def get_recent_messages(self, limit: int = 5) -> List[ConversationMessage]:
        """Get the most recent messages"""
        return list(self.messages)[-limit:]
    
    def get_context_for_llm(self, max_messages: int = 5) -> List[Dict[str, str]]:
        """
        Get formatted messages for LLM context.
        Only includes recent messages to avoid context pollution.
        """
        recent = self.get_recent_messages(max_messages)
        return [
            {"role": msg.role, "content": msg.content}
            for msg in recent
        ]
    
    def get_legal_context_summary(self) -> Dict[str, Any]:
        """Get a summary of legal context for the current conversation"""
        return {
            "conversation_id": self.conversation_id,
            "message_count": len(self.messages),
            "current_jurisdiction": self.current_jurisdiction.value if self.current_jurisdiction else None,
            "current_legal_category": self.current_legal_category.value if self.current_legal_category else None,
            "active_legal_topics": self.active_legal_topics,
            "risk_escalation_count": self.risk_escalation_count,
            "pending_clarifications": self.pending_clarifications,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    def is_stale(self, max_age_hours: int = 24) -> bool:
        """Check if conversation is stale"""
        age = datetime.utcnow() - self.updated_at
        return age > timedelta(hours=max_age_hours)


class ConversationManager:
    """Manages conversation contexts with in-memory storage"""
    
    def __init__(
        self,
        max_conversations: int = 1000,
        max_age_hours: int = 24,
        cleanup_interval_minutes: int = 60,
    ):
        self.max_conversations = max_conversations
        self.max_age_hours = max_age_hours
        self.conversations: Dict[str, ConversationContext] = {}
        self._cleanup_interval = cleanup_interval_minutes
    
    def get_or_create(self, conversation_id: str) -> ConversationContext:
        """Get existing conversation or create new one"""
        if conversation_id not in self.conversations:
            self._maybe_cleanup()
            
            if len(self.conversations) >= self.max_conversations:
                self._evict_oldest()
            
            self.conversations[conversation_id] = ConversationContext(
                conversation_id=conversation_id
            )
            logger.info(f"Created new conversation: {conversation_id}")
        
        return self.conversations[conversation_id]
    
    def get(self, conversation_id: str) -> Optional[ConversationContext]:
        """Get conversation if exists"""
        return self.conversations.get(conversation_id)
    
    def delete(self, conversation_id: str) -> bool:
        """Delete a conversation"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        return False
    
    def add_user_message(
        self,
        conversation_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConversationContext:
        """Add a user message to conversation"""
        context = self.get_or_create(conversation_id)
        context.add_message("user", content, metadata)
        return context
    
    def add_assistant_message(
        self,
        conversation_id: str,
        content: str,
        response: Optional[LegalResponse] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConversationContext:
        """Add an assistant message with legal response metadata"""
        context = self.get_or_create(conversation_id)
        
        risk_level = response.risk_level if response else None
        legal_category = response.legal_category if response else None
        jurisdiction = response.jurisdiction if response else None
        request_type = response.request_type if response else None
        sources = response.sources if response else None
        
        context.add_message(
            role="assistant",
            content=content,
            metadata=metadata,
            risk_level=risk_level,
            legal_category=legal_category,
            jurisdiction=jurisdiction,
            request_type=request_type,
            sources=sources,
        )
        return context
    
    def get_context_for_query(
        self,
        conversation_id: str,
        max_messages: int = 5,
    ) -> Tuple[List[Dict[str, str]], Dict[str, Any]]:
        """
        Get formatted context for a new legal query.
        Returns (llm_messages, legal_context_summary)
        """
        context = self.get(conversation_id)
        if not context:
            return [], {}
        
        llm_messages = context.get_context_for_llm(max_messages)
        legal_summary = context.get_legal_context_summary()
        
        return llm_messages, legal_summary
    
    def add_clarification_pending(self, conversation_id: str, clarification: str):
        """Track pending clarification questions"""
        context = self.get(conversation_id)
        if context:
            context.pending_clarifications.append(clarification)
    
    def clear_clarifications(self, conversation_id: str):
        """Clear pending clarifications after they're answered"""
        context = self.get(conversation_id)
        if context:
            context.pending_clarifications.clear()
    
    def _maybe_cleanup(self):
        """Periodic cleanup of stale conversations"""
        # Simple approach: clean up if we're near capacity
        if len(self.conversations) > self.max_conversations * 0.8:
            self._cleanup_stale()
    
    def _cleanup_stale(self):
        """Remove stale conversations"""
        stale_ids = [
            cid for cid, ctx in self.conversations.items()
            if ctx.is_stale(self.max_age_hours)
        ]
        for cid in stale_ids:
            del self.conversations[cid]
        
        if stale_ids:
            logger.info(f"Cleaned up {len(stale_ids)} stale conversations")
    
    def _evict_oldest(self):
        """Evict oldest conversation when at capacity"""
        if not self.conversations:
            return
        
        oldest_id = min(
            self.conversations.keys(),
            key=lambda cid: self.conversations[cid].updated_at
        )
        del self.conversations[oldest_id]
        logger.info(f"Evicted oldest conversation: {oldest_id}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get conversation statistics"""
        total_messages = sum(len(c.messages) for c in self.conversations.values())
        risk_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        
        for ctx in self.conversations.values():
            for msg in ctx.messages:
                if msg.risk_level:
                    risk_counts[msg.risk_level.value] += 1
        
        return {
            "total_conversations": len(self.conversations),
            "total_messages": total_messages,
            "risk_distribution": risk_counts,
            "memory_usage_estimate_mb": len(self.conversations) * 0.1,  # rough estimate
        }


# Global conversation manager instance
_conversation_manager: Optional[ConversationManager] = None


def get_conversation_manager() -> ConversationManager:
    """Get or create global conversation manager"""
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationManager()
    return _conversation_manager


def create_conversation_manager(
    max_conversations: int = 1000,
    max_age_hours: int = 24,
) -> ConversationManager:
    """Factory function for conversation manager"""
    return ConversationManager(
        max_conversations=max_conversations,
        max_age_hours=max_age_hours,
    )


# Context-aware query builder
class ContextAwareQueryBuilder:
    """Builds queries that incorporate conversation context appropriately"""
    
    def __init__(self, conversation_manager: ConversationManager):
        self.manager = conversation_manager
    
    def build_contextual_prompt(
        self,
        conversation_id: str,
        current_question: str,
        base_prompt: str,
        max_context_messages: int = 3,
    ) -> str:
        """
        Build a prompt that includes relevant conversation context
        without overwhelming the model or leaking sensitive info.
        """
        context = self.manager.get(conversation_id)
        if not context or not context.messages:
            return base_prompt
        
        # Get recent legal context
        recent_messages = context.get_recent_messages(max_context_messages)
        
        # Filter to only include relevant legal context
        legal_context_parts = []
        
        for msg in recent_messages:
            if msg.role == "user" and msg.metadata.get("legal_topic"):
                legal_context_parts.append(
                    f"Previous question: {msg.content[:200]}"
                )
            elif msg.role == "assistant" and msg.legal_category:
                legal_context_parts.append(
                    f"Previous topic: {msg.legal_category.value} "
                    f"(risk: {msg.risk_level.value if msg.risk_level else 'unknown'})"
                )
        
        if not legal_context_parts:
            return base_prompt
        
        # Inject context into prompt
        context_section = "\n".join([
            "CONVERSATION CONTEXT (for reference only):",
            *legal_context_parts,
            "---",
            "CURRENT QUESTION:",
            current_question,
        ])
        
        # Replace the USER QUESTION section in the base prompt
        if "USER QUESTION:" in base_prompt:
            return base_prompt.replace(
                "USER QUESTION: {question}",
                f"USER QUESTION:\n{context_section}"
            ).format(question=current_question)
        
        # Fallback: prepend context
        return f"{context_section}\n\n{base_prompt}"