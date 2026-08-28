export function DemoWalkthrough() {
  return (
    <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-100 px-5 py-3">
        <h2 className="text-sm font-semibold text-slate-900">Product walkthrough</h2>
        <p className="mt-0.5 text-sm text-slate-500">
          Screencast of the Prior Authorization Assistant (synthetic demo).
        </p>
      </div>
      <video
        className="aspect-video w-full bg-slate-900"
        controls
        playsInline
        preload="metadata"
        poster="/demo/provider-dashboard-poster.jpg"
      >
        <source src="/demo/provider-dashboard-demo.mp4" type="video/mp4" />
        <source src="/demo/provider-dashboard-demo.webm" type="video/webm" />
        Your browser does not support embedded video.{" "}
        <a href="/demo/provider-dashboard-demo.mp4" className="underline">
          Download MP4
        </a>
        .
      </video>
    </section>
  );
}
