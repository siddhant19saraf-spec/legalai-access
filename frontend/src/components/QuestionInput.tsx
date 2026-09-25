'use client';

import { useState, useCallback, useRef, FormEvent, KeyboardEvent } from 'react';
import { Textarea, Select, PrimaryButton, Button } from './AccessibleComponents';
import type { JurisdictionOption } from '@/types';

interface QuestionInputProps {
  onSubmit: (question: string, jurisdiction: string, context: string) => void;
  isLoading: boolean;
  jurisdictions: JurisdictionOption[];
  error?: string;
}

const EXAMPLE_PROMPTS = [
  "Describe your legal situation in plain language with your location.",
  "I received a notice from my employer and need guidance.",
  "What are my rights regarding a housing dispute?",
];

export function QuestionInput({ onSubmit, isLoading, jurisdictions, error }: QuestionInputProps) {
  const [question, setQuestion] = useState('');
  const [jurisdiction, setJurisdiction] = useState('');
  const [context, setContext] = useState('');
  const [showContext, setShowContext] = useState(false);
  const [questionError, setQuestionError] = useState('');
  const [charCount, setCharCount] = useState(0);
  const textareaRef = useCallback((node: HTMLTextAreaElement | null) => {
    if (node) node.focus();
  }, []);

  const handleSubmit = useCallback((e: FormEvent) => {
    e.preventDefault();
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion) {
      setQuestionError('Please enter a legal question');
      return;
    }
    if (trimmedQuestion.length < 3) {
      setQuestionError('Question must be at least 3 characters');
      return;
    }
    setQuestionError('');
    onSubmit(trimmedQuestion, jurisdiction, context.trim());
  }, [question, jurisdiction, context, onSubmit]);

  const handleKeyDown = useCallback((e: KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      handleSubmit(e as unknown as FormEvent);
    }
  }, [handleSubmit]);

  const handleQuestionChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    setQuestion(value);
    setCharCount(value.length);
    if (questionError) setQuestionError('');
  };

  const isDisabled = isLoading;

  return (
    <form onSubmit={handleSubmit} className="space-y-6" noValidate role="form" aria-label="Legal question form">
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl p-6 shadow-sm">
        <div>
          <label htmlFor="legal-question" className="block text-sm font-semibold text-gray-900 dark:text-white mb-2">
            Your Legal Question
          </label>
          <div className="relative">
            <Textarea
              ref={textareaRef}
              id="legal-question"
              value={question}
              onChange={handleQuestionChange}
              onKeyDown={handleKeyDown}
              placeholder="Describe your legal situation in plain language with your location. Example: 'My landlord gave me a 3-day eviction notice for non-payment in California. What are my options?'"
              rows={6}
              className={`
                w-full px-4 py-3 text-base border rounded-xl resize-y min-h-[160px]
                transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-0
                ${questionError || error
                  ? 'border-red-500 focus:ring-red-500 focus:border-red-500'
                  : 'border-gray-300 dark:border-gray-600 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white'
                }
                ${isDisabled ? 'opacity-50 cursor-not-allowed' : ''}
              `}
              aria-invalid={!!questionError || !!error}
              aria-describedby={questionError ? 'legal-question-error' : error ? 'legal-question-external-error' : 'legal-question-hint'}
              aria-required="true"
              disabled={isDisabled}
              maxLength={5000}
            />
            <div className="absolute bottom-2 right-2 text-xs text-gray-500 dark:text-gray-400 font-mono" aria-hidden="true">
              {charCount} / 5000
            </div>
          </div>
          <p id="legal-question-hint" className="mt-2 text-sm text-gray-600 dark:text-gray-400 flex items-center gap-2" role="status">
            <span>Be specific about your location and situation for better results.</span>
            <kbd className="px-1.5 py-0.5 text-xs bg-gray-100 dark:bg-gray-700 rounded border border-gray-200 dark:border-gray-600 font-mono">Ctrl+Enter</kbd>
            <span className="text-gray-400">to submit</span>
          </p>
          {questionError && (
            <p id="legal-question-error" className="mt-2 text-sm text-red-600 dark:text-red-400" role="alert" aria-live="polite">
              {questionError}
            </p>
          )}
          {error && !questionError && (
            <p id="legal-question-external-error" className="mt-2 text-sm text-red-600 dark:text-red-400" role="alert" aria-live="polite">
              {error}
            </p>
          )}
        </div>

        <div className="pt-4 border-t border-gray-100 dark:border-gray-700">
          <Select
            id="jurisdiction"
            label="Jurisdiction"
            value={jurisdiction}
            onChange={(e) => setJurisdiction(e.target.value)}
            options={jurisdictions}
            placeholder="Auto-detect from question"
            hint="Legal information varies by jurisdiction. Select your state or country for more accurate information."
            disabled={isDisabled}
          >
            <option value="">Auto-detect from question</option>
          </Select>
        </div>

        <details className="group" open={showContext}>
          <summary
            className="cursor-pointer select-none flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded-lg px-3 py-2 -ml-1 -mr-1 bg-gray-50 dark:bg-gray-800/50"
            onClick={(e) => {
              e.preventDefault();
              setShowContext(!showContext);
            }}
            aria-expanded={showContext}
          >
            <svg
              className="w-4 h-4 text-gray-500 dark:text-gray-400 transition-transform group-open:rotate-90 flex-shrink-0"
              viewBox="0 0 20 20"
              fill="currentColor"
              aria-hidden="true"
            >
              <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
            </svg>
            <span>Additional Context (Optional)</span>
          </summary>
          {showContext && (
            <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-700 animate-fade-in">
              <Textarea
                id="context"
                label="Additional Details"
                value={context}
                onChange={(e) => setContext(e.target.value)}
                placeholder="Relevant dates, notices received, previous correspondence, or other details that might help"
                rows={3}
                hint="This helps provide more tailored information. Do not include sensitive personal information."
                disabled={isDisabled}
                maxLength={2000}
              />
            </div>
          )}
        </details>

        <div className="pt-4 border-t border-gray-100 dark:border-gray-700 flex items-center gap-3 flex-wrap">
          <PrimaryButton
            type="submit"
            disabled={isDisabled || !question.trim()}
            aria-busy={isDisabled}
            size="lg"
            className="w-full sm:w-auto min-w-[200px]"
          >
            {isDisabled ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" aria-hidden="true">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Analyzing…
              </span>
            ) : (
              'Get Legal Information'
            )}
          </PrimaryButton>

          <Button
            type="button"
            variant="secondary"
            disabled={isDisabled}
            size="lg"
            className="w-full sm:w-auto"
            onClick={() => {
              setQuestion('');
              setContext('');
              setJurisdiction('');
              setShowContext(false);
              setQuestionError('');
              setCharCount(0);
            }}
          >
            Clear Form
          </Button>

          <span className="sr-only" aria-live="polite">
            {isDisabled ? 'Analyzing your legal question, please wait' : 'Ready to submit'}
          </span>
        </div>

        <div className="mt-6 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-gray-200 dark:border-gray-700">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">Example Questions</h3>
          <ul className="space-y-2" role="list">
            <li className="text-sm text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 cursor-text transition-colors p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700/50">
              &ldquo;My landlord gave me a 3-day eviction notice for non-payment in California. What are my options?&rdquo;
            </li>
            <li className="text-sm text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 cursor-text transition-colors p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700/50">
              &ldquo;I received a termination notice from my employer. What are my rights?&rdquo;
            </li>
            <li className="text-sm text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 cursor-text transition-colors p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700/50">
              &ldquo;What should I do if a debt collector is calling me about a debt I don&apos;t owe?&rdquo;
            </li>
          </ul>
          <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            These are general examples &mdash; not legal advice. For specific situations, consult an attorney.
          </p>
        </div>

        {/* Privacy Notice */}
        <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl">
          <div className="flex items-start gap-3">
            <svg className="flex-shrink-0 mt-0.5 h-5 w-5 text-blue-600 dark:text-blue-400" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            <div>
              <h4 className="text-sm font-semibold text-blue-800 dark:text-blue-200">Privacy First</h4>
              <p className="mt-1 text-sm text-blue-700 dark:text-blue-300">
                Do not enter unnecessary sensitive personal information such as passwords, financial credentials, government ID numbers, or private medical information. Questions are not saved as a permanent legal record by this interface.
              </p>
            </div>
          </div>
        </div>
      </div>
    </form>
  );
}