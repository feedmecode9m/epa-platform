import type { PredictionResponse } from "@/lib/types/api";

interface PredictionResultsProps {
  prediction: PredictionResponse | null;
  preview?: boolean;
}

function scoreColor(score: number): string {
  if (score >= 80) return "text-emerald-600";
  if (score >= 50) return "text-amber-600";
  return "text-red-600";
}

function scoreRingColor(score: number): string {
  if (score >= 80) return "stroke-emerald-500";
  if (score >= 50) return "stroke-amber-500";
  return "stroke-red-500";
}

export function PredictionResults({ prediction, preview = false }: PredictionResultsProps) {
  if (!prediction) {
    return (
      <section className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-5">
        <h2 className="text-lg font-semibold text-slate-700">Approval Likelihood</h2>
        <p className="mt-2 text-sm text-slate-500">
          Predictive rules engine results will appear here.
        </p>
      </section>
    );
  }

  const score = prediction.approval_likelihood_score;
  const circumference = 2 * Math.PI * 54;
  const offset = circumference - (score / 100) * circumference;

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-slate-900">Approval Likelihood</h2>
        {preview && (
          <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
            Demo preview
          </span>
        )}
      </div>
      {prediction.policy_name && (
        <p className="mt-1 text-sm text-slate-500">{prediction.policy_name}</p>
      )}

      <div className="mt-6 flex flex-col items-center sm:flex-row sm:items-start sm:gap-8">
        <div className="relative h-32 w-32 shrink-0">
          <svg className="h-32 w-32 -rotate-90" viewBox="0 0 120 120">
            <circle
              cx="60"
              cy="60"
              r="54"
              fill="none"
              strokeWidth="8"
              className="stroke-slate-200"
            />
            <circle
              cx="60"
              cy="60"
              r="54"
              fill="none"
              strokeWidth="8"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              strokeLinecap="round"
              className={scoreRingColor(score)}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className={`text-3xl font-bold ${scoreColor(score)}`}>{score}%</span>
            <span className="text-xs text-slate-500">Likelihood</span>
          </div>
        </div>

        <div className="mt-4 flex-1 sm:mt-0">
          <p className="text-sm font-medium text-slate-800">{prediction.recommendation}</p>

          {prediction.matched_criteria.length > 0 && (
            <div className="mt-4">
              <h3 className="text-xs font-semibold uppercase tracking-wide text-emerald-700">
                Met criteria
              </h3>
              <ul className="mt-2 space-y-1">
                {prediction.matched_criteria.map((item) => (
                  <li key={item} className="flex items-start gap-2 text-sm text-slate-700">
                    <span className="text-emerald-600">✓</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      {prediction.documentation_gaps.length > 0 && (
        <div className="mt-6 border-t border-slate-100 pt-5">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-amber-700">
            Documentation gaps
          </h3>
          <ul className="mt-3 space-y-2">
            {prediction.documentation_gaps.map((gap) => (
              <li
                key={`${gap.code}-${gap.description}`}
                className="flex items-start gap-2 rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-900"
              >
                <span className="shrink-0 font-mono text-xs">{gap.severity}</span>
                <span>{gap.description}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
