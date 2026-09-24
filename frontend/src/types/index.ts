export type Jurisdiction =
  | 'us_federal'
  | 'us_ca'
  | 'us_ny'
  | 'us_tx'
  | 'uk'
  | 'ca_federal'
  | 'ca_on'
  | 'au_federal'
  | 'eu'
  | 'international'
  | 'unknown';

export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';

export type RequestType =
  | 'general_info'
  | 'procedural_guidance'
  | 'rights_explanation'
  | 'deadline_inquiry'
  | 'document_review'
  | 'form_assistance'
  | 'escalation_needed'
  | 'unsupported';

export type LegalCategory =
  | 'housing'
  | 'employment'
  | 'family'
  | 'criminal'
  | 'immigration'
  | 'consumer'
  | 'civil_rights'
  | 'healthcare'
  | 'education'
  | 'financial'
  | 'other';

export type SourceType =
  | 'statute'
  | 'regulation'
  | 'case_law'
  | 'government_publication'
  | 'court_rule'
  | 'legal_aid_resource'
  | 'unknown';

export interface Source {
  type: SourceType;
  title: string;
  citation?: string;
  url?: string;
  jurisdiction: Jurisdiction;
  excerpt?: string;
  verified: boolean;
  retrieval_date: string;
}

export interface ClarificationQuestion {
  question: string;
  reason: string;
  required: boolean;
}

export interface TerminologyExplanation {
  term: string;
  explanation: string;
  category: string;
}

export interface DocumentChecklistItem {
  item: string;
  category: string;
  relevant: boolean;
}

export interface FollowUpSuggestion {
  question: string;
  reason: string;
  category: string;
}

export interface QuestionQuality {
  score: number;
  level: string;
  missing_information: string[];
  is_complete: boolean;
}

export type CoverageLevel = 'high' | 'moderate' | 'limited';

export interface LegalResponse {
  request_type: RequestType;
  risk_level: RiskLevel;
  legal_category: LegalCategory;
  jurisdiction: Jurisdiction;
  summary: string;
  explanation: string;
  sources: Source[];
  clarification_questions: ClarificationQuestion[];
  next_steps: string[];
  escalation_guidance?: string;
  uncertainty_notes: string[];
  disclaimer: string;
  generated_at: string;
  // Competition-quality additions
  question_quality?: QuestionQuality;
  information_coverage?: CoverageLevel;
  coverage_reason?: string;
  terminology_explanations: TerminologyExplanation[];
  document_checklist: DocumentChecklistItem[];
  follow_up_suggestions: FollowUpSuggestion[];
  provider_status?: string;
}

export interface AskRequest {
  question: string;
  jurisdiction?: Jurisdiction;
  context?: string;
  conversation_id?: string;
}

export interface AskResponse {
  response: LegalResponse;
  conversation_id: string;
}

export interface FeedbackRequest {
  conversation_id: string;
  rating: number;
  comment?: string;
  issue_type?: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  ai_provider: string;
}

export interface JurisdictionOption {
  value: Jurisdiction;
  label: string;
}

export interface CategoryOption {
  value: LegalCategory;
  label: string;
}