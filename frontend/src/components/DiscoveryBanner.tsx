"use client";

import { useEffect, useRef, useState } from "react";

interface DiscoveryMeta {
  discovered: number;
  indexed: number;
  provider: string;
}

interface Props {
  loading: boolean;
  discoveryMeta?: DiscoveryMeta | null;
  latencyMs?: number;
}

const STAGES = [
  { key: "search",  label: "Searching web",     icon: "🔍" },
  { key: "fetch",   label: "Fetching pages",     icon: "📡" },
  { key: "index",   label: "Indexing content",   icon: "📑" },
  { key: "rank",    label: "Ranking results",    icon: "⚡" },
];

export function DiscoveryBanner({ loading, discoveryMeta, latencyMs }: Props) {
  const [stageIdx, setStageIdx] = useState(0);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (loading) {
      setStageIdx(0);
      intervalRef.current = setInterval(() => {
        setStageIdx((i) => Math.min(i + 1, STAGES.length - 1));
      }, 1800);
    } else {
      if (intervalRef.current) clearInterval(intervalRef.current);
    }
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [loading]);

  if (!loading && !discoveryMeta) return null;

  return (
    <div
      className="w-full max-w-2xl rounded-xl border px-4 py-3 text-sm animate-fade-in overflow-hidden"
      style={{
        background: "var(--color-bg-card)",
        borderColor: "var(--color-border)",
      }}
    >
      {loading ? (
        <div className="flex flex-col gap-2">
          {/* Stage pills */}
          <div className="flex items-center gap-2 flex-wrap">
            {STAGES.map((stage, i) => (
              <span
                key={stage.key}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium transition-all duration-400"
                style={{
                  background: i <= stageIdx ? "rgba(79,172,254,0.12)" : "var(--color-bg-tertiary)",
                  color: i <= stageIdx ? "var(--color-brand-blue)" : "var(--color-text-muted)",
                  border: `1px solid ${i <= stageIdx ? "rgba(79,172,254,0.3)" : "transparent"}`,
                }}
              >
                <span>{stage.icon}</span>
                <span>{stage.label}</span>
                {i === stageIdx && (
                  <span className="flex gap-0.5 ml-0.5">
                    {[0,1,2].map((d) => (
                      <span
                        key={d}
                        className="w-1 h-1 rounded-full"
                        style={{
                          background: "var(--color-brand-blue)",
                          animation: `bounce-dots 1.2s ease infinite`,
                          animationDelay: `${d * 0.2}s`,
                        }}
                      />
                    ))}
                  </span>
                )}
                {i < stageIdx && (
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                )}
              </span>
            ))}
          </div>
          {/* Progress bar */}
          <div className="h-0.5 rounded-full overflow-hidden" style={{ background: "var(--color-border)" }}>
            <div
              className="h-full gradient-bg rounded-full transition-all duration-1000"
              style={{ width: `${((stageIdx + 1) / STAGES.length) * 100}%` }}
            />
          </div>
        </div>
      ) : discoveryMeta ? (
        <div className="flex items-center gap-3 flex-wrap">
          <span className="font-semibold" style={{ color: "var(--color-brand-blue)" }}>
            Live Web
          </span>
          <span style={{ color: "var(--color-text-muted)" }}>·</span>
          <span style={{ color: "var(--color-text-secondary)" }}>
            <b style={{ color: "var(--color-text-primary)" }}>{discoveryMeta.discovered}</b> pages discovered
          </span>
          <span style={{ color: "var(--color-text-muted)" }}>·</span>
          <span style={{ color: "var(--color-text-secondary)" }}>
            <b style={{ color: "var(--color-text-primary)" }}>{discoveryMeta.indexed}</b> indexed
          </span>
          <span style={{ color: "var(--color-text-muted)" }}>·</span>
          <span
            className="uppercase text-xs font-bold px-2 py-0.5 rounded-full"
            style={{ background: "rgba(79,172,254,0.12)", color: "var(--color-brand-blue)" }}
          >
            {discoveryMeta.provider}
          </span>
          {latencyMs !== undefined && (
            <>
              <span style={{ color: "var(--color-text-muted)" }}>·</span>
              <span style={{ color: "var(--color-text-muted)" }} className="text-xs">
                {(latencyMs / 1000).toFixed(1)}s
              </span>
            </>
          )}
        </div>
      ) : null}
    </div>
  );
}
