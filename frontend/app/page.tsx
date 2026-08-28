import { Dashboard } from "@/components/dashboard/Dashboard";

export default function Home() {
  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-teal-700">
              ePA Platform
            </p>
            <h1 className="text-xl font-bold text-slate-900">Prior Authorization Assistant</h1>
          </div>
          <p className="hidden text-xs text-slate-500 sm:block">
            Demo · Synthetic data · Phase 3
          </p>
        </div>
      </header>

      <main className="px-4 py-8 sm:px-6">
        <Dashboard />
      </main>

      <footer className="border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-500">
        Not for use with real PHI. OAuth tokens stored in httpOnly cookies.
      </footer>
    </div>
  );
}
