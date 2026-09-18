"use client";

import { RetrievalMode } from "@/types/search";

interface Props {
  mode: RetrievalMode;
  setMode: (m: RetrievalMode) => void;
  loading: boolean;
  onModeChange?: () => void;
  glass?: boolean;
}

const MODES: { key: RetrievalMode; label: string; icon: string; desc: string }[] = [
  { key: "keyword",  label: "Keyword",  icon: "🔤", desc: "BM25 lexical match" },
  { key: "semantic", label: "Semantic", icon: "🧠", desc: "Vector similarity" },
  { key: "hybrid",   label: "Hybrid",   icon: "⚡", desc: "BM25 + Semantic RRF" },
  { key: "agentic",  label: "Agentic",  icon: "🤖", desc: "Multi-agent AI answer" },
];

export function ModeSelector({ mode, setMode, loading, onModeChange, glass }: Props) {
  return (
    <div
      className={`inline-flex rounded-xl p-1 gap-0.5 ${glass ? 'backdrop-blur-xl bg-white/10 dark:bg-black/30' : ''}`}
      style={{ 
        background: glass ? undefined : "var(--color-bg-tertiary)", 
        border: glass ? "1px solid rgba(255,255,255,0.2)" : "1px solid var(--color-border)" 
      }}
      role="tablist"
      aria-label="Search mode"
    >
      {MODES.map((m) => (
        <button
          key={m.key}
          role="tab"
          aria-selected={mode === m.key}
          disabled={loading}
          onClick={() => { setMode(m.key); onModeChange?.(); }}
          title={m.desc}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium capitalize transition-all duration-200 disabled:opacity-50"
          style={
            mode === m.key
              ? { background: glass ? "rgba(255,255,255,0.2)" : "var(--color-bg-card)", color: glass ? "#ffffff" : "var(--color-text-primary)", boxShadow: "0 1px 4px rgba(0,0,0,0.08)" }
              : { color: glass ? "rgba(255,255,255,0.7)" : "var(--color-text-muted)" }
          }
        >
          <span className="text-base leading-none">{m.icon}</span>
          <span>{m.label}</span>
        </button>
      ))}
    </div>
  );
}
