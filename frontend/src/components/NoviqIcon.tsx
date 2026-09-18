export function NoviqIcon({ className = "" }: { className?: string }) {
  return (
    <svg 
      xmlns="http://www.w3.org/2000/svg" 
      viewBox="0 0 100 100" 
      className={className}
      width="1em"
      height="1em"
    >
      <defs>
        <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#4facfe" />
          <stop offset="100%" stopColor="#00f2fe" />
        </linearGradient>
        <linearGradient id="nGrad" x1="0%" y1="100%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#ffffff" />
          <stop offset="100%" stopColor="#f0f0f0" />
        </linearGradient>
        <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="4" stdDeviation="4" floodOpacity="0.3" />
        </filter>
      </defs>
      
      {/* Outer glowing circle / shield */}
      <circle cx="50" cy="50" r="45" fill="url(#bgGrad)" filter="url(#shadow)" />
      
      {/* Inner dark accent (optional for depth) */}
      <circle cx="50" cy="50" r="38" fill="#111827" />
      
      {/* The bold 'N' */}
      <path d="M32 68 V32 H42 L58 52 V32 H68 V68 H58 L42 48 V68 Z" fill="url(#nGrad)" />
    </svg>
  );
}
