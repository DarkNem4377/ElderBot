// frontend/src/components/ZoneMap.tsx

"use client";

import dynamic from "next/dynamic";
import type { AnalysisResult } from "@/lib/api";

interface Props {
  analysis: AnalysisResult | null;
}

const ZoneMapInner = dynamic(() => import("./ZoneMapInner"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full min-h-[280px] items-center justify-center text-sm text-slate-500">
      Loading map…
    </div>
  ),
});

export default function ZoneMap({ analysis }: Props) {
  if (!analysis) return null;

  return (
    <div className="overflow-hidden rounded-xl border border-blue-500/35 bg-diq-panel/45 shadow-2xl shadow-black/20">
      <div className="border-b border-diq-line/60 bg-slate-950/30 px-4 py-3">
        <h3 className="font-label text-xs uppercase tracking-[0.18em] text-slate-200">
          Zone Map
        </h3>
      </div>

      {analysis.geo_available ? (
        <div className="h-[320px] w-full">
          <ZoneMapInner analysis={analysis} />
        </div>
      ) : (
        <div className="flex h-[120px] items-center justify-center px-6 text-center text-xs text-slate-500">
          {analysis.geo_message ??
            "Geographic coordinates available for demo pairs with xBD metadata only."}
        </div>
      )}
    </div>
  );
}
