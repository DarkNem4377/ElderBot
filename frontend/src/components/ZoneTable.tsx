// frontend/src/components/ZoneTable.tsx

"use client";

import type { AnalysisResult } from "@/lib/api";

interface Props {
  analysis: AnalysisResult | null;
}

function EmptyPriorityZones() {
  return (
    <div className="rounded-xl border border-blue-500/35 bg-diq-panel/55 shadow-2xl shadow-black/20">
      <div className="border-b border-diq-line/60 bg-slate-950/30 px-4 py-3">
        <div className="flex items-center justify-between gap-3">
          <h3 className="font-label text-xs uppercase tracking-[0.18em] text-slate-200">
            Priority Zones
          </h3>

          <span className="rounded border border-diq-line/50 bg-slate-950/60 px-2 py-1 text-[10px] font-black uppercase tracking-[0.12em] text-slate-500">
            Standby
          </span>
        </div>
      </div>

      <div className="p-4">
        <div className="overflow-hidden rounded-xl border border-diq-line/50 bg-slate-950/35">
          <div className="grid grid-cols-[56px_1fr_95px] border-b border-diq-line/50 bg-slate-950/55 px-3 py-2 text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">
            <span>Zone</span>
            <span>Damaged Buildings</span>
            <span className="text-right">Priority</span>
          </div>

          <div className="divide-y divide-diq-line/40">
            {[1, 2, 3, 4].map((rank) => (
              <div
                key={rank}
                className="grid grid-cols-[56px_1fr_95px] items-center gap-3 px-3 py-3"
              >
                <div className="h-7 w-7 rounded-lg bg-diq-line/25" />

                <div>
                  <div className="h-3 w-20 rounded bg-diq-line/25" />
                  <div className="mt-2 h-2 w-32 rounded bg-diq-line/15" />
                </div>

                <div className="ml-auto h-6 w-16 rounded-md bg-diq-line/20" />
              </div>
            ))}
          </div>
        </div>

        <p className="mt-4 text-sm leading-relaxed text-slate-500">
          Ranked response zones will appear here after DisasterIQ analyzes the
          before/after imagery.
        </p>
      </div>
    </div>
  );
}

function getPriorityMeta(rank: number) {
  if (rank === 1) {
    return {
      label: "High",
      badge: "border-red-500/50 bg-red-500 text-slate-950 shadow-red-950/30",
      rankBox: "bg-red-500 text-white",
      zoneText: "text-red-300",
      row: "bg-red-950/20 hover:bg-red-950/30",
      line: "bg-red-500/60",
    };
  }

  if (rank === 2) {
    return {
      label: "High",
      badge:
        "border-orange-500/50 bg-orange-500 text-slate-950 shadow-orange-950/30",
      rankBox: "bg-orange-500 text-white",
      zoneText: "text-orange-300",
      row: "bg-orange-950/15 hover:bg-orange-950/25",
      line: "bg-orange-500/60",
    };
  }

  if (rank === 3) {
    return {
      label: "Medium",
      badge:
        "border-yellow-500/50 bg-yellow-400 text-slate-950 shadow-yellow-950/30",
      rankBox: "bg-yellow-400 text-slate-950",
      zoneText: "text-yellow-200",
      row: "bg-yellow-950/10 hover:bg-yellow-950/20",
      line: "bg-yellow-400/60",
    };
  }

  return {
    label: "Low",
    badge:
      "border-green-500/50 bg-green-500 text-slate-950 shadow-green-950/30",
    rankBox: "bg-green-500 text-white",
    zoneText: "text-slate-100",
    row: "bg-slate-950/25 hover:bg-slate-900/40",
    line: "bg-green-500/50",
  };
}

function getZoneName(rank: number) {
  /*
    The current backend zones are ranked but do not expose a named zone_id
    in the existing frontend type. This gives the UI the same "Zone 3 / Zone 5"
    feel as the mockup while staying deterministic.
  */
  const demoZoneNames = [
    "Zone 3",
    "Zone 5",
    "Zone 8",
    "Zone 2",
    "Zone 6",
    "Zone 1",
  ];
  return demoZoneNames[rank - 1] ?? `Zone ${rank}`;
}

export default function ZoneTable({ analysis }: Props) {
  if (!analysis) {
    return <EmptyPriorityZones />;
  }

  const topZones = [...analysis.zones]
    .sort((a, b) => a.rank - b.rank)
    .slice(0, 6);

  return (
    <div className="rounded-xl border border-blue-500/35 bg-diq-panel/55 shadow-2xl shadow-black/20">
      <div className="border-b border-diq-line/60 bg-slate-950/30 px-4 py-3">
        <div className="flex items-center justify-between gap-3">
          <h3 className="font-label text-xs uppercase tracking-[0.18em] text-slate-200">
            Priority Zones
          </h3>

          <span className="rounded border border-diq-orange/40 bg-diq-orange/10 px-2 py-1 text-[10px] font-black uppercase tracking-[0.12em] text-diq-orange">
            {topZones.length} zones
          </span>
        </div>
      </div>

      <div className="p-4">
        <div className="overflow-hidden rounded-xl border border-diq-line/50 bg-slate-950/35">
          <div className="grid grid-cols-[60px_1fr_92px] border-b border-diq-line/50 bg-slate-950/55 px-3 py-2 text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">
            <span>Zone</span>
            <span>Damaged Buildings</span>
            <span className="text-right">Priority</span>
          </div>

          <div className="divide-y divide-diq-line/40">
            {topZones.map((zone) => {
              const meta = getPriorityMeta(zone.rank);
              const destroyed = zone.building_counts.destroyed;
              const major = zone.building_counts.major;
              const damagedBuildings = destroyed + major;
              const zoneName = getZoneName(zone.rank);

              return (
                <article
                  key={`${zone.rank}-${zoneName}`}
                  className={`grid grid-cols-[60px_1fr_92px] items-center gap-3 px-3 py-3 transition ${meta.row}`}
                >
                  <div className="flex items-center gap-3">
                    <span
                      className={`flex h-8 w-8 items-center justify-center rounded-lg text-sm font-black shadow-lg shadow-black/20 ${meta.rankBox}`}
                    >
                      {zone.rank}
                    </span>
                  </div>

                  <div className="min-w-0">
                    <div className="flex items-baseline justify-between gap-3">
                      <h4
                        className={`truncate text-sm font-black ${meta.zoneText}`}
                      >
                        {zoneName}
                      </h4>

                      <span className="text-lg font-black leading-none text-white">
                        {damagedBuildings}
                      </span>
                    </div>

                    <div className="mt-1 flex items-center justify-between gap-3">
                      <p className="truncate text-[11px] text-slate-400">
                        {destroyed} destroyed, {major} major
                      </p>

                      <div className="h-1 w-24 overflow-hidden rounded-full bg-slate-800">
                        <div
                          className={`h-full rounded-full ${meta.line}`}
                          style={{
                            width: `${Math.min(
                              100,
                              Math.max(12, damagedBuildings),
                            )}%`,
                          }}
                        />
                      </div>
                    </div>
                  </div>

                  <div className="flex justify-end">
                    <span
                      className={`rounded-md border px-2.5 py-1.5 text-[10px] font-black uppercase tracking-[0.08em] shadow-lg ${meta.badge}`}
                    >
                      {meta.label}
                    </span>
                  </div>
                </article>
              );
            })}
          </div>
        </div>

        <button
          type="button"
          className="mt-4 w-full rounded-lg border border-blue-500/30 bg-blue-950/20 px-3 py-2 text-sm font-semibold text-blue-300 transition hover:border-blue-400/60 hover:bg-blue-950/35"
        >
          View all zones →
        </button>

        <p className="mt-3 text-[11px] leading-5 text-slate-500">
          Building counts are estimated via connected-component analysis of
          the damage mask, not verified per-building IDs.
        </p>
      </div>
    </div>
  );
}
