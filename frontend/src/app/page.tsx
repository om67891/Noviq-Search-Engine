"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AgenticSearchResponse,
  DEFAULT_FILTERS,
  DiscoveryMeta,
  FilterState,
  RetrievalMode,
  SearchResult,
  SortKey,
  TrustFilter,
} from "@/types/search";

import { SearchBar }       from "@/components/SearchBar";
import { ModeSelector }    from "@/components/ModeSelector";
import { DiscoveryBanner } from "@/components/DiscoveryBanner";
import { ResultCard }      from "@/components/ResultCard";
import { AgenticPanel }    from "@/components/AgenticPanel";
import { FilterPanel }     from "@/components/FilterPanel";
import { StatsBar }        from "@/components/StatsBar";
import { useSearchHistory } from "@/hooks/useSearchHistory";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const TRENDING = [
  "AI safety research 2024",
  "climate change solutions",
  "quantum computing breakthroughs",
  "CRISPR gene editing",
  "prompt injection attacks",
];

/* ─── Filter + sort logic ─────────────────────────────────────────────────── */
const TRUST_MIN: Record<TrustFilter, number> = {
  any: 0, low: 1, medium: 40, high: 70,
};

function applyFilters(results: SearchResult[], filters: FilterState): SearchResult[] {
  let r = results.filter((item) => {
    if (filters.source !== "all") {
      const has = (s: string) => item.retrieval_sources?.includes(s);
      if (filters.source === "bm25"   && !has("bm25"))    return false;
      if (filters.source === "vector" && !has("vector"))  return false;
      if (filters.source === "both"   && (!has("bm25") || !has("vector"))) return false;
    }
    if ((item.trust_score ?? 0) < TRUST_MIN[filters.minTrust]) return false;
    if (filters.safeOnly && item.security_status !== "SAFE") return false;
    return true;
  });

  const key: SortKey = filters.sort;
  if (key === "trust") r = [...r].sort((a, b) => (b.trust_score ?? 0) - (a.trust_score ?? 0));
  else if (key === "domain") r = [...r].sort((a, b) => (a.domain ?? "").localeCompare(b.domain ?? ""));
  // "relevance" = server order, no-op

  return r;
}

/* ─── Skeleton card ───────────────────────────────────────────────────────── */
function SkeletonCard() {
  return (
    <div className="card p-5 flex flex-col gap-3">
      <div className="flex items-center gap-3">
        <div className="skeleton w-4 h-4 rounded-sm" />
        <div className="skeleton w-24 h-4" />
        <div className="skeleton w-16 h-4 ml-auto" />
      </div>
      <div className="skeleton w-3/4 h-5" />
      <div className="space-y-2">
        <div className="skeleton w-full h-3" />
        <div className="skeleton w-5/6 h-3" />
        <div className="skeleton w-4/6 h-3" />
      </div>
    </div>
  );
}

/* ─── Main page ───────────────────────────────────────────────────────────── */
export default function Home() {
  const [query, setQuery]               = useState("");
  const [mode, setMode]                 = useState<RetrievalMode>("hybrid");
  const [results, setResults]           = useState<SearchResult[]>([]);
  const [agenticResult, setAgenticResult] = useState<AgenticSearchResponse | null>(null);
  const [discoveryMeta, setDiscoveryMeta] = useState<DiscoveryMeta | null>(null);
  const [latencyMs, setLatencyMs]       = useState<number | undefined>();
  const [loading, setLoading]           = useState(false);
  const [error, setError]               = useState<string | null>(null);
  const [hasSearched, setHasSearched]   = useState(false);
  const [layout, setLayout]             = useState<"list" | "grid">("list");
  const [filters, setFilters]           = useState<FilterState>(DEFAULT_FILTERS);
  const [showFilters, setShowFilters]   = useState(false);

  const { history, add: addHistory, remove: removeHistory, clear: clearHistory } = useSearchHistory();

  // Read ?q and ?mode from URL on mount
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const q = params.get("q");
    const m = params.get("mode") as RetrievalMode | null;
    if (q) { setQuery(q); if (m) setMode(m); }
  }, []);

  const handleSearch = useCallback(async (overrideQuery?: string, overrideMode?: RetrievalMode) => {
    const q = (overrideQuery ?? query).trim();
    const m = overrideMode ?? mode;
    if (!q) return;

    setLoading(true);
    setError(null);
    setHasSearched(true);
    setAgenticResult(null);
    setDiscoveryMeta(null);
    setResults([]);
    setFilters(DEFAULT_FILTERS);
    addHistory(q);

    // Update URL without reload
    const url = new URL(window.location.href);
    url.searchParams.set("q", q);
    url.searchParams.set("mode", m);
    window.history.replaceState({}, "", url.toString());

    try {
      if (m === "agentic") {
        const res = await fetch(`${API}/api/v1/agentic-search/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query: q, mode: m }),
        });
        if (!res.ok) throw new Error(`Backend error: ${res.status}`);
        const data: AgenticSearchResponse = await res.json();
        setAgenticResult(data);
        setResults(data.sources ?? []);
        setDiscoveryMeta(data.discovery_meta ?? null);
        setLatencyMs(data.latency ? data.latency * 1000 : undefined);
      } else {
        const res = await fetch(`${API}/api/v1/search/?q=${encodeURIComponent(q)}&mode=${m}`);
        if (!res.ok) throw new Error(`Backend error: ${res.status}`);
        const data = await res.json();
        setResults(data.results ?? []);
        setDiscoveryMeta(data.discovery_meta ?? null);
        setLatencyMs(data.latency_ms);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Search failed";
      setError(msg);
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, [query, mode, addHistory]);

  const filtered = useMemo(() => applyFilters(results, filters), [results, filters]);

  const handleRemoveHistory = useCallback((q: string) => {
    if (q === "__clear_all__") clearHistory();
    else removeHistory(q);
  }, [clearHistory, removeHistory]);

  return (
    <div
      className="flex flex-col items-center min-h-[calc(100vh-4rem)] px-4 transition-all duration-500"
      style={{ paddingTop: hasSearched ? "2rem" : "0" }}
    >
      {/* ── Hero / Search bar area ───────────────────────────────────────── */}
      <div
        className={`flex flex-col items-center gap-4 w-full transition-all duration-500 ${
          hasSearched ? "max-w-5xl" : "max-w-3xl justify-center min-h-[calc(100vh-4rem)]"
        }`}
      >
        {/* Brand */}
        <div className={`text-center transition-all duration-500 ${hasSearched ? "mb-0" : "mb-4"}`}>
          <h1 className={`font-extrabold tracking-tight transition-all duration-500 ${hasSearched ? "text-3xl" : "text-6xl md:text-7xl"}`}
            style={{ color: "var(--color-text-primary)" }}>
            N<span className="gradient-text">o</span>viq
          </h1>
          {!hasSearched && (
            <div className="mt-3 space-y-2 animate-fade-in">
              <p className="text-xl font-medium" style={{ color: "var(--color-text-secondary)" }}>
                Search. Verify. Discover.
              </p>
              <p className="text-base max-w-xl mx-auto leading-relaxed" style={{ color: "var(--color-text-muted)" }}>
                A trust-aware AI search engine that discovers real web pages, scans for threats, and explains every result.
              </p>
            </div>
          )}
        </div>

        {/* Search bar */}
        <SearchBar
          query={query}
          setQuery={setQuery}
          onSearch={() => handleSearch()}
          loading={loading}
          mode={mode}
          history={history}
          onRemoveHistory={handleRemoveHistory}
        />

        {/* Mode selector */}
        <ModeSelector
          mode={mode}
          setMode={setMode}
          loading={loading}
          onModeChange={() => hasSearched && handleSearch(query, mode)}
        />

        {/* Discovery banner */}
        <DiscoveryBanner
          loading={loading}
          discoveryMeta={discoveryMeta}
          latencyMs={latencyMs}
        />

        {/* Trending (only on home) */}
        {!hasSearched && (
          <div className="flex flex-col items-center gap-3 mt-2 animate-fade-in">
            <p className="text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--color-text-muted)" }}>
              Try searching
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              {TRENDING.map((t) => (
                <button
                  key={t}
                  onClick={() => { setQuery(t); handleSearch(t); }}
                  className="text-sm px-3 py-1.5 rounded-full transition-all hover:opacity-80"
                  style={{
                    background: "var(--color-bg-card)",
                    border: "1px solid var(--color-border)",
                    color: "var(--color-text-secondary)",
                  }}
                >
                  {t}
                </button>
              ))}
            </div>

            {/* Feature pills */}
            <div className="flex items-center gap-6 mt-4 text-xs" style={{ color: "var(--color-text-muted)" }}>
              {[
                { icon: "🌐", text: "Live web discovery" },
                { icon: "🛡️", text: "SSRF + injection protection" },
                { icon: "⚡", text: "Hybrid RRF ranking" },
                { icon: "🤖", text: "Multi-agent AI answers" },
              ].map((f) => (
                <span key={f.text} className="flex items-center gap-1.5">
                  <span>{f.icon}</span>
                  <span>{f.text}</span>
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ── Results area ────────────────────────────────────────────────── */}
      {hasSearched && (
        <div className="w-full max-w-5xl mt-4 pb-20">

          {/* Error */}
          {error && !loading && (
            <div
              className="rounded-xl p-5 mb-4 animate-fade-in"
              style={{ background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.2)", color: "#dc2626" }}
            >
              <p className="font-bold mb-1 flex items-center gap-2">⚠ Search Failed</p>
              <p className="text-sm">{error}</p>
              <button
                onClick={() => handleSearch()}
                className="mt-3 px-4 py-1.5 rounded-lg text-sm font-semibold transition-colors hover:opacity-80"
                style={{ background: "rgba(239,68,68,0.12)", color: "#dc2626" }}
              >
                Retry
              </button>
            </div>
          )}

          {/* Agentic panel */}
          {!loading && agenticResult && <AgenticPanel result={agenticResult} />}

          {/* Top bar */}
          {!loading && results.length > 0 && (
            <div className="flex items-center gap-3 mb-3">
              <StatsBar
                total={results.length}
                filtered={filtered.length}
                latencyMs={latencyMs}
                provider={discoveryMeta?.provider}
                indexed={discoveryMeta?.indexed}
                query={query}
                mode={mode}
              />
              <div className="flex items-center gap-2 ml-2 flex-shrink-0">
                {/* Filter toggle */}
                <button
                  onClick={() => setShowFilters((v) => !v)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors"
                  style={{
                    background: showFilters ? "rgba(79,172,254,0.12)" : "var(--color-bg-tertiary)",
                    color: showFilters ? "var(--color-brand-blue)" : "var(--color-text-secondary)",
                    border: "1px solid var(--color-border)",
                  }}
                >
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>
                  </svg>
                  Filter
                </button>
                {/* Layout toggle */}
                <button
                  onClick={() => setLayout((v) => v === "list" ? "grid" : "list")}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors"
                  style={{
                    background: "var(--color-bg-tertiary)",
                    color: "var(--color-text-secondary)",
                    border: "1px solid var(--color-border)",
                  }}
                  title={`Switch to ${layout === "list" ? "grid" : "list"} view`}
                >
                  {layout === "list" ? (
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
                      <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
                    </svg>
                  ) : (
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/>
                      <line x1="8" y1="18" x2="21" y2="18"/>
                      <line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/>
                      <line x1="3" y1="18" x2="3.01" y2="18"/>
                    </svg>
                  )}
                  {layout === "list" ? "Grid" : "List"}
                </button>
              </div>
            </div>
          )}

          {/* Body: filter sidebar + results */}
          <div className="flex gap-6">
            {/* Filter sidebar */}
            {showFilters && !loading && results.length > 0 && (
              <div className="animate-fade-in">
                <FilterPanel
                  filters={filters}
                  onChange={setFilters}
                  totalResults={results.length}
                  filteredCount={filtered.length}
                />
              </div>
            )}

            {/* Results */}
            <div className="flex-1 min-w-0">
              {/* Skeleton */}
              {loading && (
                <div className={layout === "grid" ? "grid grid-cols-2 gap-4" : "flex flex-col gap-4"}>
                  {Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)}
                </div>
              )}

              {/* Empty state */}
              {!loading && hasSearched && filtered.length === 0 && !error && (
                <div
                  className="card p-12 text-center animate-fade-in"
                  style={{ color: "var(--color-text-muted)" }}
                >
                  <div className="text-4xl mb-4">🔍</div>
                  <p className="text-lg font-semibold mb-2" style={{ color: "var(--color-text-primary)" }}>
                    {results.length > 0 ? "No results match your filters" : "No results found"}
                  </p>
                  <p className="text-sm max-w-sm mx-auto">
                    {results.length > 0
                      ? "Try adjusting the filter panel on the left."
                      : `No reliable sources were found for "${query}". Try a different query or mode.`}
                  </p>
                  {results.length > 0 && (
                    <button
                      onClick={() => setFilters(DEFAULT_FILTERS)}
                      className="mt-4 px-4 py-2 rounded-lg text-sm font-medium gradient-bg text-white"
                    >
                      Clear filters
                    </button>
                  )}
                </div>
              )}

              {/* Result cards */}
              {!loading && !error && filtered.length > 0 && (
                <>
                  {agenticResult && results.length > 0 && (
                    <h3 className="text-sm font-bold uppercase tracking-wider mb-3"
                      style={{ color: "var(--color-text-muted)" }}>
                      Supporting sources
                    </h3>
                  )}
                  <div className={layout === "grid" ? "grid grid-cols-1 md:grid-cols-2 gap-4" : "flex flex-col gap-4"}>
                    {filtered.map((r, i) => (
                      <ResultCard key={r.id || i} result={r} index={i} layout={layout} />
                    ))}
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
