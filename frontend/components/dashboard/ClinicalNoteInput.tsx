"use client";

import { SAMPLE_NOTE } from "@/lib/demo/sample-workflow";

interface ClinicalNoteInputProps {
  value: string;
  onChange: (value: string) => void;
  onAnalyze: () => void;
  loading: boolean;
  disabled: boolean;
}

export function ClinicalNoteInput({
  value,
  onChange,
  onAnalyze,
  loading,
  disabled,
}: ClinicalNoteInputProps) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-900">Clinical Note</h2>
        <span className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
          Synthetic data only
        </span>
      </div>
      <p className="mt-1 text-sm text-slate-500">
        Paste a de-identified or synthetic progress note for NLP extraction and PA scoring.
      </p>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={8}
        disabled={disabled}
        placeholder="Enter synthetic clinical note…"
        className="mt-4 w-full resize-y rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm leading-relaxed focus:border-teal-600 focus:outline-none focus:ring-2 focus:ring-teal-600/20 disabled:bg-slate-50"
      />
      <div className="mt-4 flex flex-wrap gap-3">
        <button
          type="button"
          onClick={onAnalyze}
          disabled={disabled || loading || value.trim().length < 10}
          className="btn-primary px-5 py-2.5 text-sm"
        >
          {loading ? "Analyzing…" : "Analyze prior authorization"}
        </button>
        <button
          type="button"
          onClick={() => onChange(SAMPLE_NOTE)}
          disabled={loading}
          className="btn-secondary px-4 py-2.5 text-sm"
        >
          Load sample note
        </button>
      </div>
    </section>
  );
}
