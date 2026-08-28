"use client";

import { useState } from "react";

interface AuthPanelProps {
  connected: boolean;
  onConnectionChange: (connected: boolean) => void;
}

export function AuthPanel({ connected, onConnectionChange }: AuthPanelProps) {
  const [token, setToken] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function connect() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/auth/session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? "Failed to connect");
      }
      setToken("");
      onConnectionChange(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Connection failed");
    } finally {
      setLoading(false);
    }
  }

  async function disconnect() {
    await fetch("/api/auth/session", { method: "DELETE" });
    onConnectionChange(false);
  }

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
            Session
          </h2>
          <p className="mt-1 text-sm text-slate-600">
            Token stored in httpOnly cookie — never in localStorage.
          </p>
        </div>
        <span
          className={`rounded-full px-3 py-1 text-xs font-medium ${
            connected
              ? "bg-emerald-100 text-emerald-800"
              : "bg-amber-100 text-amber-800"
          }`}
        >
          {connected ? "Connected" : "Not connected"}
        </span>
      </div>

      {!connected ? (
        <div className="mt-4 space-y-3">
          <label htmlFor="oauth-token" className="block text-sm font-medium text-slate-700">
            OAuth Access Token (synthetic dev environment)
          </label>
          <input
            id="oauth-token"
            type="password"
            autoComplete="off"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="Paste Bearer token from OAuth flow"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-teal-600 focus:outline-none focus:ring-2 focus:ring-teal-600/20"
          />
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button
            type="button"
            onClick={connect}
            disabled={loading || token.length < 20}
            className="btn-primary px-4 py-2 text-sm font-medium"
          >
            {loading ? "Connecting…" : "Connect securely"}
          </button>
        </div>
      ) : (
        <button
          type="button"
          onClick={disconnect}
          className="mt-4 text-sm text-slate-600 underline hover:text-slate-900"
        >
          Disconnect session
        </button>
      )}
    </section>
  );
}
