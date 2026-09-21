'use client';

import type { RiskLevel } from '@/types';

interface HighRiskNoticeProps {
  riskLevel: Extract<RiskLevel, 'high' | 'critical'>;
  guidance: string;
  onDismiss?: () => void;
  dismissible?: boolean;
}

const RISK_CONFIG = {
  high: {
    bg: 'bg-orange-50',
    border: 'border-orange-200',
    iconColor: 'text-orange-600',
    textColor: 'text-orange-800',
    title: 'High-Risk Situation',
    description: 'This situation involves significant legal consequences. The information below is general legal information and should not be treated as definitive advice.',
  },
  critical: {
    bg: 'bg-red-50',
    border: 'border-red-200',
    iconColor: 'text-red-600',
    textColor: 'text-red-800',
    title: 'Critical Situation - Immediate Action Recommended',
    description: 'This appears to be an urgent, high-stakes legal matter. The information below is general legal information only. You should seek professional legal assistance immediately.',
  },
} as const;

export function HighRiskNotice({ 
  riskLevel, 
  guidance, 
  onDismiss, 
  dismissible = true 
}: HighRiskNoticeProps) {
  const config = RISK_CONFIG[riskLevel];
  
  return (
    <div
      role="alert"
      aria-live="assertive"
      className={`${config.bg} border ${config.border} rounded-xl p-5 md:p-6 ${dismissible ? 'pr-12' : ''} relative`}
    >
      <div className="flex items-start gap-4">
        <div className="flex-shrink-0 mt-0.5" aria-hidden="true">
          <svg
            className={`h-6 w-6 ${config.iconColor} flex-shrink-0`}
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fillRule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
              clipRule="evenodd"
            />
          </svg>
        </div>
        
        <div className="flex-1 min-w-0">
          <h3 className={`text-lg font-semibold ${config.textColor}`}>
            {config.title}
          </h3>
          <p className={`mt-2 ${config.textColor}`}>
            {config.description}
          </p>
          
            <div className="mt-4 p-4 bg-white border border-gray-200 rounded-xl">
            <h4 className="text-sm font-medium text-gray-900 mb-1">Recommended Action</h4>
            <p className="text-sm text-gray-700">{guidance}</p>
          </div>
        </div>
        
        {dismissible && onDismiss && (
          <button
            type="button"
            onClick={onDismiss}
            className="flex-shrink-0 p-1.5 text-gray-500 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-orange-50 focus:ring-orange-500 rounded-lg"
            aria-label="Dismiss high-risk notice"
          >
            <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              <path d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}