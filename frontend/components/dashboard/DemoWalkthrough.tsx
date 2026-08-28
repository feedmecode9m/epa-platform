export function DemoWalkthrough() {
  return (
    <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-100 px-5 py-3">
        <h2 className="text-sm font-semibold text-slate-900">Product walkthrough</h2>
        <p className="mt-0.5 text-sm text-slate-500">
          9-second screencast of the Prior Authorization Assistant (synthetic demo).
        </p>
      </div>
      <video
        className="aspect-video w-full bg-slate-900"
        controls
        playsInline
        preload="metadata"
        src="/demo/provider-dashboard-demo.webm"
      >
        Your browser does not support embedded video. Download{" "}
        <a href="/demo/provider-dashboard-demo.webm" className="underline">
          provider-dashboard-demo.webm
        </a>
        .
      </video>
    </section>
  );
}
