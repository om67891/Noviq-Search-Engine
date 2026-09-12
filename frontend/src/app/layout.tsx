import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ThemeToggle } from "@/components/ThemeToggle";
import { TopNav } from "@/components/TopNav";

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
        {/* ── Header ────────────────────────────────────────────────────── */}
        <header
          className="sticky top-0 z-50 w-full border-b backdrop-blur-md"
          style={{
            background: "rgba(var(--color-bg-primary-rgb, 255,255,255), 0.85)",
            borderColor: "var(--color-border)",
            backgroundColor: "color-mix(in srgb, var(--color-bg-primary) 85%, transparent)",
          }}
        >
          <div className="container mx-auto px-4 h-16 flex items-center justify-between gap-4">
            {/* Brand */}
            <a href="/" className="flex items-center gap-2 flex-shrink-0">
              <span className="text-xl font-extrabold tracking-tight" style={{ color: "var(--color-text-primary)" }}>
                N<span className="gradient-text">o</span>viq
              </span>
              <span
                className="hidden sm:inline text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-full"
                style={{
                  background: "rgba(79,172,254,0.1)",
                  color: "var(--color-brand-blue)",
                  border: "1px solid rgba(79,172,254,0.2)",
                }}
              >
                Beta
              </span>
            </a>

            {/* Nav */}
            <div className="hidden md:flex flex-1">
              <TopNav />
            </div>

            {/* Right actions */}
            <div className="flex items-center gap-4 flex-shrink-0">
              {/* Keyboard shortcut hint */}
              <span
                className="hidden lg:flex items-center gap-1 text-[11px] px-2 py-1 rounded-lg"
                style={{
                  background: "var(--color-bg-tertiary)",
                  color: "var(--color-text-muted)",
                  border: "1px solid var(--color-border)",
                }}
              >
                <kbd className="font-mono">⌘K</kbd>
                <span>to search</span>
              </span>
              <ThemeToggle />
              <div className="w-8 h-8 rounded-full bg-[var(--color-brand-blue)] text-white flex items-center justify-center font-bold text-sm">
                S
              </div>
            </div>
          </div>
        </header>

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
