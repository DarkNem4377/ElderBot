// frontend/src/components/BriefPanel.tsx

"use client";

interface Props {
  brief: string | null;
  source: string | null;
  loading: boolean;
  onDownloadReport?: () => void;
  reportLoading?: boolean;
}

function LoadingBrief() {
  return (
    <div className="rounded-xl border border-diq-orange/30 bg-diq-orange/10 p-5">
      <div className="flex items-center gap-3">
        <span className="h-3 w-3 animate-pulse rounded-full bg-diq-orange shadow-[0_0_16px_rgba(249,115,22,0.8)]" />

        <div>
          <p className="text-sm font-black uppercase tracking-[0.12em] text-diq-orange">
            Generating AI situation brief
          </p>

          <p className="mt-1 text-sm text-slate-400">
            Converting ranked damage zones into a field-ready response summary.
          </p>
        </div>
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-3">
        <div className="h-20 animate-pulse rounded-lg bg-slate-950/45" />
        <div className="h-20 animate-pulse rounded-lg bg-slate-950/45" />
        <div className="h-20 animate-pulse rounded-lg bg-slate-950/45" />
      </div>
    </div>
  );
}

function EmptyBrief() {
  return (
    <div className="rounded-xl border border-dashed border-diq-line/50 bg-slate-950/30 p-5">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div>
          <p className="font-label text-xs uppercase tracking-[0.18em] text-slate-500">
            Awaiting analysis
          </p>

          <h4 className="mt-2 text-xl font-black text-white">
            No emergency brief generated yet
          </h4>

          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
            Run damage analysis to generate an executive summary, response
            priorities, and field recommendations.
          </p>
        </div>

        <div className="grid min-w-[300px] gap-2 sm:grid-cols-3 xl:grid-cols-1">
          <BriefMiniCard title="Summary" body="Damage overview" />
          <BriefMiniCard title="Priorities" body="Critical zones" />
          <BriefMiniCard title="Actions" body="Relief guidance" />
        </div>
      </div>
    </div>
  );
}

function BriefMiniCard({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-lg border border-diq-line/35 bg-slate-950/45 px-3 py-2.5">
      <p className="text-[10px] font-black uppercase tracking-[0.14em] text-slate-500">
        {title}
      </p>

      <p className="mt-1 text-xs text-slate-400">{body}</p>
    </div>
  );
}

function ReportTabs({
  source,
  isLive,
}: {
  source: string | null;
  isLive: boolean;
}) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <button
        type="button"
        className="rounded-lg border border-diq-orange/50 bg-diq-orange px-3 py-1.5 text-[11px] font-black uppercase tracking-[0.12em] text-white shadow-lg shadow-orange-950/30"
      >
        English Report
      </button>

      {source && (
        <span
          className={`rounded-lg border px-3 py-1.5 text-[11px] font-black uppercase tracking-[0.12em] ${
            isLive
              ? "border-green-500/40 bg-green-950/30 text-green-300"
              : "border-diq-line/50 bg-slate-950/50 text-slate-400"
          }`}
        >
          {isLive ? "Fireworks AI" : source}
        </span>
      )}
    </div>
  );
}

function GeneratedBrief({
  brief,
  onDownloadReport,
  reportLoading,
}: {
  brief: string;
  onDownloadReport?: () => void;
  reportLoading?: boolean;
}) {
  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_330px]">
      <article className="overflow-hidden rounded-xl border border-diq-line/45 bg-slate-950/35">
        <div className="border-b border-diq-line/40 bg-slate-950/45 px-5 py-4">
          <p className="text-xs font-black uppercase tracking-[0.16em] text-diq-orange">
            Executive Summary
          </p>

          <p className="mt-1 text-sm text-slate-500">
            Generated from ranked damage zones and severity counts.
          </p>
        </div>

        <div className="max-h-[360px] overflow-auto p-5">
          <pre className="whitespace-pre-wrap font-sans text-sm leading-7 text-slate-200">
            {brief}
          </pre>
        </div>
      </article>

      <aside className="space-y-3">
        <div className="rounded-xl border border-diq-line/50 bg-slate-950/35 p-4">
          <p className="font-label text-xs uppercase tracking-[0.18em] text-slate-300">
            Key Insights
          </p>

          <div className="mt-3 space-y-2.5">
            <InsightCard
              number="01"
              title="Highest damage cluster"
              body="Top-ranked zones should receive first assessment teams."
              tone="red"
            />

            <InsightCard
              number="02"
              title="Resource triage"
              body="Destroyed and major-damage counts drive priority."
              tone="orange"
            />

            <InsightCard
              number="03"
              title="Coordinator use"
              body="Use as a dispatch brief, not a final ground survey."
              tone="blue"
            />
          </div>
        </div>

        <button
          type="button"
          onClick={onDownloadReport}
          disabled={!onDownloadReport || reportLoading}
          className="w-full rounded-lg border border-diq-orange/50 bg-diq-orange px-4 py-3 text-sm font-black text-white shadow-lg shadow-orange-950/30 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-55"
        >
          {reportLoading ? "Generating PDF…" : "Download field report (PDF)"}
        </button>
      </aside>
    </div>
  );
}

function InsightCard({
  number,
  title,
  body,
  tone,
}: {
  number: string;
  title: string;
  body: string;
  tone: "red" | "orange" | "blue";
}) {
  const styles = {
    red: "border-red-500/30 bg-red-950/20",
    orange: "border-orange-500/30 bg-orange-950/20",
    blue: "border-blue-500/30 bg-blue-950/20",
  }[tone];

  const numberStyles = {
    red: "text-red-300",
    orange: "text-orange-300",
    blue: "text-blue-300",
  }[tone];

  return (
    <div className={`rounded-lg border p-3 ${styles}`}>
      <div className="flex items-start gap-3">
        <span
          className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-slate-950/55 text-[11px] font-black ${numberStyles}`}
        >
          {number}
        </span>

        <div>
          <p className="text-sm font-black text-slate-100">{title}</p>
          <p className="mt-1 text-xs leading-5 text-slate-400">{body}</p>
        </div>
      </div>
    </div>
  );
}

export default function BriefPanel({
  brief,
  source,
  loading,
  onDownloadReport,
  reportLoading,
}: Props) {
  const isLive = source === "fireworks";

  return (
    <section className="rounded-xl border border-blue-500/35 bg-diq-panel/55 shadow-2xl shadow-black/20">
      <div className="border-b border-diq-line/60 bg-slate-950/30 px-5 py-4">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div>
            <p className="font-label text-xs uppercase tracking-[0.18em] text-diq-orange">
              AI Situation Brief
            </p>

            <h3 className="mt-1 text-2xl font-black tracking-tight text-white">
              Emergency Response Summary
            </h3>

            <p className="mt-1 text-sm text-slate-500">
              Plain-language disaster intelligence for field coordinators.
            </p>
          </div>

          <ReportTabs source={source} isLive={isLive} />
        </div>
      </div>

      <div className="p-5">
        {loading && <LoadingBrief />}

        {!loading && brief && (
          <GeneratedBrief
            brief={brief}
            onDownloadReport={onDownloadReport}
            reportLoading={reportLoading}
          />
        )}

        {!loading && !brief && <EmptyBrief />}
      </div>
    </section>
  );
}