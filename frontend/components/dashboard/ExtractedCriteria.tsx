import type { NLPExtractionResponse } from "@/lib/types/api";

interface ExtractedCriteriaProps {
  extraction: NLPExtractionResponse | null;
  preview?: boolean;
}

const ENTITY_LABELS: Record<string, string> = {
  condition: "Diagnosis",
  procedure: "Procedure",
  medication: "Medication",
  conservative_therapy: "Conservative therapy",
  clinical_justification: "Clinical justification",
};

export function ExtractedCriteria({ extraction, preview = false }: ExtractedCriteriaProps) {
  if (!extraction) {
    return (
      <section className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-5">
        <h2 className="text-lg font-semibold text-slate-700">Extracted FHIR Criteria</h2>
        <p className="mt-2 text-sm text-slate-500">
          Run analysis to view structured CoverageEligibilityRequest fields.
        </p>
      </section>
    );
  }

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-slate-900">Extracted FHIR Criteria</h2>
        <div className="flex items-center gap-2">
          {preview && (
            <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
              Demo preview
            </span>
          )}
          <span className="text-sm text-slate-500">
            Confidence {(extraction.confidence_score * 100).toFixed(0)}%
          </span>
        </div>
      </div>

      {extraction.conservative_therapy_weeks != null && (
        <div className="mt-4 rounded-lg bg-blue-50 px-4 py-3 text-sm text-blue-900">
          Conservative treatment duration:{" "}
          <strong>{extraction.conservative_therapy_weeks} weeks</strong>
        </div>
      )}

      <ul className="mt-4 space-y-3">
        {extraction.entities.map((entity, idx) => (
          <li
            key={`${entity.entity_type}-${idx}`}
            className="flex items-start justify-between gap-4 rounded-lg border border-slate-100 bg-slate-50 px-4 py-3"
          >
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-teal-700">
                {ENTITY_LABELS[entity.entity_type] ?? entity.entity_type}
              </p>
              <p className="mt-1 text-sm text-slate-800">{entity.text}</p>
              {entity.code && (
                <p className="mt-1 font-mono text-xs text-slate-500">{entity.code}</p>
              )}
            </div>
            <span className="shrink-0 text-xs text-slate-400">
              {(entity.confidence * 100).toFixed(0)}%
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
