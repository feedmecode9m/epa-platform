"use client";

import { useCallback, useEffect, useState } from "react";
import { AuthPanel } from "@/components/dashboard/AuthPanel";
import { DemoWalkthrough } from "@/components/dashboard/DemoWalkthrough";
import { ClinicalNoteInput } from "@/components/dashboard/ClinicalNoteInput";
import { ExtractedCriteria } from "@/components/dashboard/ExtractedCriteria";
import { PredictionResults } from "@/components/dashboard/PredictionResults";
import { SAMPLE_ANALYSIS, SAMPLE_NOTE } from "@/lib/demo/sample-workflow";
import type { AnalysisResult } from "@/lib/types/api";

export function Dashboard() {
  const [connected, setConnected] = useState(false);
  const [note, setNote] = useState(SAMPLE_NOTE);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(SAMPLE_ANALYSIS);
  const [isPreview, setIsPreview] = useState(true);

  useEffect(() => {
    fetch("/api/auth/session")
      .then((r) => r.json())
      .then((data) => setConnected(Boolean(data.connected)))
      .catch(() => setConnected(false));
  }, []);

  const analyze = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ clinical_note: note }),
      });
      const data = await res.json();
      if (!res.ok) {
        if (res.status === 401) setConnected(false);
        throw new Error(data.detail ?? "Analysis failed");
      }
      setResult(data);
      setIsPreview(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  }, [note]);

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <DemoWalkthrough />

      <ol className="grid gap-3 sm:grid-cols-3">
        {[
          { n: "1", title: "Paste the note", body: "Synthetic progress note is pre-loaded." },
          { n: "2", title: "Extract FHIR criteria", body: "Diagnoses, CPT, and therapy duration." },
          { n: "3", title: "Score the request", body: "Likelihood % and documentation gaps." },
        ].map((step) => (
          <li
            key={step.n}
            className="rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm"
          >
            <p className="text-xs font-semibold uppercase tracking-wide text-teal-700">
              Step {step.n}
            </p>
            <p className="mt-1 font-medium text-slate-900">{step.title}</p>
            <p className="mt-0.5 text-sm text-slate-500">{step.body}</p>
          </li>
        ))}
      </ol>

      {isPreview && (
        <p className="rounded-lg border border-teal-200 bg-teal-50 px-4 py-2 text-sm text-teal-900">
          Showing a synthetic lumbar-spine demo so the screen is never empty. Connect a
          token and click Analyze to run the live pipeline.
        </p>
      )}

      <AuthPanel connected={connected} onConnectionChange={setConnected} />

      <ClinicalNoteInput
        value={note}
        onChange={setNote}
        onAnalyze={analyze}
        loading={loading}
        disabled={!connected}
      />

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {error}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <ExtractedCriteria extraction={result?.extraction ?? null} preview={isPreview} />
        <PredictionResults prediction={result?.prediction ?? null} preview={isPreview} />
      </div>
    </div>
  );
}
