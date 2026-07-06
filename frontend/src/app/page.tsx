"use client";

import { useCallback, useEffect, useState } from "react";
import BriefPanel from "@/components/BriefPanel";
import DamageCanvas from "@/components/DamageCanvas";
import ZoneTable from "@/components/ZoneTable";
import {
  analyzeDemoPair,
  analyzeUpload,
  demoImageUrl,
  fetchBrief,
  fetchDemoPairs,
  type AnalysisResult,
  type DemoPair,
} from "@/lib/api";

export default function HomePage() {
  const [pairs, setPairs] = useState<DemoPair[]>([]);
  const [selectedPair, setSelectedPair] = useState<string>("");
  const [preFile, setPreFile] = useState<File | null>(null);
  const [postFile, setPostFile] = useState<File | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [postUrl, setPostUrl] = useState<string>("");
  const [preUrl, setPreUrl] = useState<string>("");
  const [brief, setBrief] = useState<string | null>(null);
  const [briefSource, setBriefSource] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [briefLoading, setBriefLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDemoPairs()
      .then((p) => {
        setPairs(p);
        if (p.length > 0) setSelectedPair(p[0].id);
      })
      .catch((e) => setError(String(e)));
  }, []);

  const runAnalysis = useCallback(async () => {
    setLoading(true);
    setError(null);
    setBrief(null);
    try {
      let result: AnalysisResult;
      if (preFile && postFile) {
        result = await analyzeUpload(preFile, postFile);
        setPreUrl(URL.createObjectURL(preFile));
        setPostUrl(URL.createObjectURL(postFile));
      } else if (selectedPair) {
        result = await analyzeDemoPair(selectedPair);
        const pair = pairs.find((p) => p.id === selectedPair);
        if (pair) {
          setPreUrl(demoImageUrl(pair.pre_image));
          setPostUrl(demoImageUrl(pair.post_image));
        }
      } else {
        throw new Error("Select a demo pair or upload images");
      }
      setAnalysis(result);

      setBriefLoading(true);
      const context =
        "Pakistan disaster response context: prioritize flood and earthquake damage zones for triage.";
      const briefResp = await fetchBrief(result, context);
      setBrief(briefResp.brief);
      setBriefSource(briefResp.source);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
      setBriefLoading(false);
    }
  }, [preFile, postFile, selectedPair, pairs]);

  return (
    <main className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      <header className="space-y-2">
        <p className="text-xs uppercase tracking-widest text-amber-500/80">Team DarkNem</p>
        <h1 className="text-3xl font-bold text-white">Satellite Disaster-Damage Triage</h1>
        <p className="text-slate-400 max-w-2xl">
          Deterministic ML damage scoring with AI-generated situation briefs for emergency
          coordinators. AMD Hackathon ACT II.
        </p>
      </header>

      <section className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-4 rounded-lg border border-slate-700 bg-slate-900/40 p-4">
          <h2 className="font-semibold text-slate-200">Input</h2>

          <label className="block text-sm text-slate-400">Demo pair (xBD test set)</label>
          <select
            value={selectedPair}
            onChange={(e) => {
              setSelectedPair(e.target.value);
              setPreFile(null);
              setPostFile(null);
            }}
            className="w-full rounded bg-slate-800 border border-slate-600 px-3 py-2 text-sm"
          >
            {pairs.map((p) => (
              <option key={p.id} value={p.id}>
                {p.disaster_type}: {p.id}
              </option>
            ))}
          </select>

          <div className="text-center text-xs text-slate-500">— or upload custom pair —</div>

          <label className="block text-sm text-slate-400">Pre-disaster image</label>
          <input
            type="file"
            accept="image/*"
            onChange={(e) => setPreFile(e.target.files?.[0] ?? null)}
            className="w-full text-sm text-slate-400"
          />

          <label className="block text-sm text-slate-400">Post-disaster image</label>
          <input
            type="file"
            accept="image/*"
            onChange={(e) => setPostFile(e.target.files?.[0] ?? null)}
            className="w-full text-sm text-slate-400"
          />

          <button
            onClick={runAnalysis}
            disabled={loading}
            className="w-full rounded-lg bg-amber-600 hover:bg-amber-500 disabled:opacity-50 px-4 py-2.5 font-medium text-white transition"
          >
            {loading ? "Analyzing..." : "Analyze Damage"}
          </button>

          {error && <p className="text-red-400 text-sm">{error}</p>}

          <div className="text-xs text-slate-500 space-y-1 pt-2 border-t border-slate-800">
            <p className="font-medium text-slate-400">Legend</p>
            <p><span className="text-green-400">■</span> No damage</p>
            <p><span className="text-blue-400">■</span> Minor</p>
            <p><span className="text-orange-400">■</span> Major</p>
            <p><span className="text-red-400">■</span> Destroyed</p>
          </div>
        </div>

        <div className="lg:col-span-2 space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-slate-500 mb-1">Pre-disaster</p>
              {preUrl ? (
                <img src={preUrl} alt="Pre disaster" className="rounded border border-slate-700 w-full" />
              ) : (
                <div className="h-40 rounded border border-dashed border-slate-700 flex items-center justify-center text-slate-600 text-sm">
                  No image
                </div>
              )}
            </div>
            <div>
              <p className="text-xs text-slate-500 mb-1">Post-disaster + damage overlay</p>
              {postUrl ? (
                <DamageCanvas postImageUrl={postUrl} analysis={analysis} />
              ) : (
                <div className="h-40 rounded border border-dashed border-slate-700 flex items-center justify-center text-slate-600 text-sm">
                  No image
                </div>
              )}
            </div>
          </div>

          <ZoneTable analysis={analysis} />
          <BriefPanel brief={brief} source={briefSource} loading={briefLoading} />
        </div>
      </section>
    </main>
  );
}
