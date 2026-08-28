export interface ExtractedEntity {
  entity_type: string;
  text: string;
  code: string | null;
  code_system: string | null;
  confidence: number;
}

export interface NLPExtractionResponse {
  entities: ExtractedEntity[];
  conservative_therapy_weeks: number | null;
  coverage_eligibility_request: Record<string, unknown>;
  confidence_score: number;
}

export interface DocumentationGap {
  code: string;
  description: string;
  severity: string;
}

export interface PredictionResponse {
  approval_likelihood_score: number;
  policy_id: string | null;
  policy_name: string | null;
  matched_criteria: string[];
  documentation_gaps: DocumentationGap[];
  scoring_breakdown: Record<string, number>;
  recommendation: string;
  coverage_eligibility_request: Record<string, unknown> | null;
}

export interface AnalysisResult {
  extraction: NLPExtractionResponse;
  prediction: PredictionResponse;
}

export interface ApiError {
  detail: string;
  status: number;
}
