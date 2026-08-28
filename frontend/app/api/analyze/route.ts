import { NextResponse } from "next/server";
import { extractClinicalNote, predictApproval } from "@/lib/api/server-client";
import { getSessionToken } from "@/lib/auth/session";
import type { ApiError } from "@/lib/types/api";

export async function POST(request: Request) {
  const token = await getSessionToken();
  if (!token) {
    return NextResponse.json(
      { detail: "Not authenticated. Connect with an OAuth token first." },
      { status: 401 },
    );
  }

  const body = await request.json().catch(() => null);
  const clinicalNote =
    typeof body?.clinical_note === "string" ? body.clinical_note.trim() : "";

  if (clinicalNote.length < 10) {
    return NextResponse.json(
      { detail: "Clinical note must be at least 10 characters." },
      { status: 400 },
    );
  }

  try {
    const [extraction, prediction] = await Promise.all([
      extractClinicalNote(token, clinicalNote),
      predictApproval(token, clinicalNote),
    ]);

    return NextResponse.json({ extraction, prediction });
  } catch (err) {
    const apiErr = err as ApiError;
    return NextResponse.json(
      { detail: apiErr.detail ?? "Analysis failed" },
      { status: apiErr.status ?? 502 },
    );
  }
}
