import { NextResponse } from "next/server";
import { SESSION_COOKIE, sessionCookieOptions } from "@/lib/auth/session";

export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  const token = typeof body?.token === "string" ? body.token.trim() : "";

  if (!token || token.length < 20) {
    return NextResponse.json({ detail: "Invalid token" }, { status: 400 });
  }

  const response = NextResponse.json({ status: "connected" });
  response.cookies.set(SESSION_COOKIE, token, sessionCookieOptions());
  return response;
}

export async function DELETE() {
  const response = NextResponse.json({ status: "disconnected" });
  response.cookies.set(SESSION_COOKIE, "", { ...sessionCookieOptions(), maxAge: 0 });
  return response;
}

export async function GET() {
  const { getSessionToken } = await import("@/lib/auth/session");
  const token = await getSessionToken();
  return NextResponse.json({ connected: Boolean(token) });
}
