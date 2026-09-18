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
  WidgetData,
} from "@/types/search";

import { SearchBar }       from "@/components/SearchBar";
import { ModeSelector }    from "@/components/ModeSelector";
import { DiscoveryBanner } from "@/components/DiscoveryBanner";
import { ResultCard }      from "@/components/ResultCard";
import { AgenticPanel }    from "@/components/AgenticPanel";
import { FilterPanel }     from "@/components/FilterPanel";
import { StatsBar }        from "@/components/StatsBar";
import { Sidebar }         from "@/components/Sidebar";
import { WidgetContainer } from "@/components/widgets/WidgetContainer";
import { useSearchHistory } from "@/hooks/useSearchHistory";
import { NoviqIcon }       from "@/components/NoviqIcon";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const BENTO_LINKS = [
  { label: "News", icon: "📰", color: "bg-blue-500" },
  { label: "Finance", icon: "📈", color: "bg-green-500" },
  { label: "Tech", icon: "💻", color: "bg-purple-500" },
  { label: "Health", icon: "⚕️", color: "bg-red-500" },
  { label: "Sports", icon: "🏈", color: "bg-orange-500" },
  { label: "Travel", icon: "✈️", color: "bg-teal-500" },
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
  const [widget, setWidget]             = useState<WidgetData | undefined>();

  // New Brave UI states
  const [bgImage, setBgImage] = useState<string | null>(null);
  const [time, setTime] = useState("");

  const { history, add: addHistory, remove: removeHistory, clear: clearHistory } = useSearchHistory();

  // Read ?q and ?mode from URL on mount
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const q = params.get("q");
    const m = params.get("mode") as RetrievalMode | null;
    if (q) { 
      setQuery(q); 
      if (m) setMode(m); 
      // trigger search if URL has query
      handleSearch(q, m ?? "hybrid", true);
    }

    // Set Random Background for Brave UI
    const bgs = ["/backgrounds/bg1.jpg", "/backgrounds/bg2.jpg", "/backgrounds/bg3.jpg"];
    setBgImage(bgs[Math.floor(Math.random() * bgs.length)]);

    // Start Live Clock
    const updateTime = () => {
      setTime(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSearch = useCallback(async (overrideQuery?: string, overrideMode?: RetrievalMode, skipUrlUpdate = false) => {
    const q = (overrideQuery ?? query).trim();
    const m = overrideMode ?? mode;
    if (!q) return;

    setLoading(true);
    setError(null);
    setHasSearched(true);
    setAgenticResult(null);
    setDiscoveryMeta(null);
    setWidget(undefined);
    setResults([]);
    setFilters(DEFAULT_FILTERS);
    addHistory(q);

    // Update URL without reload
    if (!skipUrlUpdate) {
      const url = new URL(window.location.href);
      url.searchParams.set("q", q);
      url.searchParams.set("mode", m);
      window.history.replaceState({}, "", url.toString());
    }

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
        setWidget(data.widget);
        setLatencyMs(data.latency ? data.latency * 1000 : undefined);
      } else {
        const res = await fetch(`${API}/api/v1/search/?q=${encodeURIComponent(q)}&mode=${m}`);
        if (!res.ok) throw new Error(`Backend error: ${res.status}`);
        const data = await res.json();
        setResults(data.results ?? []);
        setDiscoveryMeta(data.discovery_meta ?? null);
        setWidget(data.widget);
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

  // When clicking the logo to go home
  const goHome = () => {
    setHasSearched(false);
    setQuery("");
    setResults([]);
    window.history.replaceState({}, "", "/");
    // Randomize background again when returning home
    const bgs = ["/backgrounds/bg1.jpg", "/backgrounds/bg2.jpg", "/backgrounds/bg3.jpg"];
    setBgImage(bgs[Math.floor(Math.random() * bgs.length)]);
  };

  return (
    <div className={`flex flex-col min-h-screen w-full relative ${!hasSearched ? 'text-white' : ''}`}>
      
      {/* ── Background Image Layer (Only visible BEFORE search) ───────── */}
      {!hasSearched && bgImage && (
        <div className="fixed top-0 left-0 w-full min-h-[100dvh] h-full z-[-1] transition-opacity duration-1000 ease-in-out bg-black">
          <div 
            className="absolute inset-0"
            style={{
              backgroundImage: `url(${bgImage})`,
              backgroundSize: 'cover',
              backgroundPosition: 'center',
              opacity: 0.85 // Slight dimming to make text pop
            }}
          />
        </div>
      )}

      {/* ── Sticky Header (Only visible AFTER search) ──────────────────── */}
      <header
        className={`fixed top-0 left-0 right-0 z-40 w-full border-b backdrop-blur-md transition-all duration-300 ease-in-out ${
          hasSearched ? "translate-y-0 opacity-100" : "-translate-y-full opacity-0 pointer-events-none"
        }`}
        style={{
          background: "rgba(var(--color-bg-primary-rgb, 255,255,255), 0.85)",
          borderColor: "var(--color-border)",
          backgroundColor: "color-mix(in srgb, var(--color-bg-primary) 85%, transparent)",
        }}
      >
        <div className="container mx-auto px-4 h-16 flex items-center gap-6">
          {/* Small Brand Logo */}
          <button onClick={goHome} className="flex items-center gap-2 flex-shrink-0 transition-opacity hover:opacity-80">
            <NoviqIcon className="w-8 h-8" />
            <span className="text-2xl font-extrabold tracking-tight" style={{ color: "var(--color-text-primary)" }}>
              N<span className="gradient-text">o</span>viq
            </span>
          </button>

          {/* Search Bar inside Header */}
          <div className="flex-1 max-w-2xl">
            <div className="flex items-center gap-2">
              <div className="flex-1">
                <SearchBar
                  query={query}
                  setQuery={setQuery}
                  onSearch={() => handleSearch()}
                  loading={loading}
                  mode={mode}
                  history={history}
                  onRemoveHistory={handleRemoveHistory}
                />
              </div>
              <div className="hidden md:block flex-shrink-0 w-64">
                <ModeSelector
                  mode={mode}
                  setMode={setMode}
                  loading={loading}
                  onModeChange={() => handleSearch(query, mode)}
                />
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* ── Main Body (Dynamic Layout) ─────────────────────────────────── */}
      <div 
        className={`flex-1 w-full flex ${
          hasSearched ? "pt-24 items-start" : "items-center justify-center pt-0"
        } transition-all duration-500`}
      >
        {/* ── HOMEPAGE VIEW (!hasSearched) ── */}
        {!hasSearched && (
          <div className="flex flex-col items-center w-full animate-fade-in absolute inset-0 pt-8 overflow-y-auto">
            
            {/* Top Dashboard Header (Stats + Clock) */}
            <div className="w-full flex flex-col md:flex-row justify-between items-center md:items-start px-8 lg:px-16 mb-auto mt-4 gap-4 md:gap-0">
              <div className="flex gap-4 md:gap-8 text-center md:text-left">
                <div>
                  <div className="text-xl md:text-3xl font-light">14,205</div>
                  <div className="text-[10px] md:text-xs uppercase tracking-widest opacity-80 mt-1">Threats Blocked</div>
                </div>
                <div>
                  <div className="text-xl md:text-3xl font-light">42.5<span className="text-lg md:text-xl">s</span></div>
                  <div className="text-[10px] md:text-xs uppercase tracking-widest opacity-80 mt-1">Time Saved</div>
                </div>
                <div className="hidden sm:block">
                  <div className="text-xl md:text-3xl font-light">100<span className="text-lg md:text-xl">%</span></div>
                  <div className="text-[10px] md:text-xs uppercase tracking-widest opacity-80 mt-1">Verified Sources</div>
                </div>
              </div>
              
              <div className="text-4xl md:text-6xl font-extralight tracking-tight drop-shadow-lg text-right">
                {time}
              </div>
            </div>

            {/* Massive Logo & Search Bar Centered */}
            <div className="flex flex-col items-center w-full max-w-3xl px-4 mt-auto mb-auto pt-12 pb-24">
              
              {/* Massive Logo */}
              <div className="mb-10 text-center flex flex-col items-center">
                <h1 className="text-7xl md:text-8xl font-extrabold tracking-tight drop-shadow-2xl">
                  Noviq
                </h1>
              </div>

              {/* Massive Search Bar (Glass) */}
              <div className="w-full mb-6">
                <SearchBar
                  query={query}
                  setQuery={setQuery}
                  onSearch={() => handleSearch()}
                  loading={loading}
                  mode={mode}
                  history={history}
                  onRemoveHistory={handleRemoveHistory}
                  glass={true}
                />
              </div>

              {/* Mode Selector (Glass) */}
              <div className="w-full max-w-lg mb-12">
                <ModeSelector
                  mode={mode}
                  setMode={setMode}
                  loading={loading}
                  onModeChange={() => {}}
                  glass={true}
                />
              </div>

              {/* Quick Links / Bento Grid */}
              <div className="flex gap-4 flex-wrap justify-center max-w-2xl mt-4">
                {BENTO_LINKS.map((link) => (
                  <button 
                    key={link.label}
                    onClick={() => { setQuery(link.label); handleSearch(link.label); }}
                    className="flex flex-col items-center gap-2 p-3 w-20 md:w-24 rounded-2xl backdrop-blur-md bg-white/10 hover:bg-white/20 transition-all cursor-pointer border border-white/10 hover:border-white/30 shadow-lg group"
                  >
                    <div className={`w-10 h-10 md:w-12 md:h-12 ${link.color} rounded-xl flex items-center justify-center text-xl shadow-inner group-hover:scale-110 transition-transform`}>
                      {link.icon}
                    </div>
                    <span className="text-[11px] md:text-xs font-medium opacity-90">{link.label}</span>
                  </button>
                ))}
              </div>
            </div>
            
            <button 
              onClick={() => { setQuery("Latest News"); handleSearch("Latest News"); }}
              className="mb-8 mt-auto opacity-60 text-xs tracking-widest uppercase hover:opacity-100 transition-opacity cursor-pointer flex flex-col items-center gap-2"
            >
              <span>Scroll for Noviq News</span>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </button>
          </div>
        )}


        {/* ── RESULTS VIEW (hasSearched) ── */}
        {hasSearched && (
          <div className="container mx-auto flex gap-8 px-4 pb-20 w-full animate-fade-in relative z-10">
            {/* Left Sidebar (Yahoo Style Portal Features) */}
            <div className="hidden lg:block w-64 flex-shrink-0">
              <Sidebar 
                currentQuery={query}
                onNavigate={(q) => {
                  setQuery(q);
                  handleSearch(q);
                }} 
              />
            </div>

            {/* Main Content Area */}
            <div className="flex-1 min-w-0 max-w-4xl">
              {/* Discovery banner */}
              <DiscoveryBanner
                loading={loading}
                discoveryMeta={discoveryMeta}
                latencyMs={latencyMs}
              />

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

              {/* Top bar for filtering/stats */}
              {!loading && results.length > 0 && (
                <div className="flex flex-wrap items-center gap-3 mb-4">
                  <StatsBar
                    total={results.length}
                    filtered={filtered.length}
                    latencyMs={latencyMs}
                    provider={discoveryMeta?.provider}
                    indexed={discoveryMeta?.indexed}
                    query={query}
                    mode={mode}
                  />
                  <div className="flex items-center gap-2 ml-auto flex-shrink-0">
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
              <div className="flex gap-6 items-start">
                {/* Filter Panel (Slide Down) */}
                {showFilters && !loading && results.length > 0 && (
                  <div className="w-56 flex-shrink-0 animate-fade-in sticky top-24">
                    <FilterPanel
                      filters={filters}
                      onChange={setFilters}
                      totalResults={results.length}
                      filteredCount={filtered.length}
                    />
                  </div>
                )}

                {/* Results List */}
                <div className="flex-1 min-w-0">
                  {/* Skeleton */}
                  {loading && (
                    <div className={layout === "grid" ? "grid grid-cols-2 gap-4" : "flex flex-col gap-4"}>
                      {Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)}
                    </div>
                  )}

                  {/* Empty state */}
                  {!loading && filtered.length === 0 && !error && (
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
                          className="mt-4 px-4 py-2 rounded-lg text-sm font-medium gradient-bg text-white hover:opacity-90"
                        >
                          Clear filters
                        </button>
                      )}
                    </div>
                  )}

                  {/* Widgets */}
                  {!loading && !error && widget && (
                    <WidgetContainer widget={widget} />
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
            
            {/* Right Margin to balance Sidebar */}
            <div className="hidden xl:block w-32 flex-shrink-0"></div>
          </div>
        )}
      </div>
    </div>
  );
}
