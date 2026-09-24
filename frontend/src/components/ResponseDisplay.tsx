'use client';

import { Fragment, useState, useCallback, useMemo } from 'react';
import { Button, SecondaryButton } from './AccessibleComponents';
import { HighRiskNotice } from './HighRiskNotice';
import type { LegalResponse, RiskLevel, Source, CoverageLevel, TerminologyExplanation, DocumentChecklistItem, FollowUpSuggestion, QuestionQuality } from '@/types';

const RISK_CONFIG: Record<RiskLevel, { bg: string; border: string; icon: string; text: string; label: string }> = {
  low: { bg: 'bg-green-50', border: 'border-green-200', icon: 'text-green-600', text: 'text-green-800', label: 'Low Risk' },
  medium: { bg: 'bg-yellow-50', border: 'border-yellow-200', icon: 'text-yellow-600', text: 'text-yellow-800', label: 'Medium Risk' },
  high: { bg: 'bg-orange-50', border: 'border-orange-200', icon: 'text-orange-600', text: 'text-orange-800', label: 'High Risk' },
  critical: { bg: 'bg-red-50', border: 'border-red-200', icon: 'text-red-600', text: 'text-red-800', label: 'Critical Risk' },
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

const SOURCE_TYPE_LABELS: Record<string, string> = {
  statute: 'Statute',
  regulation: 'Regulation',
  case_law: 'Case Law',
  government_publication: 'Government Publication',
  court_rule: 'Court Rule',
  legal_aid_resource: 'Legal Aid Resource',
  unknown: 'Source',
};

const COVERAGE_CONFIG: Record<CoverageLevel, { bg: string; border: string; text: string; label: string }> = {
  high: { bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-800', label: 'High Coverage' },
  moderate: { bg: 'bg-yellow-50', border: 'border-yellow-200', text: 'text-yellow-800', label: 'Moderate Coverage' },
  limited: { bg: 'bg-orange-50', border: 'border-orange-200', text: 'text-orange-800', label: 'Limited Coverage' },
};

const QUALITY_CONFIG: Record<string, { bg: string; border: string; text: string; label: string }> = {
  complete: { bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-800', label: 'Good' },
  partial: { bg: 'bg-yellow-50', border: 'border-yellow-200', text: 'text-yellow-800', label: 'Partial' },
  needs_more_context: { bg: 'bg-orange-50', border: 'border-orange-200', text: 'text-orange-800', label: 'Needs More Context' },
};

function RiskBadge({ riskLevel }: { riskLevel: RiskLevel }) {
  const config = RISK_CONFIG[riskLevel];
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.bg} ${config.text} border ${config.border}`}
      role="status"
      aria-label={`Risk level: ${config.label}`}
    >
      <svg className={`w-3 h-3 mr-1.5 ${config.icon}`} viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
      </svg>
      {config.label}
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

function SectionHeader({ number, title, children }: { number: string; title: string; children?: React.ReactNode }) {
  return (
    <div className="flex items-start gap-3 mb-3">
      <span className="flex-shrink-0 w-7 h-7 rounded-lg bg-blue-100 text-blue-700 text-sm font-semibold flex items-center justify-center" aria-hidden="true">
        {number}
      </span>
      <div>
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        {children}
      </div>
    </div>
  );
}

function AnswerSection({ response }: { response: LegalResponse }) {
  return (
    <div className="space-y-4 animate-slide-up">
      <SectionHeader number="1" title="Answer" />
      <div className="p-5 bg-blue-50 border border-blue-100 rounded-xl">
        <p className="text-gray-800 leading-relaxed">{response.summary}</p>
      </div>
      {response.explanation && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700">Detailed Explanation</h4>
          <div className="prose prose-sm max-w-none text-gray-700">
            {response.explanation.split('\n').map((paragraph, i) => (
              <p key={i} className="mb-3">{paragraph}</p>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// NEW: Question Quality Check Section
function QuestionQualitySection({ quality }: { quality: QuestionQuality | undefined }) {
  if (!quality) return null;

  const config = QUALITY_CONFIG[quality.level] || QUALITY_CONFIG.needs_more_context;

  return (
    <div className="space-y-3 animate-slide-up">
      <SectionHeader number="2" title="Question Quality Check" />
      <div className={`inline-flex items-center px-4 py-2.5 rounded-lg border ${config.bg} ${config.border}`} role="status">
        <span className={`font-semibold ${config.text}`}>{config.label}</span>
        <span className="ml-2 text-sm text-gray-600">({quality.score}/100)</span>
      </div>
      {quality.missing_information.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">Useful details that could improve the response:</h4>
          <ul className="space-y-1" role="list">
            {quality.missing_information.map((item, index) => (
              <li key={index} className="flex items-start gap-2 text-sm text-gray-600">
                <svg className="flex-shrink-0 mt-0.5 h-4 w-4 text-orange-400" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
                {item}
              </li>
            ))}
          </ul>
        </div>
      )}
      <p className="text-xs text-gray-500">You can still continue with your question even if more context would help.</p>
    </div>
  );
}

// NEW: Information Coverage Section
function InformationCoverageSection({ coverage, reason }: { coverage: CoverageLevel | undefined; reason?: string }) {
  if (!coverage) return null;

  const config = COVERAGE_CONFIG[coverage];

  return (
    <div className="space-y-3 animate-slide-up">
      <SectionHeader number="3" title="Information Coverage" />
      <div className={`inline-flex items-center px-4 py-2.5 rounded-lg border ${config.bg} ${config.border}`} role="status">
        <span className={`font-semibold ${config.text}`}>{config.label}</span>
      </div>
      {reason && (
        <p className="text-sm text-gray-600">{reason}</p>
      )}
    </div>
  );
}

// NEW: Why This Response? Section
function WhyThisResponseSection({ response }: { response: LegalResponse }) {
  return (
    <div className="space-y-4 animate-slide-up">
      <SectionHeader number="4" title="Why This Response?" />
      <div className="space-y-2 text-sm text-gray-700">
        <div className="flex items-start gap-2">
          <span className="flex-shrink-0 font-medium text-blue-600">Detected topic:</span>
          <span>{response.legal_category.replace('_', ' ').toUpperCase()}</span>
        </div>
        <div className="flex items-start gap-2">
          <span className="flex-shrink-0 font-medium text-blue-600">Response mode:</span>
          <span>
            {response.provider_status === 'TestProvider' || response.provider_status === 'MockProvider'
              ? 'Deterministic Legal Information Mode'
              : `AI Provider Active (${response.provider_status})`}
          </span>
        </div>
        <div className="flex items-start gap-2">
          <span className="flex-shrink-0 font-medium text-blue-600">Source coverage:</span>
          <span>
            {response.information_coverage === 'high' && 'US Federal + Jurisdiction-specific'}
            {response.information_coverage === 'moderate' && 'Federal source coverage available'}
            {response.information_coverage === 'limited' && 'Coverage may be limited for this jurisdiction'}
            {!response.information_coverage && 'Not specified'}
          </span>
        </div>
        <div className="flex items-start gap-2">
          <span className="flex-shrink-0 font-medium text-blue-600">Risk classification:</span>
          <span>{response.risk_level.replace('_', ' ').toUpperCase()}</span>
        </div>
        {response.sources.length > 0 && (
          <div className="flex items-start gap-2">
            <span className="flex-shrink-0 font-medium text-blue-600">Sources used:</span>
            <span>{response.sources.length} verified source{response.sources.length !== 1 ? 's' : ''}</span>
          </div>
        )}
      </div>
    </div>
  );
}

function KeyPointsSection({ steps }: { steps: string[] }) {
  if (!steps.length) return null;
  return (
    <div className="space-y-3 animate-slide-up">
      <SectionHeader number="5" title="Key Points" />
      <ul className="space-y-2" role="list">
        {steps.map((step, index) => (
          <li key={index} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
            <span className="flex-shrink-0 w-5 h-5 rounded-full bg-blue-100 text-blue-700 text-xs font-medium flex items-center justify-center mt-0.5">
              {index + 1}
            </span>
            <p className="text-sm text-gray-700 mt-0.5">{step}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}

function RiskSection({ riskLevel }: { riskLevel: RiskLevel }) {
  const config = RISK_CONFIG[riskLevel];
  return (
    <div className="animate-slide-up">
      <SectionHeader number="6" title="Risk Level" />
      <div className={`inline-flex items-center px-4 py-2.5 rounded-lg border ${config.bg} ${config.border}`} role="status">
        <svg className={`w-5 h-5 mr-2 ${config.icon}`} viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
        </svg>
        <span className={`font-semibold ${config.text}`}>{config.label}</span>
      </div>
    </div>
  );
}

function JurisdictionSection({ jurisdiction }: { jurisdiction: string }) {
  return (
    <div className="animate-slide-up">
      <SectionHeader number="7" title="Jurisdiction" />
      <div className="inline-flex items-center px-4 py-2.5 rounded-lg border border-gray-200 bg-white">
        <span className="text-sm font-medium text-gray-700">{jurisdiction.replace('_', ' ').toUpperCase()}</span>
      </div>
      <p className="mt-2 text-sm text-gray-500">
        Jurisdiction-specific accuracy may vary. Consult a local attorney for definitive guidance.
      </p>
    </div>
  );
}

function SourcesList({ sources }: { sources: Source[] }) {
  if (!sources.length) {
    return (
      <div className="animate-slide-up">
        <SectionHeader number="8" title="Sources" />
        <div className="p-4 bg-gray-50 border border-gray-200 rounded-xl">
          <p className="text-sm text-gray-600">No verified source was returned for this response.</p>
          <p className="mt-1 text-xs text-gray-500">The response is based on general legal knowledge.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3 animate-slide-up">
      <SectionHeader number="8" title="Sources" />
      <div className="space-y-3" role="list">
        {sources.map((source, index) => (
          <article
            key={`${source.title}-${index}`}
            className="p-4 bg-white border border-gray-200 rounded-xl hover:border-blue-300 transition-colors"
            role="listitem"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap mb-2">
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
                <h4 className="text-sm font-semibold text-gray-900">{source.title}</h4>
                {source.citation && (
                  <p className="mt-1 text-sm text-gray-600 font-mono">{source.citation}</p>
                )}
                {source.excerpt && (
                  <p className="mt-2 text-sm text-gray-700 italic border-l-2 border-gray-200 pl-3">
                    &ldquo;{source.excerpt}&rdquo;
                  </p>
                )}
                {source.url && (
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800 underline mt-2"
                  >
                    View Source
                    <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                      <path d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z" />
                      <path d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-2a1 1 0 10-2 0v2H5V7a1 1 0 011-1h2a1 1 0 100-2H5z" />
                    </svg>
                  </a>
                )}
              </div>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}

// NEW: Document Checklist Section
function DocumentChecklistSection({ items }: { items: DocumentChecklistItem[] }) {
  const [checkedItems, setCheckedItems] = useState<Set<number>>(new Set());

  if (!items.length) return null;

  const toggleItem = (index: number) => {
    setCheckedItems(prev => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  return (
    <div className="space-y-3 animate-slide-up">
      <SectionHeader number="9" title="Documents That May Help" />
      <p className="text-sm text-gray-600 mb-2">Gathering these documents may help clarify your situation:</p>
      <ul className="space-y-2" role="list">
        {items.map((item, index) => (
          <li key={index} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100 transition-colors" onClick={() => toggleItem(index)}>
            <input
              type="checkbox"
              checked={checkedItems.has(index)}
              onChange={() => toggleItem(index)}
              className="mt-1 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              aria-label={item.item}
            />
            <div>
              <p className={`text-sm ${checkedItems.has(index) ? 'text-gray-500 line-through' : 'text-gray-700'}`}>
                {item.item}
              </p>
              <p className="text-xs text-gray-500">{item.category}</p>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

// NEW: Legal Terminology Explainer Section
function TerminologyExplainerSection({ explanations }: { explanations: TerminologyExplanation[] }) {
  const [expandedTerms, setExpandedTerms] = useState<Set<string>>(new Set());

  if (!explanations.length) return null;

  const toggleTerm = (term: string) => {
    setExpandedTerms(prev => {
      const next = new Set(prev);
      if (next.has(term)) {
        next.delete(term);
      } else {
        next.add(term);
      }
      return next;
    });
  };

  return (
    <div className="space-y-3 animate-slide-up">
      <SectionHeader number="10" title="Legal Terminology" />
      <p className="text-sm text-gray-600 mb-2">Some legal terms may appear in this response. Hover or click to understand:</p>
      <div className="flex flex-wrap gap-2">
        {explanations.map((item) => (
          <button
            key={item.term}
            type="button"
            onClick={() => toggleTerm(item.term)}
            className="inline-flex items-center gap-1 px-3 py-1.5 text-sm font-medium bg-indigo-50 text-indigo-800 border border-indigo-200 rounded-lg hover:bg-indigo-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-colors"
            aria-expanded={expandedTerms.has(item.term)}
            aria-label={`What does ${item.term} mean?`}
          >
            {item.term}
            <svg
              className={`w-3 h-3 transition-transform ${expandedTerms.has(item.term) ? 'rotate-180' : ''}`}
              viewBox="0 0 20 20"
              fill="currentColor"
              aria-hidden="true"
            >
              <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        ))}
      </div>
      {expandedTerms.size > 0 && (
        <div className="space-y-2 mt-3" role="list">
          {explanations.filter(e => expandedTerms.has(e.term)).map((item) => (
            <div key={item.term} className="p-3 bg-white border border-indigo-200 rounded-lg" role="listitem">
              <div className="flex items-center gap-2">
                <h4 className="text-sm font-semibold text-indigo-900">{item.term}</h4>
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-50 text-indigo-700 border border-indigo-200">
                  {item.category}
                </span>
              </div>
              <p className="mt-1 text-sm text-gray-700">{item.explanation}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// NEW: Enhanced Next Steps with Checkboxes
function NextStepsSection({ steps }: { steps: string[] }) {
  const [checkedSteps, setCheckedSteps] = useState<Set<number>>(new Set());

  if (!steps.length) return null;

  const toggleStep = (index: number) => {
    setCheckedSteps(prev => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  return (
    <div className="space-y-3 animate-slide-up">
      <SectionHeader number="11" title="Your Next Steps" />
      <p className="text-sm text-gray-600 mb-2">These steps are informational and safe:</p>
      <ol className="space-y-2" role="list">
        {steps.map((step, index) => (
          <li key={index} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100 transition-colors" onClick={() => toggleStep(index)}>
            <input
              type="checkbox"
              checked={checkedSteps.has(index)}
              onChange={() => toggleStep(index)}
              className="mt-1 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              aria-label={`Check step ${index + 1}: ${step}`}
            />
            <p className={`text-sm ${checkedSteps.has(index) ? 'text-gray-500 line-through' : 'text-gray-700'} mt-0.5`}>
              {step}
            </p>
          </li>
        ))}
      </ol>
    </div>
  );
}

// NEW: Follow-up Suggestions Section
function FollowUpSection({ suggestions }: { suggestions: FollowUpSuggestion[] }) {
  if (!suggestions.length) return null;

  return (
    <div className="space-y-3 animate-slide-up">
      <SectionHeader number="12" title="Useful Follow-up Questions" />
      <p className="text-sm text-gray-600 mb-2">These may help you explore further:</p>
      <div className="space-y-2">
        {suggestions.map((suggestion, index) => (
          <button
            key={index}
            type="button"
            className="block w-full text-left p-3 bg-white border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
            onClick={() => {
              const input = document.querySelector('textarea[name="question"]') as HTMLTextAreaElement;
              if (input) {
                input.value = suggestion.question;
                input.focus();
              }
            }}
          >
            <p className="text-sm font-medium text-gray-900">{suggestion.question}</p>
            <p className="text-xs text-gray-500 mt-0.5">{suggestion.reason}</p>
          </button>
        ))}
      </div>
    </div>
  );
}

function EscalationSection({ guidance }: { guidance: string }) {
  if (!guidance) return null;
  return (
    <div className="animate-slide-up">
      <SectionHeader number="13" title="When to Seek Professional Help" />
      <HighRiskNotice riskLevel="high" guidance={guidance} />
    </div>
  );
}

function UncertaintySection({ notes }: { notes: string[] }) {
  if (!notes.length) return null;
  return (
    <div className="space-y-3 animate-slide-up">
      <SectionHeader number="14" title="Limitations & Uncertainties" />
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
    </div>
  );
}

function DisclaimerSection({ disclaimer }: { disclaimer: string }) {
  return (
    <div className="pt-4 border-t border-gray-200 animate-slide-up">
      <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl">
        <div className="flex items-start gap-3">
          <svg className="flex-shrink-0 mt-0.5 h-5 w-5 text-amber-600" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
          <div>
            <h4 className="text-sm font-semibold text-amber-800">Disclaimer</h4>
            <p className="mt-1 text-sm text-amber-700">{disclaimer}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

// NEW: Provider Status Indicator
function ProviderStatus({ providerStatus }: { providerStatus?: string }) {
  if (!providerStatus) return null;

  const isLocal = providerStatus === 'TestProvider' || providerStatus === 'MockProvider';

  return (
    <div className="animate-slide-up">
      <SectionHeader number="0" title="Legal Information Mode" />
      <div className={`inline-flex items-center px-4 py-2.5 rounded-lg border ${
        isLocal
          ? 'bg-purple-50 border-purple-200'
          : 'bg-green-50 border-green-200'
      }`} role="status">
        <span className={`text-sm font-medium ${
          isLocal ? 'text-purple-800' : 'text-green-800'
        }`}>
          {isLocal
            ? 'Deterministic Legal Information Engine'
            : `AI Provider Active: ${providerStatus}`}
        </span>
      </div>
      <p className="mt-2 text-xs text-gray-500">
        {isLocal
          ? 'No API key required. Responses are generated from verified legal sources.'
          : 'External AI provider is active. Responses may include AI-generated analysis.'}
      </p>
    </div>
  );
}

interface ResponseDisplayProps {
  response: LegalResponse;
  onFeedback?: (rating: number, comment?: string, issueType?: string) => void;
  feedbackSent?: boolean;
  feedbackError?: Error | null;
  onCopyResponse?: () => void;
  onPrintResponse?: () => void;
}

export function ResponseDisplay({
  response,
  onFeedback,
  feedbackSent,
  feedbackError,
}: ResponseDisplayProps) {
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedbackRating, setFeedbackRating] = useState(0);
  const [feedbackComment, setFeedbackComment] = useState('');

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
      alert('Response copied to clipboard');
    });
  }, [response]);

  const handlePrintResponse = useCallback(() => {
    window.print();
  }, []);

  return (
    <div className="space-y-8" role="region" aria-label="Legal information response">
      <header className="space-y-4">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <h2 className="text-2xl font-bold text-gray-900">Legal Information</h2>
          <div className="flex items-center gap-2 flex-wrap">
            <MetadataBadges response={response} />
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200">
            <svg className="w-3 h-3 mr-1" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zm0 16a3 3 0 01-3-3h6a3 3 0 01-3 3z" />
            </svg>
            AI-generated
          </span>
          <span className="text-xs text-gray-500">{response.generated_at}</span>
        </div>
      </header>

      {/* Provider Status */}
      <ProviderStatus providerStatus={response.provider_status} />

      {response.risk_level === 'high' || response.risk_level === 'critical' ? (
        <HighRiskNotice
          riskLevel={response.risk_level as 'high' | 'critical'}
          guidance={response.escalation_guidance || 'Please consult with a qualified attorney immediately.'}
        />
      ) : null}

      {/* Question Quality Check */}
      <QuestionQualitySection quality={response.question_quality} />

      {/* Information Coverage */}
      <InformationCoverageSection coverage={response.information_coverage} reason={response.coverage_reason} />

      {/* Why This Response? */}
      <WhyThisResponseSection response={response} />

      <AnswerSection response={response} />
      <KeyPointsSection steps={response.next_steps} />
      <RiskSection riskLevel={response.risk_level} />
      <JurisdictionSection jurisdiction={response.jurisdiction} />
      <SourcesList sources={response.sources} />
      <DocumentChecklistSection items={response.document_checklist} />
      <TerminologyExplainerSection explanations={response.terminology_explanations} />
      <NextStepsSection steps={response.next_steps} />
      <FollowUpSection suggestions={response.follow_up_suggestions} />
      <EscalationSection guidance={response.escalation_guidance || ''} />
      <UncertaintySection notes={response.uncertainty_notes} />
      <DisclaimerSection disclaimer={response.disclaimer} />

      <section aria-labelledby="feedback-heading" className="pt-6 border-t border-gray-200">
        <h3 id="feedback-heading" className="text-lg font-semibold text-gray-900">Was this helpful?</h3>

        {feedbackSent ? (
          <div className="p-4 bg-green-50 border border-green-200 rounded-xl text-green-800" role="status">
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
              <label htmlFor="feedback-comment" className="label">
                Additional Comments (Optional)
              </label>
              <textarea
                id="feedback-comment"
                value={feedbackComment}
                onChange={(e) => setFeedbackComment(e.target.value)}
                rows={3}
                className="input input-default"
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
              <button
                type="submit"
                disabled={feedbackRating === 0}
                className="inline-flex items-center px-4 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Submit Feedback
              </button>
              <button
                type="button"
                onClick={() => setShowFeedback(!showFeedback)}
                className="inline-flex items-center px-4 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
              >
                {showFeedback ? 'Cancel' : 'Skip'}
              </button>
            </div>
          </form>
        )}
      </section>
    </div>
  );
}
