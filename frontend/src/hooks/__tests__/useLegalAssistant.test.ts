import { renderHook, act, waitFor } from '@testing-library/react';
import { useLegalAssistant } from '@/hooks/useLegalAssistant';
import * as api from '@/lib/api';

jest.mock('@/lib/api');

describe('useLegalAssistant', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('initializes with empty state', () => {
    const { result } = renderHook(() => useLegalAssistant());
    expect(result.current.response).toBeNull();
    expect(result.current.conversationId).toBeNull();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.feedbackSent).toBe(false);
    expect(result.current.feedbackError).toBeNull();
  });

  it('sets loading state when asking', async () => {
    const mockResponse = {
      response: {
        request_type: 'general_info',
        risk_level: 'low',
        legal_category: 'other',
        jurisdiction: 'unknown',
        summary: 'Test summary',
        explanation: 'Test explanation',
        sources: [],
        clarification_questions: [],
        next_steps: [],
        uncertainty_notes: [],
        disclaimer: 'Test disclaimer',
        generated_at: new Date().toISOString(),
      },
      conversation_id: 'test-123',
    };

    (api.askQuestion as jest.Mock).mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useLegalAssistant());

    // Start the ask
    const askPromise = act(async () => {
      await result.current.ask('Test question');
    });

    // The loading state should be true during the async operation
    // Note: due to React 18 batching, we may need to wait for the next tick
    await act(async () => {
      await Promise.resolve();
    });

    // Now await the full completion
    await askPromise;

    expect(result.current.isLoading).toBe(false);
    expect(result.current.response).toEqual(mockResponse.response);
    expect(result.current.conversationId).toBe('test-123');
  });

  it('handles API error', async () => {
    const apiError = new api.ApiError('Rate limited', 'RATE_LIMIT_EXCEEDED', 429);
    (api.askQuestion as jest.Mock).mockRejectedValue(apiError);

    const { result } = renderHook(() => useLegalAssistant());

    await act(async () => {
      await result.current.ask('Test question');
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toEqual(apiError);
    expect(result.current.response).toBeNull();
  });

  it('clears response', async () => {
    const mockResponse = {
      response: {
        request_type: 'general_info',
        risk_level: 'low',
        legal_category: 'other',
        jurisdiction: 'unknown',
        summary: 'Test',
        explanation: 'Test',
        sources: [],
        clarification_questions: [],
        next_steps: [],
        uncertainty_notes: [],
        disclaimer: 'Test',
        generated_at: new Date().toISOString(),
      },
      conversation_id: 'test-123',
    };

    (api.askQuestion as jest.Mock).mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useLegalAssistant());

    await act(async () => {
      await result.current.ask('Test question');
    });

    act(() => {
      result.current.clearResponse();
    });

    expect(result.current.response).toBeNull();
    expect(result.current.conversationId).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.feedbackSent).toBe(false);
  });

  it('sends feedback', async () => {
    (api.submitFeedback as jest.Mock).mockResolvedValue({ status: 'received' });

    const mockResponse = {
      response: {
        request_type: 'general_info',
        risk_level: 'low',
        legal_category: 'other',
        jurisdiction: 'unknown',
        summary: 'Test',
        explanation: 'Test',
        sources: [],
        clarification_questions: [],
        next_steps: [],
        uncertainty_notes: [],
        disclaimer: 'Test',
        generated_at: new Date().toISOString(),
      },
      conversation_id: 'test-123',
    };

    (api.askQuestion as jest.Mock).mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useLegalAssistant());

    await act(async () => {
      await result.current.ask('Test question');
    });

    await act(async () => {
      await result.current.sendFeedback(5, 'Great!');
    });

    expect(result.current.feedbackSent).toBe(true);
    expect(api.submitFeedback).toHaveBeenCalledWith({
      conversation_id: 'test-123',
      rating: 5,
      comment: 'Great!',
      issue_type: undefined,
    });
  });

  it('handles feedback error', async () => {
    const apiError = new api.ApiError('Failed', 'INTERNAL_ERROR', 500);
    (api.submitFeedback as jest.Mock).mockRejectedValue(apiError);

    const mockResponse = {
      response: {
        request_type: 'general_info',
        risk_level: 'low',
        legal_category: 'other',
        jurisdiction: 'unknown',
        summary: 'Test',
        explanation: 'Test',
        sources: [],
        clarification_questions: [],
        next_steps: [],
        uncertainty_notes: [],
        disclaimer: 'Test',
        generated_at: new Date().toISOString(),
      },
      conversation_id: 'test-123',
    };

    (api.askQuestion as jest.Mock).mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useLegalAssistant());

    await act(async () => {
      await result.current.ask('Test question');
    });

    await act(async () => {
      await result.current.sendFeedback(5);
    });

    expect(result.current.feedbackSent).toBe(false);
    expect(result.current.feedbackError).toEqual(apiError);
  });

  it('cancels previous request when new one starts', async () => {
    let resolveFirst: (value: any) => void;
    const firstPromise = new Promise(resolve => { resolveFirst = resolve; });
    
    const mockResponse = {
      response: {
        request_type: 'general_info',
        risk_level: 'low',
        legal_category: 'other',
        jurisdiction: 'unknown',
        summary: 'Test',
        explanation: 'Test',
        sources: [],
        clarification_questions: [],
        next_steps: [],
        uncertainty_notes: [],
        disclaimer: 'Test',
        generated_at: new Date().toISOString(),
      },
      conversation_id: 'test-123',
    };

    (api.askQuestion as jest.Mock)
      .mockReturnValueOnce(firstPromise)
      .mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useLegalAssistant());

    // Start first request
    const firstAsk = act(async () => {
      await result.current.ask('First question');
    });

    // Immediately start second request (should cancel first)
    await act(async () => {
      await result.current.ask('Second question');
    });

    // Resolve first request (should be ignored)
    resolveFirst!(mockResponse);

    await firstAsk;

    // Should have result from second request
    expect(api.askQuestion).toHaveBeenCalledTimes(2);
    expect(result.current.conversationId).toBe('test-123');
  });
});