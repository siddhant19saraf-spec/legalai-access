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

  const handlePrintResponse = useCallback(() => {
    window.print();
  }, []);

  const handleExportResponse = useCallback(() => {
    if (!response) return;
    const exportData = {
      jurisdiction: response.jurisdiction,
      summary: response.summary,
      explanation: response.explanation,
      risk_level: response.risk_level,
      legal_category: response.legal_category,
      sources: response.sources.map(s => ({
        title: s.title,
        jurisdiction: s.jurisdiction,
        type: s.type,
        url: s.url,
      })),
      next_steps: response.next_steps,
      disclaimer: response.disclaimer,
      generated_at: response.generated_at,
      information_coverage: response.information_coverage,
      question_quality: response.question_quality,
    };
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `legal-response-${response.jurisdiction}-${new Date().toISOString().slice(0,10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [response]);

  return (
    <div className="min-h-screen bg-slate-950">
      <header className="bg-slate-900/80 border-b border-slate-700/50 sticky top-0 z-40 backdrop-blur-sm">
        <div className="max-w-5xl mx-auto px-4 py-3.5 sm:px-6 lg:px-8" aria-label="Main navigation">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div className="flex items-center gap-3" aria-hidden="true">
              <div className="flex items-center justify-center w-9 h-9 bg-blue-600 rounded-xl glow-blue">
                <svg className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                  <path d="M2 12h20" />
                </svg>
              </div>
              <div>
                <h1 className="text-lg font-bold text-white tracking-tight">LegalAI Access</h1>
                <p className="text-xs text-slate-400">Structured Legal Information</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full ${
                healthStatus === 'healthy'
                  ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                  : healthStatus === 'unhealthy'
                  ? 'bg-red-500/20 text-red-300 border border-red-500/30'
                  : 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30'
              }`}>
                <span className={`w-1.5 h-1.5 rounded-full ${healthStatus === 'healthy' ? 'bg-purple-400' : healthStatus === 'unhealthy' ? 'bg-red-400' : 'bg-yellow-400'}`} aria-hidden="true" />
                {healthStatus === 'healthy' ? 'Legal Information Mode' : healthStatus === 'unhealthy' ? 'Service Unavailable' : 'Connecting…'}
              </span>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-6 sm:px-6 lg:px-8" id="main-content">
        <PersistentDisclaimer />

        {(!response && !isLoading) || showNewQuestion ? (
            <section className="space-y-6" aria-labelledby="hero-heading">
              <header className="text-center py-4" id="hero-heading">
                <p className="text-xs font-semibold text-blue-400 uppercase tracking-wider mb-2">
                  LEGAL INFORMATION ASSISTANT
                </p>
                <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white tracking-tight leading-tight">
                  Understand Your{' '}
                  <span className="text-blue-400">Legal Situation</span>{' '}
                  Clearly.
                </h2>
                <p className="mt-3 text-base text-slate-400 max-w-2xl mx-auto leading-relaxed">
                  Structured, jurisdiction-aware legal information with risk signals, relevant sources, and practical next steps.
                </p>
                <div className="mt-4 flex items-center justify-center gap-2 flex-wrap text-sm text-slate-500">
                  <span className="px-3 py-1 bg-blue-500/10 text-blue-300 rounded-full border border-blue-500/20">Question Quality</span>
                  <span className="text-slate-600" aria-hidden="true">•</span>
                  <span className="px-3 py-1 bg-blue-500/10 text-blue-300 rounded-full border border-blue-500/20">Risk Assessment</span>
                  <span className="text-slate-600" aria-hidden="true">•</span>
                  <span className="px-3 py-1 bg-blue-500/10 text-blue-300 rounded-full border border-blue-500/20">Source Transparency</span>
                  <span className="text-slate-600" aria-hidden="true">•</span>
                  <span className="px-3 py-1 bg-blue-500/10 text-blue-300 rounded-full border border-blue-500/20">Actionable Next Steps</span>
                </div>
              </header>

              {/* Trust/Safety Panel */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 max-w-2xl mx-auto">
                <div className="p-3 bg-slate-900/60 border border-slate-700/50 rounded-xl text-center">
                  <div className="text-xs font-semibold text-blue-300 mb-1">General Legal Information</div>
                  <div className="text-xs text-slate-500">Not legal advice</div>
                </div>
                <div className="p-3 bg-slate-900/60 border border-slate-700/50 rounded-xl text-center">
                  <div className="text-xs font-semibold text-purple-300 mb-1">Privacy First</div>
                  <div className="text-xs text-slate-500">Avoid unnecessary sensitive info</div>
                </div>
                <div className="p-3 bg-slate-900/60 border border-slate-700/50 rounded-xl text-center">
                  <div className="text-xs font-semibold text-green-300 mb-1">Jurisdiction Aware</div>
                  <div className="text-xs text-slate-500">Select or detect location</div>
                </div>
              </div>

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
                  <section aria-labelledby="export-heading" className="pt-6 border-t border-gray-200 dark:border-gray-700">
                    <h3 id="export-heading" className="text-lg font-semibold text-gray-900 mb-3">Response Actions</h3>
                    <div className="flex flex-wrap gap-3">
                      <Button variant="secondary" onClick={handleCopyResponse}>
                        Copy Response
                      </Button>
                      <Button variant="secondary" onClick={handlePrintResponse}>
                        Print
                      </Button>
                      <Button variant="secondary" onClick={handleExportResponse}>
                        Download JSON
                      </Button>
                    </div>
                  </section>
                  <section aria-labelledby="privacy-heading" className="pt-4 border-t border-gray-200 dark:border-gray-700">
                    <h3 id="privacy-heading" className="sr-only">Privacy Notice</h3>
                    <div className="p-4 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl">
                      <div className="flex items-start gap-3">
                           <svg className="flex-shrink-0 mt-0.5 h-5 w-5 text-slate-400" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                           <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                         </svg>
                         <div>
                           <h4 className="text-sm font-semibold text-white">Privacy Notice</h4>
                           <p className="mt-1 text-sm text-slate-400">
                             Do not enter unnecessary sensitive personal information such as passwords, financial credentials, government ID numbers, or private medical information. Questions are not saved as a permanent legal record by this interface.
                           </p>
                         </div>
                      </div>
                    </div>
                  </section>
<div className="pt-6 border-t border-slate-700/50 flex justify-center">
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

        <footer className="mt-16 pt-8 border-t border-slate-700/50 text-center">
           <div className="space-y-2">
             <p className="text-sm text-slate-500">
               LegalAI Access — Providing structured legal information.
             </p>
             <p className="text-xs text-slate-600">
               This platform provides general legal information only, not legal advice. Consult a qualified attorney for matters affecting your rights, liberty, or finances.
             </p>
           </div>
         </footer>
      </main>
    </div>
  );
}
