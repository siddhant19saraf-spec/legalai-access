'use client';

import { Component, ErrorInfo, ReactNode, Fragment } from 'react';
import { Button, PrimaryButton } from './AccessibleComponents';

export type ErrorBoundaryProps = {
  fallback?: React.ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  fallbackRender?: (error: Error, resetErrorBoundary: () => void) => React.ReactNode;
  children?: React.ReactNode;
};

export type ErrorBoundaryState = {
  hasError: boolean;
  error: Error | null;
};

export default class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = {
    hasError: false,
    error: null,
  };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.props.onError?.(error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <Fragment>
          <div className="min-h-[300px] flex items-center justify-center p-6">
            <div className="max-w-md w-full text-center p-6 bg-white border border-gray-200 rounded-lg">
              <svg
                className="mx-auto h-12 w-12 text-red-500"
                viewBox="0 0 20 20"
                fill="currentColor"
                aria-hidden="true"
              >
                <path
                  fillRule="evenodd"
                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                  clipRule="evenodd"
                />
              </svg>
              <h2 className="mt-4 text-lg font-medium text-gray-900">Something went wrong</h2>
              <p className="mt-2 text-sm text-gray-600">
                We encountered an unexpected error. Please try again or start a new question.
              </p>
              {this.state.error && (
                <details className="mt-4 text-left">
                  <summary className="text-sm text-gray-500 cursor-pointer">Error details</summary>
                  <pre className="mt-2 p-3 bg-gray-100 rounded text-xs text-gray-700 overflow-auto max-h-32">
                    {this.state.error.message}
                    {this.state.error.stack && `\n\n${this.state.error.stack}`}
                  </pre>
                </details>
              )}
              <div className="mt-6 flex items-center justify-center gap-3">
                <PrimaryButton onClick={this.handleRetry}>
                  Try Again
                </PrimaryButton>
                <Button
                  variant="secondary"
                  onClick={() => window.location.reload()}
                >
                  Reload Page
                </Button>
              </div>
            </div>
          </div>
        </Fragment>
      );
    }
  }
}

export { ErrorBoundary };