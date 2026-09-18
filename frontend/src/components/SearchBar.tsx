"use client";

import { useEffect, useRef, useState } from "react";
import { RetrievalMode } from "@/types/search";
import { NoviqIcon } from "@/components/NoviqIcon";

interface Props {
  query: string;
  setQuery: (q: string) => void;
  onSearch: () => void;
  loading: boolean;
  mode: RetrievalMode;
  history: string[];
  onRemoveHistory: (q: string) => void;
  glass?: boolean;
}

const SUGGESTIONS = [
  "climate change 2024",
  "quantum computing breakthroughs",
  "prompt injection attacks",
  "cancer treatment research",
  "machine learning trends",
];

export function SearchBar({
  query,
  setQuery,
  onSearch,
  loading,
  mode,
  history,
  onRemoveHistory,
  glass,
}: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const [selectedIdx, setSelectedIdx] = useState(-1);

  // Combine history + suggestions filtered by query
  const items = query.trim()
    ? [...history, ...SUGGESTIONS].filter(
        (s) => s.toLowerCase().includes(query.toLowerCase()) && s !== query
      ).slice(0, 8)
    : history.slice(0, 8);

  // Keyboard shortcut: "/" or Cmd+K to focus
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.key === "/" || (e.key === "k" && (e.metaKey || e.ctrlKey))) && document.activeElement !== inputRef.current) {
        e.preventDefault();
        inputRef.current?.focus();
        setOpen(true);
      }
      if (e.key === "Escape") {
        setOpen(false);
        inputRef.current?.blur();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!open || items.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIdx((i) => Math.min(i + 1, items.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIdx((i) => Math.max(i - 1, -1));
    } else if (e.key === "Enter" && selectedIdx >= 0) {
      e.preventDefault();
      setQuery(items[selectedIdx]);
      setOpen(false);
      setSelectedIdx(-1);
      setTimeout(onSearch, 0);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      setOpen(false);
      onSearch();
    }
  };

  const isHistory = (s: string) => history.includes(s);

  return (
    <div ref={containerRef} className="w-full max-w-2xl relative">
      {/* Glow ring */}
      <div className="absolute -inset-0.5 gradient-bg rounded-2xl blur opacity-0 group-focus-within:opacity-30 transition duration-500 pointer-events-none" />

      <form
        onSubmit={handleSubmit}
        className={`relative flex items-center rounded-2xl shadow-sm border ${glass ? 'backdrop-blur-xl bg-white/20 dark:bg-black/40' : ''}`}
        style={{
          background: glass ? undefined : "var(--color-bg-card)",
          borderColor: open ? "var(--color-border-focus)" : (glass ? "rgba(255,255,255,0.2)" : "var(--color-border)"),
          boxShadow: open ? "0 0 0 3px rgba(79,172,254,0.15)" : undefined,
          transition: "border-color 0.2s, box-shadow 0.2s",
        }}
      >
        {/* Brand Icon */}
        <div className="pl-4 pr-2 flex-shrink-0 flex items-center justify-center">
          <NoviqIcon className="w-5 h-5 drop-shadow-md hover:scale-110 transition-transform" />
        </div>

        <input
          ref={inputRef}
          type="text"
          id="noviq-search-input"
          placeholder={`Search the web... (${typeof window !== 'undefined' && navigator.platform.includes('Mac') ? '⌘K' : 'Ctrl+K'})`}
          value={query}
          onChange={(e) => { setQuery(e.target.value); setSelectedIdx(-1); setOpen(true); }}
          onFocus={() => setOpen(true)}
          onKeyDown={handleKeyDown}
          disabled={loading}
          autoComplete="off"
          className="flex-1 bg-transparent border-none outline-none text-base py-3.5 px-2 disabled:opacity-50"
          style={{ color: "var(--color-text-primary)" }}
          aria-autocomplete="list"
          aria-expanded={open && items.length > 0}
        />

        {/* Clear button */}
        {query && (
          <button
            type="button"
            onClick={() => { setQuery(""); inputRef.current?.focus(); }}
            className="px-2 flex-shrink-0 transition-opacity hover:opacity-70"
            style={{ color: "var(--color-text-muted)" }}
            aria-label="Clear search"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        )}

        {/* Search button */}
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="gradient-bg text-white px-5 py-2.5 m-1.5 rounded-xl font-semibold text-sm shadow-md hover:opacity-90 hover:shadow-lg transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2 flex-shrink-0"
        >
          {loading ? (
            <>
              <svg className="animate-spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M21 12a9 9 0 11-6.219-8.56" />
              </svg>
              Searching
            </>
          ) : (
            "Search"
          )}
        </button>
      </form>

      {/* Autocomplete / History dropdown */}
      {open && items.length > 0 && (
        <div
          className="absolute left-0 right-0 top-full mt-2 rounded-xl shadow-2xl border overflow-hidden z-50 animate-slide-down"
          style={{ background: "var(--color-bg-card)", borderColor: "var(--color-border)" }}
          role="listbox"
        >
          {history.length > 0 && !query.trim() && (
            <div className="flex items-center justify-between px-4 pt-3 pb-1.5">
              <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--color-text-muted)" }}>
                Recent searches
              </span>
              <button
                onClick={() => { onRemoveHistory("__clear_all__"); setOpen(false); }}
                className="text-xs hover:underline transition-opacity"
                style={{ color: "var(--color-text-muted)" }}
              >
                Clear all
              </button>
            </div>
          )}
          {query.trim() && (
            <div className="px-4 pt-3 pb-1.5">
              <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--color-text-muted)" }}>
                Suggestions
              </span>
            </div>
          )}
          <ul className="py-1.5">
            {items.map((item, i) => (
              <li
                key={item}
                role="option"
                aria-selected={i === selectedIdx}
                onClick={() => { setQuery(item); setOpen(false); setTimeout(onSearch, 0); }}
                onMouseEnter={() => setSelectedIdx(i)}
                className="flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-colors"
                style={{
                  background: i === selectedIdx ? "var(--color-bg-hover)" : "transparent",
                  color: "var(--color-text-primary)",
                }}
              >
                {isHistory(item) ? (
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ color: "var(--color-text-muted)", flexShrink: 0 }}>
                    <polyline points="12 8 12 12 14 14" />
                    <path d="M3.05 11a9 9 0 1 0 .5-4.5" />
                    <polyline points="3 3 3 9 9 9" />
                  </svg>
                ) : (
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ color: "var(--color-text-muted)", flexShrink: 0 }}>
                    <circle cx="11" cy="11" r="8" />
                    <line x1="21" y1="21" x2="16.65" y2="16.65" />
                  </svg>
                )}
                <span className="flex-1 text-sm truncate">{item}</span>
                {isHistory(item) && (
                  <button
                    onClick={(e) => { e.stopPropagation(); onRemoveHistory(item); }}
                    className="flex-shrink-0 opacity-40 hover:opacity-100 transition-opacity"
                    style={{ color: "var(--color-text-muted)" }}
                    aria-label={`Remove "${item}" from history`}
                  >
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <line x1="18" y1="6" x2="6" y2="18" />
                      <line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                  </button>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
