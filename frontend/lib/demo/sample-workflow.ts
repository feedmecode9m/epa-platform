import type { AnalysisResult } from "@/lib/types/api";

export const SAMPLE_NOTE =
  "MRI confirms L4-L5 disc herniation with radiculopathy. Patient completed 8 weeks of conservative physical therapy without improvement. Requesting lumbar microdiscectomy (CPT 63030).";

/** Static synthetic preview so the dashboard is never a blank slate. */
export const SAMPLE_ANALYSIS: AnalysisResult = {
  extraction: {
    entities: [
      {
        entity_type: "condition",
        text: "Lumbar disc herniation",
        code: "M51.26",
        code_system: "http://hl7.org/fhir/sid/icd-10-cm",
        confidence: 0.92,
      },
      {
        entity_type: "procedure",
        text: "Laminotomy",
        code: "63030",
        code_system: "http://www.ama-assn.org/go/cpt",
        confidence: 0.88,
      },
      {
        entity_type: "conservative_therapy",
        text: "8 weeks conservative therapy",
        code: null,
        code_system: null,
        confidence: 0.9,
      },
      {
        entity_type: "clinical_justification",
        text: "Conservative treatment failure documented",
        code: null,
        code_system: null,
        confidence: 0.87,
      },
    ],
    conservative_therapy_weeks: 8,
    coverage_eligibility_request: {
      resourceType: "CoverageEligibilityRequest",
      status: "active",
    },
    confidence_score: 0.893,
  },
  prediction: {
    approval_likelihood_score: 85,
    policy_id: "spine-surgery-lumbar",
    policy_name: "Lumbar Spine Surgery Prior Authorization",
    matched_criteria: [
      "Conservative therapy 8 weeks (≥6 required)",
      "Imaging study referenced in clinical note",
      "Required entity present: condition",
      "Required entity present: procedure",
    ],
    documentation_gaps: [
      {
        code: "DOC_GAP",
        description: "Provider NPI and specialty",
        severity: "recommended",
      },
    ],
    scoring_breakdown: {
      conservative_therapy_met: 30,
      has_imaging: 25,
    },
    recommendation: "Likely approved — criteria substantially met",
    coverage_eligibility_request: null,
  },
};
