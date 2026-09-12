"use client";

import { AgenticSearchResponse } from "@/types/search";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useState } from "react";

interface Props {
  result: AgenticSearchResponse;
}

const TRACE_LABELS: Record<string, string> = {
  planner: "Query Planning",
  retrieval: "Web Discovery",
  security_gate: "Security Scan",
  source_selection: "Source Selection",
  conflict_detection: "Conflict Check",
  answer: "Answer Synthesis",
  citation_validation: "Citation Validation",
};

function ConfidenceArc({ score }: { score: number }) {
  const color = score >= 80 ? "#22c55e" : score >= 50 ? "#f59e0b" : "#ef4444";
  const label = score >= 80 ? "HIGH" : score >= 50 ? "MEDIUM" : "LOW";
  // SVG arc
  const r = 30;
  const circ = Math.PI * r; // half-circumference for 180° arc
  const filled = (score / 100) * circ;
  return (
    <div className="flex flex-col items-center gap-0.5">
      <svg viewBox="0 0 80 44" width="80" height="44">
        <path d="M5,40 A35,35 0 0,1 75,40" fill="none" stroke="var(--color-border)" strokeWidth="8" strokeLinecap="round" />
        <path
          d="M5,40 A35,35 0 0,1 75,40"
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={`${(score / 100) * 110} 110`}
          style={{ transition: "stroke-dasharray 0.8s ease" }}
        />
        <text x="40" y="38" textAnchor="middle" className="text-[11px] font-black" fill={color} fontSize="14" fontWeight="900">
          {score}
        </text>
      </svg>
      <span className="text-[10px] font-bold uppercase tracking-wider" style={{ color }}>{label}</span>
    </div>
  );
}

export function AgenticPanel({ result }: Props) {
  const [traceOpen, setTraceOpen] = useState(false);
  const [whyOpen, setWhyOpen] = useState(false);

  return (
    <div className="card overflow-hidden mb-6 animate-fade-in">
      {/* Header */}
      <div className="px-6 py-4 border-b flex items-center gap-3 justify-between flex-wrap"
        style={{ borderColor: "var(--color-border)", background: "var(--color-bg-tertiary)" }}>
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 gradient-bg rounded-lg flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
            AI
          </div>
          <div>
            <h2 className="font-bold text-base" style={{ color: "var(--color-text-primary)" }}>
              AI Answer
            </h2>
            <p className="text-[11px]" style={{ color: "var(--color-text-muted)" }}>
              {result.latency}s · {result.trust_summary?.total_sources_used ?? 0} sources
            </p>
          </div>
          <span
            className="text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded-full"
            style={{ background: "rgba(142,45,226,0.12)", color: "var(--color-brand-violet)", border: "1px solid rgba(142,45,226,0.25)" }}
          >
            Agentic
          </span>
        </div>
        <ConfidenceArc score={result.confidence_score} />
      </div>

      {/* Answer body */}
      <div className="px-6 py-5">
        {result.insufficient_evidence ? (
          <div
            className="rounded-xl p-4 text-sm font-medium flex items-start gap-3"
            style={{ background: "rgba(245,158,11,0.1)", color: "#b45309", border: "1px solid rgba(245,158,11,0.2)" }}
          >
            <span className="text-lg flex-shrink-0">⚠️</span>
            <p>Insufficient reliable evidence was found for this query. No answer was synthesized to avoid hallucination.</p>
          </div>
        ) : (
          <div className="prose prose-sm max-w-none"
            style={{ "--tw-prose-body": "var(--color-text-secondary)", "--tw-prose-headings": "var(--color-text-primary)" } as React.CSSProperties}>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{result.answer}</ReactMarkdown>
          </div>
        )}

        {/* Warnings */}
        {result.warnings?.length > 0 && (
          <div className="mt-4 rounded-xl p-4 text-sm"
            style={{ background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.2)", color: "#dc2626" }}>
            <p className="font-bold mb-2 flex items-center gap-2">
              <span>🛡️</span> Security Warnings
            </p>
            <ul className="space-y-1 pl-4 list-disc">
              {result.warnings.map((w, i) => <li key={i}>{w}</li>)}
            </ul>
          </div>
        )}

        {/* Conflicts */}
        {result.conflicts?.length > 0 && (
          <div className="mt-4 rounded-xl p-4 text-sm"
            style={{ background: "rgba(245,158,11,0.08)", border: "1px solid rgba(245,158,11,0.2)", color: "#92400e" }}>
            <p className="font-bold mb-3 flex items-center gap-2">
              <span>⚡</span> Source Conflicts ({result.conflicts.length})
            </p>
            <div className="space-y-3">
              {result.conflicts.map((c, i) => (
                <div key={i} className="rounded-lg p-3"
                  style={{ background: "var(--color-bg-card)", border: "1px solid var(--color-border)" }}>
                  <p className="font-semibold mb-1" style={{ color: "var(--color-text-primary)" }}>"{c.claim}"</p>
                  <p style={{ color: "var(--color-text-secondary)" }}>{c.details}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Citations */}
      {result.citations?.length > 0 && (
        <div className="px-6 pb-5">
          <p className="text-xs font-bold uppercase tracking-wider mb-3 flex items-center gap-2"
            style={{ color: "var(--color-text-muted)" }}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
              <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
            </svg>
            Citations
          </p>
          <div className="flex flex-wrap gap-2">
            {result.citations.map((c) => (
              <a
                key={c.citation_id}
                href={c.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all hover:opacity-80"
                style={{
                  background: "var(--color-bg-tertiary)",
                  color: "var(--color-text-secondary)",
                  border: "1px solid var(--color-border)",
                }}
              >
                <img src={`https://www.google.com/s2/favicons?sz=16&domain_url=${new URL(c.url).hostname}`} width={12} height={12} alt="" className="rounded-sm" onError={(e) => (e.currentTarget.style.display = "none")} />
                [{c.citation_id}] {c.title || new URL(c.url).hostname}
              </a>
            ))}
          </div>
        </div>
      )}

      {/* Footer: Why + Trace */}
      <div className="px-6 pb-5 border-t pt-4 space-y-3" style={{ borderColor: "var(--color-border)" }}>
        {/* Why this answer */}
        <div>
          <button
            onClick={() => setWhyOpen(v => !v)}
            className="text-xs font-semibold flex items-center gap-1.5 transition-colors hover:opacity-80"
            style={{ color: "var(--color-text-muted)" }}
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
              className={`transition-transform ${whyOpen ? "rotate-180" : ""}`}>
              <polyline points="6 9 12 15 18 9" />
            </svg>
            Why this answer?
          </button>
          {whyOpen && (
            <div className="mt-3 space-y-2 animate-fade-in">
              {[
                { icon: "✓", text: `Analyzed ${result.trust_summary?.total_sources_used ?? 0} sources across ${result.trust_summary?.domain_diversity ?? 0} unique domains` },
                { icon: "✓", text: `${result.trust_summary?.high_trust_sources ?? 0} sources classified as high trust` },
                ...(result.warnings?.length === 0 ? [{ icon: "✓", text: "No prompt injection threats detected" }] : []),
                ...(result.conflicts?.length > 0 ? [{ icon: "⚡", text: `${result.conflicts.length} conflict(s) found and highlighted` }] : []),
              ].map((item, i) => (
                <div key={i} className="flex items-center gap-2 text-sm" style={{ color: "var(--color-text-secondary)" }}>
                  <span className="text-xs" style={{ color: "var(--color-brand-blue)" }}>{item.icon}</span>
                  {item.text}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Execution trace timeline */}
        {result.execution_trace?.length > 0 && (
          <div>
            <button
              onClick={() => setTraceOpen(v => !v)}
              className="text-xs font-semibold flex items-center gap-1.5 transition-colors hover:opacity-80"
              style={{ color: "var(--color-text-muted)" }}
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
                className={`transition-transform ${traceOpen ? "rotate-180" : ""}`}>
                <polyline points="6 9 12 15 18 9" />
              </svg>
              Execution trace
            </button>
            {traceOpen && (
              <div className="mt-3 flex flex-col gap-0 animate-fade-in">
                {result.execution_trace.map((step, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <div className="flex flex-col items-center">
                      <div className="w-5 h-5 rounded-full gradient-bg flex items-center justify-center text-white text-[9px] font-bold flex-shrink-0">
                        {i + 1}
                      </div>
                      {i < result.execution_trace.length - 1 && (
                        <div className="w-0.5 h-4" style={{ background: "var(--color-border)" }} />
                      )}
                    </div>
                    <span className="text-xs py-1" style={{ color: "var(--color-text-secondary)" }}>
                      {TRACE_LABELS[step] ?? step.replace(/_/g, " ")}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
