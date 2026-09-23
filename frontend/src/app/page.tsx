'use client';

import { useState, useEffect, useCallback, Fragment } from 'react';
import { useLegalAssistant } from '@/hooks/useLegalAssistant';
import { QuestionInput } from '@/components/QuestionInput';
import { ResponseDisplay } from '@/components/ResponseDisplay';
import { PersistentDisclaimer } from '@/components/DisclaimerBanner';
import { LoadingSkeleton, ResponseSkeleton, QuestionInputSkeleton } from '@/components/LoadingSkeleton';
import { Button } from '@/components/AccessibleComponents';
import { getJurisdictions, checkHealth, type JurisdictionOption } from '@/lib/api';

export default function HomePage() {
  const {
    response,
    conversationId,
    isLoading,
    error,
    ask,
    clearResponse,
    sendFeedback,
    feedbackSent,
    feedbackError,
  } = useLegalAssistant();

  const [jurisdictions, setJurisdictions] = useState<JurisdictionOption[]>([]);
  const [healthStatus, setHealthStatus] = useState<'checking' | 'healthy' | 'unhealthy'>('checking');
  const [showNewQuestion, setShowNewQuestion] = useState(false);

  useEffect(() => {
    async function loadInitialData() {
      try {
        const [jurisdictionsRes, healthRes] = await Promise.all([
          getJurisdictions(),
          checkHealth(),
        ]);
        setJurisdictions(jurisdictionsRes.jurisdictions);
        setHealthStatus(healthRes.status === 'healthy' ? 'healthy' : 'unhealthy');
      } catch {
        setHealthStatus('unhealthy');
      }
    }
    loadInitialData();
  }, []);

  const handleAsk = useCallback((question: string, jurisdiction: string, context: string) => {
    ask(question, jurisdiction || undefined, context || undefined);
    setShowNewQuestion(false);
  }, [ask]);

  const handleClear = useCallback(() => {
    clearResponse();
    setShowNewQuestion(true);
  }, [clearResponse]);

  const handleFeedback = useCallback((rating: number, comment?: string) => {
    sendFeedback(rating, comment);
  }, [sendFeedback]);

  const handleCopyResponse = useCallback(() => {
    if (!response) return;
    const responseText = [
      `Summary: ${response.summary}`,
      `Explanation: ${response.explanation}`,
      `Next Steps: ${response.next_steps.join('; ')}`,
      response.escalation_guidance ? `Escalation: ${response.escalation_guidance}` : '',
      response.uncertainty_notes.length > 0 ? `Limitations: ${response.uncertainty_notes.join('; ')}` : '',
      `Disclaimer: ${response.disclaimer}`,
    ].filter(Boolean).join('\n\n');

    navigator.clipboard.writeText(responseText).then(() => {
      alert('Response copied to clipboard');
    });
  }, [response]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-40">
        <nav className="max-w-5xl mx-auto px-4 py-4 sm:px-6 lg:px-8" aria-label="Main navigation">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-10 h-10 bg-blue-600 rounded-xl" aria-hidden="true">
                <svg className="w-6 h-6 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                  <path d="M2 12h20" />
                </svg>
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">LegalAI Access</h1>
                <p className="text-xs text-gray-500">AI-powered legal information</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full ${
                healthStatus === 'healthy'
                  ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                  : healthStatus === 'unhealthy'
                  ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                  : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
              }`}>
                <span className={`w-1.5 h-1.5 rounded-full ${healthStatus === 'healthy' ? 'bg-green-500' : healthStatus === 'unhealthy' ? 'bg-red-500' : 'bg-yellow-500'}`} aria-hidden="true" />
                {healthStatus === 'healthy' ? 'Online' : healthStatus === 'unhealthy' ? 'Offline' : 'Connecting...'}
              </span>
            </div>
          </div>
        </nav>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8 sm:px-6 lg:px-8" id="main-content">
        <PersistentDisclaimer />

        {(!response && !isLoading) || showNewQuestion ? (
            <section className="space-y-8" aria-labelledby="hero-heading">
              {/* Hero Section */}
              <header className="text-center py-8">
                <h2 id="hero-heading" className="text-3xl font-bold text-gray-900 sm:text-4xl tracking-tight">
                  Get Clear Legal Information, Tailored to You
                </h2>
                <p className="mt-4 text-lg text-gray-600 max-w-2xl mx-auto">
                  Ask a legal question and receive structured, jurisdiction-aware guidance. This is not legal advice — consult an attorney for your specific situation.
                </p>
              </header>

              <QuestionInput
                onSubmit={handleAsk}
                isLoading={isLoading}
                jurisdictions={jurisdictions}
                error={error?.message}
              />
            </section>
          ) : (
            <Fragment>
              {isLoading ? (
                <section aria-live="polite" aria-label="Loading" className="space-y-6">
                  <div className="text-center py-8">
                    <div className="inline-flex items-center justify-center w-12 h-12 bg-blue-100 rounded-full animate-pulse" aria-hidden="true">
                      <svg className="w-6 h-6 text-blue-600 animate-spin" viewBox="0 0 24 24" fill="none">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                    </div>
                    <p className="mt-4 text-gray-600">Analyzing your legal question...</p>
                  </div>
                  <ResponseSkeleton />
                </section>
              ) : error ? (
                <section aria-live="assertive" className="space-y-6">
                  <div className="p-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl" role="alert">
                    <div className="flex items-start gap-3">
                      <svg className="flex-shrink-0 mt-0.5 h-6 w-6 text-red-600 dark:text-red-400" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                      </svg>
                      <div>
                        <h3 className="text-lg font-semibold text-red-800 dark:text-red-200">Unable to Process Request</h3>
                        <p className="mt-2 text-red-700 dark:text-red-300">{error.message}</p>
                        {error.code === 'RATE_LIMIT_EXCEEDED' && error.details?.retry_after && (
                          <p className="mt-2 text-sm text-red-600 dark:text-red-400">Please try again in {error.details.retry_after} seconds.</p>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="text-center">
                    <Button onClick={() => { clearResponse(); setShowNewQuestion(true); }}>
                      Try Again
                    </Button>
                  </div>
                </section>
              ) : response ? (
                <Fragment>
                  <ResponseDisplay
                    response={response}
                    onFeedback={handleFeedback}
                    feedbackSent={feedbackSent}
                    feedbackError={feedbackError}
                  />
                  <div className="pt-6 border-t border-gray-200 dark:border-gray-700 flex justify-center">
                    <Button
                      variant="secondary"
                      onClick={handleClear}
                      className="w-full sm:w-auto"
                    >
                      Ask Another Question
                    </Button>
                  </div>
                </Fragment>
              ) : null}
            </Fragment>
          )}

        <footer className="mt-16 pt-8 border-t border-gray-200 dark:border-gray-700 text-center">
          <div className="space-y-2">
            <p className="text-sm text-gray-500">
              LegalAI Access — Providing structured legal information powered by AI.
            </p>
            <p className="text-xs text-gray-400">
              This platform provides general legal information only, not legal advice. Consult a qualified attorney for matters affecting your rights, liberty, or finances.
            </p>
          </div>
        </footer>
      </main>
    </div>
  );
}
