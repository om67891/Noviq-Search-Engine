"use client";

import { FilterState } from "@/types/search";

interface Props {
  filters: FilterState;
  onChange: (f: FilterState) => void;
  totalResults: number;
  filteredCount: number;
}

export function FilterPanel({ filters, onChange, totalResults, filteredCount }: Props) {
  const set = <K extends keyof FilterState>(key: K, val: FilterState[K]) =>
    onChange({ ...filters, [key]: val });

  return (
    <aside
      className="w-48 flex-shrink-0 space-y-5 text-sm"
      aria-label="Filter and sort options"
    >
      <div>
        <p className="text-[11px] font-bold uppercase tracking-wider mb-2" style={{ color: "var(--color-text-muted)" }}>
          Sort by
        </p>
        <div className="space-y-1">
          {(["relevance", "trust", "domain"] as const).map((s) => (
            <button
              key={s}
              onClick={() => set("sort", s)}
              className="w-full text-left px-3 py-1.5 rounded-lg capitalize text-xs font-medium transition-colors"
              style={{
                background: filters.sort === s ? "rgba(79,172,254,0.12)" : "transparent",
                color: filters.sort === s ? "var(--color-brand-blue)" : "var(--color-text-secondary)",
              }}
            >
              {s === "relevance" ? "🎯 Relevance" : s === "trust" ? "🛡 Trust score" : "🌐 Domain"}
            </button>
          ))}
        </div>
      </div>

      <div>
        <p className="text-[11px] font-bold uppercase tracking-wider mb-2" style={{ color: "var(--color-text-muted)" }}>
          Retrieval source
        </p>
        <div className="space-y-1">
          {(["all", "bm25", "vector", "both"] as const).map((s) => (
            <button
              key={s}
              onClick={() => set("source", s)}
              className="w-full text-left px-3 py-1.5 rounded-lg text-xs font-medium transition-colors"
              style={{
                background: filters.source === s ? "rgba(79,172,254,0.12)" : "transparent",
                color: filters.source === s ? "var(--color-brand-blue)" : "var(--color-text-secondary)",
              }}
            >
              {s === "all" ? "All sources" : s === "bm25" ? "BM25 only" : s === "vector" ? "Semantic only" : "Both (hybrid)"}
            </button>
          ))}
        </div>
      </div>

      <div>
        <p className="text-[11px] font-bold uppercase tracking-wider mb-2" style={{ color: "var(--color-text-muted)" }}>
          Minimum trust
        </p>
        <div className="space-y-1">
          {(["any", "low", "medium", "high"] as const).map((t) => (
            <button
              key={t}
              onClick={() => set("minTrust", t)}
              className="w-full text-left px-3 py-1.5 rounded-lg capitalize text-xs font-medium transition-colors"
              style={{
                background: filters.minTrust === t ? "rgba(79,172,254,0.12)" : "transparent",
                color: filters.minTrust === t ? "var(--color-brand-blue)" : "var(--color-text-secondary)",
              }}
            >
              {t === "any" ? "Any" : t === "low" ? "Low+" : t === "medium" ? "Medium+" : "High only"}
            </button>
          ))}
        </div>
      </div>

      <div>
        <p className="text-[11px] font-bold uppercase tracking-wider mb-2" style={{ color: "var(--color-text-muted)" }}>
          Security
        </p>
        <div className="space-y-1">
          {(["all", "safe"] as const).map((s) => (
            <button
              key={s}
              onClick={() => set("safeOnly", s === "safe")}
              className="w-full text-left px-3 py-1.5 rounded-lg text-xs font-medium transition-colors"
              style={{
                background: (s === "safe") === filters.safeOnly ? "rgba(79,172,254,0.12)" : "transparent",
                color: (s === "safe") === filters.safeOnly ? "var(--color-brand-blue)" : "var(--color-text-secondary)",
              }}
            >
              {s === "all" ? "All results" : "Safe only"}
            </button>
          ))}
        </div>
      </div>

      {/* Result count */}
      {totalResults > 0 && (
        <p className="text-[11px] px-1" style={{ color: "var(--color-text-muted)" }}>
          Showing {filteredCount} of {totalResults} results
        </p>
      )}
    </aside>
  );
}
