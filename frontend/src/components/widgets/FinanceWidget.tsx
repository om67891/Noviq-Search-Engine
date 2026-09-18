import React from 'react';

export function FinanceWidget({ data }: { data: any }) {
  if (!data) return null;
  
  const isPositive = data.change >= 0;
  const color = isPositive ? '#10b981' : '#ef4444'; // emerald-500 or red-500
  const sign = isPositive ? '+' : '';
  
  // Fake mini sparkline
  const min = Math.min(...data.history);
  const max = Math.max(...data.history);
  const range = max - min || 1;
  const points = data.history.map((val: number, i: number) => {
    const x = (i / (data.history.length - 1)) * 100;
    const y = 100 - ((val - min) / range) * 100;
    return `${x},${y}`;
  }).join(' ');

  return (
    <div className="card p-6 mb-6 animate-fade-in relative overflow-hidden group">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h2 className="text-sm font-bold uppercase tracking-wider mb-1" style={{ color: "var(--color-text-muted)" }}>
            Finance
          </h2>
          <div className="flex items-center gap-2">
            <span className="text-xl font-bold" style={{ color: "var(--color-text-primary)" }}>{data.symbol}</span>
            <span className="text-sm font-medium" style={{ color: "var(--color-text-secondary)" }}>{data.name}</span>
          </div>
        </div>
        
        <div className="text-right">
          <div className="text-4xl font-light tracking-tight mb-1" style={{ color: "var(--color-text-primary)" }}>
            ${data.price.toFixed(2)}
          </div>
          <div className="text-lg font-medium flex items-center justify-end gap-1" style={{ color }}>
            {isPositive ? (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
                <polyline points="17 6 23 6 23 12" />
              </svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polyline points="23 18 13.5 8.5 8.5 13.5 1 6" />
                <polyline points="17 18 23 18 23 12" />
              </svg>
            )}
            {sign}{data.change.toFixed(2)} ({sign}{data.change_percent}%)
          </div>
        </div>
      </div>
      
      {/* Sparkline chart */}
      <div className="h-16 w-full relative mt-2 opacity-80 group-hover:opacity-100 transition-opacity">
        <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="w-full h-full overflow-visible">
          <polyline 
            fill="none" 
            stroke={color} 
            strokeWidth="3" 
            strokeLinecap="round"
            strokeLinejoin="round"
            points={points} 
          />
        </svg>
      </div>
    </div>
  );
}
