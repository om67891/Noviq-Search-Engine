"use client";

interface Props {
  total: number;
  filtered: number;
  latencyMs?: number;
  provider?: string;
  indexed?: number;
  query: string;
  mode: string;
}

export function StatsBar({ total, filtered, latencyMs, provider, indexed, query, mode }: Props) {
  if (total === 0) return null;

  const shareUrl = () => {
    const url = new URL(window.location.href);
    url.searchParams.set("q", query);
    url.searchParams.set("mode", mode);
    navigator.clipboard.writeText(url.toString()).catch(() => {});
  };

  return (
    <div
      className="flex items-center gap-3 text-xs flex-wrap py-2"
      style={{ color: "var(--color-text-muted)" }}
      aria-live="polite"
    >
      <span>
        <b style={{ color: "var(--color-text-primary)" }}>{filtered}</b>
        {filtered !== total && <> of <b>{total}</b></>} results
      </span>

      {indexed !== undefined && indexed > 0 && (
        <>
          <Dot />
          <span>
            <b style={{ color: "#10b981" }}>{indexed}</b> live pages indexed
          </span>
        </>
      )}

      {provider && (
        <>
          <Dot />
          <span
            className="px-2 py-0.5 rounded-full font-semibold uppercase text-[10px]"
            style={{ background: "rgba(79,172,254,0.1)", color: "var(--color-brand-blue)" }}
          >
            {provider}
          </span>
        </>
      )}

      {latencyMs !== undefined && (
        <>
          <Dot />
          <span>{(latencyMs / 1000).toFixed(1)}s</span>
        </>
      )}

      {/* Share link */}
      <button
        onClick={shareUrl}
        className="ml-auto flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-medium transition-colors hover:opacity-80"
        style={{ background: "var(--color-bg-tertiary)", color: "var(--color-text-secondary)" }}
        title="Copy share link"
      >
        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/>
          <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
        </svg>
        Share
      </button>
    </div>
  );
}

function Dot() {
  return <span style={{ color: "var(--color-border)" }}>·</span>;
}
