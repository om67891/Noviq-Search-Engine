"use client";

import { useState } from "react";
import { SearchResult } from "@/types/search";

interface Props {
  result: SearchResult;
  index: number;
  layout: "list" | "grid";
}

function TrustBar({ score }: { score: number }) {
  const color =
    score >= 70 ? "#22c55e" :
    score >= 40 ? "#f59e0b" :
    "#ef4444";
  return (
    <div className="flex items-center gap-1.5">
      <div className="trust-bar flex-1" style={{ minWidth: "48px" }}>
        <div className="trust-bar-fill" style={{ width: `${score}%`, background: color }} />
      </div>
      <span className="text-[10px] font-bold tabular-nums" style={{ color, minWidth: "24px" }}>
        {score}
      </span>
    </div>
  );
}

function Favicon({ domain }: { domain: string }) {
  const [err, setErr] = useState(false);
  if (err) {
    return (
      <div className="w-4 h-4 rounded-sm flex items-center justify-center text-[8px] font-bold"
        style={{ background: "var(--color-bg-tertiary)", color: "var(--color-text-muted)" }}>
        {domain[0]?.toUpperCase() ?? "?"}
      </div>
    );
  }
  return (
    <img
      src={`https://www.google.com/s2/favicons?sz=32&domain_url=${domain}`}
      alt=""
      width={16}
      height={16}
      className="rounded-sm flex-shrink-0"
      onError={() => setErr(true)}
    />
  );
}

function Badge({ children, variant = "default" }: { children: React.ReactNode; variant?: "default" | "bm25" | "semantic" | "live" | "trust-high" | "trust-med" | "trust-low" | "danger" | "warning" }) {
  const styles: Record<string, React.CSSProperties> = {
    default:     { background: "var(--color-bg-tertiary)", color: "var(--color-text-muted)" },
    bm25:        { background: "rgba(59,130,246,0.12)", color: "#3b82f6", border: "1px solid rgba(59,130,246,0.25)" },
    semantic:    { background: "rgba(168,85,247,0.12)", color: "#a855f7", border: "1px solid rgba(168,85,247,0.25)" },
    live:        { background: "rgba(16,185,129,0.12)", color: "#10b981", border: "1px solid rgba(16,185,129,0.25)" },
    "trust-high":{ background: "rgba(34,197,94,0.12)",  color: "#22c55e", border: "1px solid rgba(34,197,94,0.25)" },
    "trust-med": { background: "rgba(245,158,11,0.12)", color: "#f59e0b", border: "1px solid rgba(245,158,11,0.25)" },
    "trust-low": { background: "rgba(239,68,68,0.12)",  color: "#ef4444", border: "1px solid rgba(239,68,68,0.25)" },
    danger:      { background: "rgba(239,68,68,0.12)",  color: "#ef4444", border: "1px solid rgba(239,68,68,0.25)" },
    warning:     { background: "rgba(245,158,11,0.12)", color: "#f59e0b", border: "1px solid rgba(245,158,11,0.25)" },
  };
  return (
    <span
      className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full"
      style={styles[variant]}
    >
      {children}
    </span>
  );
}

function copyToClipboard(text: string) {
  navigator.clipboard.writeText(text).catch(() => {});
}

export function ResultCard({ result, index, layout }: Props) {
  const [copied, setCopied] = useState<"url" | "snippet" | null>(null);
  const [expanded, setExpanded] = useState(false);

  const handleCopy = (type: "url" | "snippet") => {
    copyToClipboard(type === "url" ? result.url : (result.snippet ?? ""));
    setCopied(type);
    setTimeout(() => setCopied(null), 1800);
  };

  const trustVariant =
    (result.trust_score ?? 0) >= 70 ? "trust-high" :
    (result.trust_score ?? 0) >= 40 ? "trust-med" :
    "trust-low";

  const isGrid = layout === "grid";

  return (
    <article
      className="card p-5 flex flex-col gap-3 animate-fade-in"
      style={{ animationDelay: `${index * 40}ms` }}
    >
      {/* Header row */}
      <div className="flex items-start gap-3">
        <Favicon domain={result.domain ?? ""} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span className="text-xs font-semibold px-2 py-0.5 rounded"
              style={{ background: "var(--color-bg-tertiary)", color: "var(--color-text-secondary)" }}>
              {result.domain}
            </span>
            {result.retrieval_source_label === "live_web" && (
              <Badge variant="live">🌐 Live</Badge>
            )}
            {result.retrieval_sources?.includes("bm25") && <Badge variant="bm25">BM25</Badge>}
            {result.retrieval_sources?.includes("vector") && <Badge variant="semantic">Semantic</Badge>}
          </div>
          <a
            href={result.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-[10px] hover:underline truncate block"
            style={{ color: "var(--color-text-muted)", maxWidth: "100%" }}
            title={result.url}
          >
            {result.url}
          </a>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={() => handleCopy("url")}
            title="Copy URL"
            className="w-7 h-7 rounded-lg flex items-center justify-center transition-colors hover:bg-[var(--color-bg-hover)]"
            style={{ color: "var(--color-text-muted)" }}
          >
            {copied === "url" ? (
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="2.5">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            ) : (
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" />
              </svg>
            )}
          </button>
          <a
            href={result.url}
            target="_blank"
            rel="noopener noreferrer"
            title="Open in new tab"
            className="w-7 h-7 rounded-lg flex items-center justify-center transition-colors hover:bg-[var(--color-bg-hover)]"
            style={{ color: "var(--color-text-muted)" }}
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6" />
              <polyline points="15 3 21 3 21 9" />
              <line x1="10" y1="14" x2="21" y2="3" />
            </svg>
          </a>
        </div>
      </div>

      {/* Title */}
      <h2 className="text-base font-bold leading-snug">
        <a
          href={result.url}
          target="_blank"
          rel="noopener noreferrer"
          className="hover:underline transition-colors"
          style={{ color: "var(--color-brand-blue)" }}
        >
          {result.title || result.url}
        </a>
      </h2>

      {/* Snippet */}
      {result.snippet && (
        <p className="text-sm leading-relaxed" style={{ color: "var(--color-text-secondary)" }}>
          {isGrid ? result.snippet.slice(0, 160) + (result.snippet.length > 160 ? "…" : "") : result.snippet}
        </p>
      )}

      {/* Trust bar + badges row */}
      <div className="flex items-center gap-3 flex-wrap pt-1 border-t" style={{ borderColor: "var(--color-border)" }}>
        {result.trust_score !== undefined && (
          <div className="flex items-center gap-2 flex-1 min-w-[120px]">
            <span className="text-[10px] font-semibold uppercase" style={{ color: "var(--color-text-muted)" }}>Trust</span>
            <TrustBar score={result.trust_score} />
          </div>
        )}

        <div className="flex gap-1.5 flex-wrap ml-auto">
          {result.trust_level && (
            <Badge variant={trustVariant}>{result.trust_level}</Badge>
          )}
          {result.security_status && result.security_status !== "SAFE" && (
            <Badge variant={result.security_status === "HIGH_RISK" ? "danger" : "warning"}>
              ⚠ {result.security_status.replace("_", " ")}
            </Badge>
          )}
          {result.score !== undefined && (
            <span className="text-[10px] tabular-nums px-1.5" style={{ color: "var(--color-text-muted)" }}>
              score {result.score.toFixed(3)}
            </span>
          )}
        </div>
      </div>

      {/* Expandable trust details */}
      {result.trust_reasons && result.trust_reasons.length > 0 && (
        <div>
          <button
            onClick={() => setExpanded((v) => !v)}
            className="text-xs flex items-center gap-1 transition-colors hover:opacity-80"
            style={{ color: "var(--color-text-muted)" }}
          >
            <svg
              width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
              className={`transition-transform ${expanded ? "rotate-180" : ""}`}
            >
              <polyline points="6 9 12 15 18 9" />
            </svg>
            {expanded ? "Hide" : "Show"} trust details
          </button>
          {expanded && (
            <div
              className="mt-2 p-3 rounded-lg text-xs space-y-1 animate-fade-in"
              style={{ background: "var(--color-bg-tertiary)", color: "var(--color-text-secondary)" }}
            >
              {result.trust_reasons.map((r, i) => (
                <div key={i} className="flex items-center gap-1.5">
                  <span style={{ color: "var(--color-brand-blue)" }}>✓</span>
                  {r}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </article>
  );
}
