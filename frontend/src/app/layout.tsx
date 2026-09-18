import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ThemeToggle } from "@/components/ThemeToggle";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Noviq | Search. Verify. Discover.",
  description:
    "A trust-aware, AI-powered search engine with real-time web discovery, prompt injection protection, and explainable retrieval.",
  keywords: ["search engine", "AI search", "trust", "security", "retrieval"],
  openGraph: {
    title: "Noviq — Search. Verify. Discover.",
    description: "Real-time web discovery with AI-powered trust scoring.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        {/* Prevent dark mode flash */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  var t = localStorage.getItem('noviq-theme') ||
                    (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
                  document.documentElement.setAttribute('data-theme', t);
                } catch(e) {}
              })();
            `,
          }}
        />
      </head>
      <body
        className={`${inter.variable} font-sans`}
        style={{ background: "var(--color-bg-secondary)", color: "var(--color-text-primary)" }}
      >
        {/* Absolute top-right actions (Google style) */}
        <div className="absolute top-4 right-4 z-50 flex items-center gap-4">
          <ThemeToggle />
          <div className="w-8 h-8 rounded-full bg-[var(--color-brand-blue)] text-white flex items-center justify-center font-bold text-sm">
            S
          </div>
        </div>

        {/* ── Main ──────────────────────────────────────────────────────── */}
        <main className="flex-1 flex flex-col">{children}</main>

        {/* ── Footer ────────────────────────────────────────────────────── */}
        <footer
          className="border-t py-6 text-center text-xs"
          style={{ borderColor: "var(--color-border)", color: "var(--color-text-muted)" }}
        >
          <div className="flex items-center justify-center gap-4 flex-wrap">
            <span>Noviq — SecureAgent Search</span>
            <span style={{ color: "var(--color-border)" }}>·</span>
            <span>Search. Verify. Discover.</span>
            <span style={{ color: "var(--color-border)" }}>·</span>
            <span>Live web · SSRF protection · Hybrid RRF · Multi-agent AI</span>
          </div>
        </footer>
      </body>
    </html>
  );
}
