import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Disaster Damage Triage | DarkNem",
  description: "Satellite building damage assessment for emergency response",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-950 text-slate-100 antialiased">
        {children}
      </body>
    </html>
  );
}
