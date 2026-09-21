'use client';

import { Fragment, useState, useCallback } from 'react';
import { SecondaryButton, PrimaryButton, VisuallyHidden, Button } from './AccessibleComponents';
import { HighRiskNotice } from './HighRiskNotice';
import type { LegalResponse, RiskLevel, Source, ClarificationQuestion } from '@/types';

const RISK_COLORS: Record<RiskLevel, { bg: string; text: string; border: string; icon: string }> = {
  low: { bg: 'bg-green-50', text: 'text-green-800', border: 'border-green-200', icon: 'text-green-600' },
  medium: { bg: 'bg-yellow-50', text: 'text-yellow-800', border: 'border-yellow-200', icon: 'text-yellow-600' },
  high: { bg: 'bg-orange-50', text: 'text-orange-800', border: 'border-orange-200', icon: 'text-orange-600' },
  critical: { bg: 'bg-red-50', text: 'text-red-800', border: 'border-red-200', icon: 'text-red-600' },
};

const RISK_LABELS: Record<RiskLevel, string> = {
  low: 'Low Risk',
  medium: 'Medium Risk',
  high: 'High Risk',
  critical: 'Critical Risk',
};

const CATEGORY_LABELS: Record<string, string> = {
  housing: 'Housing',
  employment: 'Employment',
  family: 'Family Law',
  criminal: 'Criminal Law',
  immigration: 'Immigration',
  consumer: 'Consumer Protection',
  civil_rights: 'Civil Rights',
  healthcare: 'Healthcare',
  education: 'Education',
  financial: 'Financial',
  other: 'Other',
};

const REQUEST_TYPE_LABELS: Record<string, string> = {
  general_info: 'General Information',
  procedural_guidance: 'Procedural Guidance',
  rights_explanation: 'Rights Explanation',
  deadline_inquiry: 'Deadline Inquiry',
  document_review: 'Document Review',
  form_assistance: 'Form Assistance',
  escalation_needed: 'Escalation Needed',
  unsupported: 'Unsupported',
};

const SOURCE_TYPE_LABELS: Record<string, string> = {
  statute: 'Statute',
  regulation: 'Regulation',
  case_law: 'Case Law',
  government_publication: 'Government Publication',
  court_rule: 'Court Rule',
  legal_aid_resource: 'Legal Aid Resource',
  unknown: 'Source',
};

function RiskBadge({ riskLevel }: { riskLevel: RiskLevel }) {
  const colors = RISK_COLORS[riskLevel];
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colors.bg} ${colors.text} ${colors.border} border`}
      role="status"
      aria-label={`Risk level: ${RISK_LABELS[riskLevel]}`}
    >
      <svg className={`w-3 h-3 mr-1.5 ${colors.icon}`} viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
      </svg>
      {RISK_LABELS[riskLevel]}
    </span>
  );
}

function MetadataBadges({ response }: { response: LegalResponse }) {
  return (
    <div className="flex flex-wrap gap-2" role="group" aria-label="Response metadata">
      <RiskBadge riskLevel={response.risk_level} />
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-800 border border-blue-200">
        {REQUEST_TYPE_LABELS[response.request_type] || response.request_type}
      </span>
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-50 text-purple-800 border border-purple-200">
        {CATEGORY_LABELS[response.legal_category] || response.legal_category}
      </span>
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-50 text-gray-800 border border-gray-200">
        {response.jurisdiction.replace('_', ' ').toUpperCase()}
      </span>
    </div>
  );
}

function CopyButton({ text, label = 'Copy' }: { text: string; label?: string }) {
  const [copied, setCopied] = useState(false);
  
  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  }, [text]);

  return (
    <Button
      type="button"
      variant="secondary"
      size="sm"
      onClick={handleCopy}
      aria-label={copied ? 'Copied to clipboard' : label}
      className="w-full sm:w-auto"
    >
      {copied ? (
        <>
          <svg className="w-4 h-4 mr-1.5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
          Copied!
        </>
      ) : (
        <>
          <svg className="w-4 h-4 mr-1.5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
            <path d="M8 3a1 1 0 011-1h2a1 1 0 110 2H9a1 1 0 01-1-1z" />
            <path d="M6 3a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2a1 1 0 100 2h2a1 1 0 112 0h2a2 2 0 012 2v8a2 2 0 01-2 2H6a2 2 0 01-2-2V5a2 2 0 012-2h2a1 1 0 100-2H6z" />
          </svg>
          {label}
        </>
      )}
    </Button>
  );
}

function SourcesList({ sources }: { sources: Source[] }) {
  if (!sources.length) {
    return (
      <section aria-labelledby="sources-heading" className="space-y-3">
        <h3 id="sources-heading" className="text-lg font-semibold text-gray-900">Sources</h3>
        <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
          <p className="text-sm text-gray-600">
            No verified legal sources were found for this specific query. The response is based on general legal knowledge.
            For authoritative information, consult official government websites or a qualified attorney.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section aria-labelledby="sources-heading" className="space-y-3">
      <h3 id="sources-heading" className="text-lg font-semibold text-gray-900">Verified Sources ({sources.length})</h3>
      <div className="space-y-3" role="list">
        {sources.map((source, index) => (
          <article
            key={`${source.title}-${index}`}
            className="p-4 bg-white border border-gray-200 rounded-lg hover:border-blue-200 transition-colors"
            role="listitem"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-800 border border-blue-200">
                    {SOURCE_TYPE_LABELS[source.type] || source.type}
                  </span>
                  {source.verified && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-50 text-green-800 border border-green-200">
                      Verified
                    </span>
                  )}
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-50 text-gray-800 border border-gray-200">
                    {source.jurisdiction.replace('_', ' ').toUpperCase()}
                  </span>
                </div>
                <h4 className="mt-2 text-sm font-medium text-gray-900">{source.title}</h4>
                {source.citation && (
                  <p className="mt-1 text-sm text-gray-600 font-mono">{source.citation}</p>
                )}
                {source.excerpt && (
                  <p className="mt-2 text-sm text-gray-700 italic border-l-2 border-gray-200 pl-3">
                    "{source.excerpt}"
                  </p>
                )}
                <div className="mt-3 flex items-center gap-3">
                  {source.url && (
                    <a
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800 underline"
                    >
                      View Source
                      <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                        <path d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z" />
                        <path d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-2a1 1 0 10-2 0v2H5V7a1 1 0 011-1h8a1 1 0 011 1v8a1 1 0 01-1 1H5a1 1 0 01-1-1V7a1 1 0 011-1h2a1 1 0 100-2H5z" />
                      </svg>
                    </a>
                  )}
                  <CopyButton 
                    text={source.url || source.title} 
                    label="Copy source link" 
                  />
                </div>
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function ClarificationQuestions({ questions }: { questions: ClarificationQuestion[] }) {
  if (!questions.length) return null;

  return (
    <section aria-labelledby="clarifications-heading" className="space-y-3">
      <h3 id="clarifications-heading" className="text-lg font-semibold text-gray-900">Clarification Questions ({questions.length})</h3>
      <div className="space-y-3" role="list">
        {questions.map((q, index) => (
          <div
            key={index}
            className="p-4 bg-blue-50 border border-blue-200 rounded-lg"
            role="listitem"
            aria-label={`Clarification question ${index + 1}`}
          >
            <p className="text-sm text-blue-800">{q.question}</p>
            <p className="mt-1 text-xs text-blue-600"><em>Why this helps: </em>{q.reason}</p>
            {q.required && (
              <span className="inline-block mt-1.5 px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-800 rounded">
                Required for accurate answer
              </span>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}

function EscalationGuidance({ guidance }: { guidance: string }) {
  return (
    <section aria-labelledby="escalation-heading" className="space-y-2">
      <h3 id="escalation-heading" className="text-lg font-semibold text-red-800">Immediate Action Recommended</h3>
      <div role="alert" aria-live="assertive" className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <div className="flex items-start gap-3">
          <svg className="flex-shrink-0 mt-0.5 h-5 w-5 text-red-600" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
          <div className="flex-1">
            <h4 className="text-sm font-medium text-red-800">Immediate Action Recommended</h4>
            <p className="mt-1 text-sm text-red-700">{guidance}</p>
          </div>
        </div>
      </div>
    </section>
  );
}

function UncertaintyNotes({ notes }: { notes: string[] }) {
  if (!notes.length) return null;

  return (
    <section aria-labelledby="uncertainty-heading" className="space-y-3">
      <h3 id="uncertainty-heading" className="text-lg font-semibold text-gray-900">Limitations & Uncertainties</h3>
      <ul className="space-y-2" role="list">
        {notes.map((note, index) => (
          <li key={index} className="flex items-start gap-2 text-sm text-gray-600">
            <svg className="flex-shrink-0 mt-0.5 h-4 w-4 text-gray-400" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            {note}
          </li>
        ))}
      </ul>
    </section>
  );
}

function NextSteps({ steps }: { steps: string[] }) {
  if (!steps.length) return null;

  return (
    <section aria-labelledby="next-steps-heading" className="space-y-3">
      <h3 id="next-steps-heading" className="text-lg font-semibold text-gray-900">Practical Next Steps</h3>
      <ol className="space-y-2" role="list">
        {steps.map((step, index) => (
          <li key={index} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
            <span className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 text-blue-700 text-sm font-medium flex items-center justify-center">
              {index + 1}
            </span>
            <p className="text-sm text-gray-700 mt-0.5">{step}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}

interface ResponseDisplayProps {
  response: LegalResponse;
  onFeedback?: (rating: number, comment?: string, issueType?: string) => void;
  feedbackSent?: boolean;
  feedbackError?: Error | null;
  onCopyResponse?: () => void;
}

export function ResponseDisplay({ 
  response, 
  onFeedback, 
  feedbackSent, 
  feedbackError,
  onCopyResponse 
}: ResponseDisplayProps) {
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedbackRating, setFeedbackRating] = useState(0);
  const [feedbackComment, setFeedbackComment] = useState('');
  const [copiedResponse, setCopiedResponse] = useState(false);

  const handleFeedbackSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (feedbackRating > 0 && onFeedback) {
      onFeedback(feedbackRating, feedbackComment);
      setShowFeedback(false);
      setFeedbackRating(0);
      setFeedbackComment('');
    }
  };

  const handleCopyResponse = useCallback(() => {
    const responseText = [
      `Summary: ${response.summary}`,
      `Explanation: ${response.explanation}`,
      `Next Steps: ${response.next_steps.join('; ')}`,
      response.escalation_guidance ? `Escalation: ${response.escalation_guidance}` : '',
      response.uncertainty_notes.length > 0 ? `Limitations: ${response.uncertainty_notes.join('; ')}` : '',
      `Disclaimer: ${response.disclaimer}`,
    ].filter(Boolean).join('\n\n');

    navigator.clipboard.writeText(responseText).then(() => {
      setCopiedResponse(true);
      setTimeout(() => setCopiedResponse(false), 2000);
    });
  }, [response]);

  const fullResponseText = [
    `Summary: ${response.summary}`,
    `Explanation: ${response.explanation}`,
    `Next Steps: ${response.next_steps.join('; ')}`,
    response.escalation_guidance ? `Escalation: ${response.escalation_guidance}` : '',
    response.uncertainty_notes.length > 0 ? `Limitations: ${response.uncertainty_notes.join('; ')}` : '',
    `Disclaimer: ${response.disclaimer}`,
  ].filter(Boolean).join('\n\n');

  return (
    <div className="space-y-6" role="region" aria-label="Legal information response">
      <header className="space-y-3">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <h2 className="text-xl font-semibold text-gray-900">Legal Information</h2>
          <div className="flex items-center gap-2 flex-wrap">
            <MetadataBadges response={response} />
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => {
                navigator.clipboard.writeText(fullResponseText);
                alert('Response copied to clipboard');
              }}
              aria-label="Copy full response to clipboard"
              className="w-full sm:w-auto"
            >
              <svg className="w-4 h-4 mr-1.5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path d="M8 3a1 1 0 011-1h2a1 1 0 110 2H9a1 1 0 01-1-1z" />
                <path d="M6 3a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2a1 1 0 100 2h2a1 1 0 112 0h2a2 2 0 012 2v8a2 2 0 01-2 2H6a2 2 0 01-2-2V7a2 2 0 012-2h2a1 1 0 100-2H6z" />
              </svg>
              Copy Response
            </Button>
          </div>
        </div>
      </header>

      {response.risk_level === 'high' || response.risk_level === 'critical' ? (
        <HighRiskNotice 
          riskLevel={response.risk_level as 'high' | 'critical'} 
          guidance={response.escalation_guidance || 'Please consult with a qualified attorney immediately.'}
        />
      ) : null}

      <section aria-labelledby="summary-heading" className="space-y-2">
        <h3 id="summary-heading" className="text-lg font-semibold text-gray-900">Summary</h3>
        <p className="text-gray-700">{response.summary}</p>
      </section>

      <section aria-labelledby="explanation-heading" className="space-y-2">
        <h3 id="explanation-heading" className="text-lg font-semibold text-gray-900">Detailed Explanation</h3>
        <div className="prose prose-sm max-w-none text-gray-700">
          {response.explanation.split('\n').map((paragraph, i) => (
            <p key={i} className="mb-3">{paragraph}</p>
          ))}
        </div>
      </section>

      <SourcesList sources={response.sources} />
      <ClarificationQuestions questions={response.clarification_questions} />

      {response.escalation_guidance && !['high', 'critical'].includes(response.risk_level) && (
        <EscalationGuidance guidance={response.escalation_guidance} />
      )}

      <NextSteps steps={response.next_steps} />
      <UncertaintyNotes notes={response.uncertainty_notes} />

      <div className="pt-4 border-t border-gray-200">
        <p className="text-xs text-gray-500">{response.disclaimer}</p>
      </div>

      <section aria-labelledby="feedback-heading" className="space-y-4">
        <h3 id="feedback-heading" className="text-lg font-semibold text-gray-900">Was this helpful?</h3>
        
        {feedbackSent ? (
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg text-green-800" role="status">
            Thank you for your feedback! It helps us improve.
          </div>
        ) : (
          <form onSubmit={handleFeedbackSubmit} className="space-y-4">
            <fieldset>
              <legend className="sr-only">Rate this response</legend>
              <div className="flex items-center gap-2" role="radiogroup" aria-label="Rating">
                {[1, 2, 3, 4, 5].map((rating) => (
                  <button
                    key={rating}
                    type="button"
                    role="radio"
                    aria-checked={feedbackRating === rating}
                    onClick={() => setFeedbackRating(rating)}
                    className={`
                      w-10 h-10 rounded-lg border-2 flex items-center justify-center text-sm font-medium
                      transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500
                      ${feedbackRating === rating
                        ? 'bg-blue-600 border-blue-600 text-white'
                        : 'bg-white border-gray-300 text-gray-600 hover:border-blue-400'
                      }
                    `}
                  >
                    {rating}
                  </button>
                ))}
              </div>
            </fieldset>

            <div>
              <label htmlFor="feedback-comment" className="block text-sm font-medium text-gray-700 mb-1.5">
                Additional Comments (Optional)
              </label>
              <textarea
                id="feedback-comment"
                value={feedbackComment}
                onChange={(e) => setFeedbackComment(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="What could we improve? (optional)"
                maxLength={500}
              />
            </div>

            {feedbackError && (
              <div role="alert" className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-800">
                {feedbackError.message}
              </div>
            )}

            <div className="flex items-center gap-3">
              <SecondaryButton
                type="submit"
                disabled={feedbackRating === 0}
                className="w-full sm:w-auto"
              >
                Submit Feedback
              </SecondaryButton>
              <Button
                type="button"
                variant="secondary"
                onClick={() => setShowFeedback(!showFeedback)}
                className="w-full sm:w-auto"
              >
                {showFeedback ? 'Cancel' : 'Skip'}
              </Button>
            </div>
          </form>
        )}
      </section>
    </div>
  );
}