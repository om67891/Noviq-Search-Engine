"use client";

import { RetrievalMode } from "@/types/search";

interface Props {
  mode: RetrievalMode;
  setMode: (m: RetrievalMode) => void;
  loading: boolean;
  onModeChange?: () => void;
}

const MODES: { key: RetrievalMode; label: string; icon: string; desc: string }[] = [
  { key: "keyword",  label: "Keyword",  icon: "🔤", desc: "BM25 lexical match" },
  { key: "semantic", label: "Semantic", icon: "🧠", desc: "Vector similarity" },
  { key: "hybrid",   label: "Hybrid",   icon: "⚡", desc: "BM25 + Semantic RRF" },
  { key: "agentic",  label: "Agentic",  icon: "🤖", desc: "Multi-agent AI answer" },
];

export function ModeSelector({ mode, setMode, loading, onModeChange }: Props) {
  return (
    <div
      className="inline-flex rounded-xl p-1 gap-0.5"
      style={{ background: "var(--color-bg-tertiary)", border: "1px solid var(--color-border)" }}
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
              ? { background: "var(--color-bg-card)", color: "var(--color-text-primary)", boxShadow: "0 1px 4px rgba(0,0,0,0.08)" }
              : { color: "var(--color-text-muted)" }
          }
        >
          <span className="text-base leading-none">{m.icon}</span>
          <span>{m.label}</span>
        </button>
      ))}
    </div>
  );
}
