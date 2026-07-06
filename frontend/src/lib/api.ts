export interface DamageCounts {
  none: number;
  minor: number;
  major: number;
  destroyed: number;
}

export interface Zone {
  rank: number;
  bbox: number[];
  damage_counts: DamageCounts;
  priority_score: number;
}

export interface AnalysisSummary {
  total_building_pixels: number;
  destroyed_pct: number;
  major_pct: number;
  minor_pct: number;
}

export interface AnalysisResult {
  zones: Zone[];
  summary: AnalysisSummary;
  mask_base64?: string | null;
  pair_id?: string | null;
  inference_mode: string;
}

export interface DemoPair {
  id: string;
  disaster_type: string;
  pre_image: string;
  post_image: string;
}

export interface BriefResponse {
  brief: string;
  source: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchDemoPairs(): Promise<DemoPair[]> {
  const res = await fetch(`${API_BASE}/demo/pairs`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load demo pairs");
  return res.json();
}

export async function analyzeDemoPair(pairId: string): Promise<AnalysisResult> {
  const form = new FormData();
  form.append("demo_pair_id", pairId);
  const res = await fetch(`${API_BASE}/analyze`, { method: "POST", body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function analyzeUpload(
  pre: File,
  post: File
): Promise<AnalysisResult> {
  const form = new FormData();
  form.append("pre_image", pre);
  form.append("post_image", post);
  const res = await fetch(`${API_BASE}/analyze`, { method: "POST", body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function fetchBrief(
  analysis: AnalysisResult,
  context?: string
): Promise<BriefResponse> {
  const res = await fetch(`${API_BASE}/brief`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ analysis, context }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export function demoImageUrl(filename: string): string {
  return `${API_BASE}/demo/images/${filename}`;
}
