/**
 * Server-side API client — never import in Client Components.
 * Tokens are read from httpOnly cookies, not exposed to the browser.
 */

import type {
  ApiError,
  NLPExtractionResponse,
  PredictionResponse,
} from "@/lib/types/api";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

async function backendFetch<T>(
  path: string,
  token: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${BACKEND_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(options.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    let detail = "Request failed";
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      /* ignore parse errors */
    }
    const error: ApiError = { detail, status: response.status };
    throw error;
  }

  return response.json() as Promise<T>;
}

export async function extractClinicalNote(
  token: string,
  clinicalNote: string,
): Promise<NLPExtractionResponse> {
  return backendFetch<NLPExtractionResponse>("/api/v1/nlp/extract", token, {
    method: "POST",
    body: JSON.stringify({
      clinical_note: clinicalNote,
      patient_reference: "Patient/synth-patient-0000",
      insurer_reference: "Organization/payer-aetna-synth",
    }),
  });
}

export async function predictApproval(
  token: string,
  clinicalNote: string,
): Promise<PredictionResponse> {
  return backendFetch<PredictionResponse>(
    "/api/v1/prior-authorization/predict",
    token,
    {
      method: "POST",
      body: JSON.stringify({ clinical_note: clinicalNote }),
    },
  );
}
