"use client";

const SIDEBAR_ITEMS = [
  { label: "News", icon: "📰" },
  { label: "Finance", icon: "📈" },
  { label: "Sports", icon: "🏈" },
  { label: "Mail", icon: "✉️" },
  { label: "Search", icon: "🔍", active: true },
  { label: "Weather", icon: "⛅" },
  { label: "Health", icon: "⚕️" },
  { label: "Technology", icon: "💻" },
  { label: "Travel", icon: "✈️" },
  { label: "Life", icon: "❤️" },
];

export function Sidebar({ onNavigate, currentQuery }: { onNavigate: (query: string) => void, currentQuery?: string }) {
  return (
    <aside className="w-56 flex-shrink-0 hidden lg:block p-4 rounded-xl border animate-fade-in"
      style={{
        background: "var(--color-bg-card)",
        borderColor: "var(--color-border)",
      }}>
      <h3 className="font-bold text-lg mb-4 ml-2" style={{ color: "var(--color-text-primary)" }}>
        Explore More
      </h3>
      <nav className="flex flex-col gap-1">
        {SIDEBAR_ITEMS.map((item) => {
          const isActive = item.active || (currentQuery && currentQuery.toLowerCase().includes(item.label.toLowerCase()));
          return (
            <button
              key={item.label}
              onClick={() => onNavigate(item.label)}
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors font-medium text-sm w-full text-left cursor-pointer"
              style={{
                background: isActive ? "var(--color-bg-hover)" : "transparent",
                color: isActive ? "var(--color-brand-blue)" : "var(--color-text-secondary)",
              }}
            >
              <span className="text-xl">{item.icon}</span>
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
