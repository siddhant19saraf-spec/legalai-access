import type {
  AskRequest,
  AskResponse,
  FeedbackRequest,
  HealthResponse,
  JurisdictionOption,
  CategoryOption,
} from '@/types';

export type { JurisdictionOption, CategoryOption };

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiError extends Error {
  constructor(
    message: string,
    public code: string,
    public status: number,
    public details?: Record<string, unknown> & { retry_after?: number }
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorData: { error?: string; code?: string; details?: Record<string, unknown> } = {};
    try {
      errorData = await response.json();
    } catch {
      // Ignore JSON parse errors
    }
    throw new ApiError(
      errorData.error || `Request failed with status ${response.status}`,
      errorData.code || 'UNKNOWN_ERROR',
      response.status,
      errorData.details
    );
  }
  return response.json();
}

export async function askQuestion(request: AskRequest): Promise<AskResponse> {
  const response = await fetch(`${API_BASE}/api/v1/ask`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });
  return handleResponse<AskResponse>(response);
}

export async function submitFeedback(request: FeedbackRequest): Promise<{ status: string; message: string }> {
  const response = await fetch(`${API_BASE}/api/v1/feedback`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });
  return handleResponse(response);
}

export async function checkHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE}/api/v1/health`);
  return handleResponse<HealthResponse>(response);
}

export async function getJurisdictions(): Promise<{ jurisdictions: JurisdictionOption[] }> {
  const response = await fetch(`${API_BASE}/api/v1/jurisdictions`);
  return handleResponse(response);
}

export async function getCategories(): Promise<{ categories: CategoryOption[] }> {
  const response = await fetch(`${API_BASE}/api/v1/categories`);
  return handleResponse(response);
}

export { ApiError };