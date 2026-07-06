"use client";

interface Props {
  brief: string | null;
  source: string | null;
  loading: boolean;
}

export default function BriefPanel({ brief, source, loading }: Props) {
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900/50 p-4 h-full">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-slate-300">Situation Brief</h3>
        {source && (
          <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-400">
            {source}
          </span>
        )}
      </div>
      {loading && <p className="text-slate-500 text-sm animate-pulse">Generating brief...</p>}
      {!loading && brief && (
        <pre className="whitespace-pre-wrap text-sm text-slate-300 leading-relaxed font-sans">
          {brief}
        </pre>
      )}
      {!loading && !brief && (
        <p className="text-slate-500 text-sm">Run analysis to generate a situation brief.</p>
      )}
    </div>
  );
}
