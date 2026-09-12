"use client";

export function TopNav() {
  const navItems = [
    { label: "News", href: "#", active: true },
    { label: "Finance", href: "#" },
    { label: "Sports", href: "#" },
    { label: "Research", href: "#" },
    { label: "Docs", href: "#" },
    { label: "More", href: "#" },
  ];

  return (
    <nav className="flex items-center gap-6 text-sm font-medium ml-8">
      {navItems.map((item) => (
        <a
          key={item.label}
          href={item.href}
          className="transition-colors py-4 border-b-2 relative"
          style={{
            borderColor: item.active ? "var(--color-brand-blue)" : "transparent",
            color: item.active ? "var(--color-text-primary)" : "var(--color-text-secondary)",
            fontWeight: item.active ? 700 : 500,
          }}
        >
          {item.label}
          {item.active && (
             <div className="absolute -bottom-[2px] left-0 right-0 h-[2px] bg-[var(--color-brand-blue)] rounded-t-sm" />
          )}
        </a>
      ))}
    </nav>
  );
}
