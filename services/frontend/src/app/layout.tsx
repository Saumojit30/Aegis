import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Aegis — Type 2 Diabetes Digital Twin Clinician Dashboard",
  description: "Calibrated 180-min post-meal trajectory forecasting with degradation resilience and what-if simulation.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#0b0f19] text-slate-100 min-h-screen antialiased">
        {children}
      </body>
    </html>
  );
}
