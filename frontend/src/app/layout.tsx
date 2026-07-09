import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DisasterIQ — Satellite Disaster-Damage Triage",
  description:
    "AI-powered building damage assessment from pre/post disaster satellite imagery. Deterministic ML scoring, ranked zone triage, English situation briefs. Team DarkNem — AMD Hackathon ACT II.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-diq-bg text-slate-100 antialiased">
        {children}
      </body>
    </html>
  );
}
