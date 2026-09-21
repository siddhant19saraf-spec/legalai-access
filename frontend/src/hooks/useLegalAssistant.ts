import { useState, useCallback, useRef } from 'react';
import { askQuestion, submitFeedback, ApiError } from '@/lib/api';
import type { AskRequest, AskResponse, LegalResponse, FeedbackRequest } from '@/types';

interface UseLegalAssistantReturn {
  response: LegalResponse | null;
  conversationId: string | null;
  isLoading: boolean;
  error: ApiError | null;
  ask: (question: string, jurisdiction?: string, context?: string) => Promise<void>;
  clearResponse: () => void;
  sendFeedback: (rating: number, comment?: string, issueType?: string) => Promise<void>;
  feedbackSent: boolean;
  feedbackError: ApiError | null;
}

export function useLegalAssistant(): UseLegalAssistantReturn {
  const [response, setResponse] = useState<LegalResponse | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [feedbackSent, setFeedbackSent] = useState(false);
  const [feedbackError, setFeedbackError] = useState<ApiError | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const ask = useCallback(async (question: string, jurisdiction?: string, context?: string) => {
    // Cancel any in-flight request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    setIsLoading(true);
    setError(null);
    setFeedbackSent(false);
    setFeedbackError(null);

    try {
      const request: AskRequest = {
        question: question.trim(),
        jurisdiction: jurisdiction as AskRequest['jurisdiction'] | undefined,
        context: context?.trim() || undefined,
        conversation_id: conversationId || undefined,
      };

      const result = await askQuestion(request);
      setResponse(result.response);
      setConversationId(result.conversation_id);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err);
      } else {
        setError(new ApiError('An unexpected error occurred', 'UNKNOWN_ERROR', 500));
      }
      setResponse(null);
    } finally {
      setIsLoading(false);
    }
  }, [conversationId]);

  const clearResponse = useCallback(() => {
    setResponse(null);
    setConversationId(null);
    setError(null);
    setFeedbackSent(false);
    setFeedbackError(null);
  }, []);

  const sendFeedback = useCallback(async (rating: number, comment?: string, issueType?: string) => {
    if (!conversationId) return;
    
    const clampedRating = Math.max(1, Math.min(5, Math.round(rating)));

    setFeedbackError(null);
    try {
      const request: FeedbackRequest = {
        conversation_id: conversationId,
        rating: clampedRating,
        comment: comment?.trim(),
        issue_type: issueType,
      };
      await submitFeedback(request);
      setFeedbackSent(true);
    } catch (err) {
      if (err instanceof ApiError) {
        setFeedbackError(err);
      } else {
        setFeedbackError(new ApiError('Failed to submit feedback', 'UNKNOWN_ERROR', 500));
      }
    }
  }, [conversationId]);

  return {
    response,
    conversationId,
    isLoading,
    error,
    ask,
    clearResponse,
    sendFeedback,
    feedbackSent,
    feedbackError,
  };
}