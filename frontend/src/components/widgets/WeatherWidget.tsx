import React from 'react';

export function WeatherWidget({ data }: { data: any }) {
  if (!data) return null;
  
  return (
    <div className="card p-6 mb-6 flex flex-col md:flex-row gap-6 animate-fade-in relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute top-0 right-0 p-8 opacity-5 text-9xl pointer-events-none select-none">
        {data.condition === 'Sunny' ? '☀️' : '☁️'}
      </div>
      
      <div className="flex-1 z-10">
        <h2 className="text-sm font-bold uppercase tracking-wider mb-4" style={{ color: "var(--color-text-muted)" }}>
          Weather
        </h2>
        
        <div className="flex items-end gap-4 mb-1">
          <div className="text-6xl font-light tracking-tighter" style={{ color: "var(--color-text-primary)" }}>
            {data.temperature}°
          </div>
          <div className="text-xl pb-2 font-medium" style={{ color: "var(--color-brand-blue)" }}>
            {data.condition}
          </div>
        </div>
        
        <div className="text-lg font-medium" style={{ color: "var(--color-text-secondary)" }}>
          {data.location}
        </div>
        <div className="text-sm mt-1 flex gap-3" style={{ color: "var(--color-text-muted)" }}>
          <span>High: <strong style={{ color: "var(--color-text-primary)" }}>{data.high}°</strong></span>
          <span>Low: <strong style={{ color: "var(--color-text-primary)" }}>{data.low}°</strong></span>
        </div>
      </div>
      
      {/* Forecast */}
      <div className="flex gap-4 items-center z-10 pt-6 md:pt-0 border-t md:border-t-0 md:border-l border-[var(--color-border)] md:pl-6">
        {data.forecast?.map((day: any, i: number) => (
          <div key={i} className="flex flex-col items-center gap-2">
            <span className="text-xs uppercase font-semibold" style={{ color: "var(--color-text-muted)" }}>{day.day}</span>
            <span className="text-2xl">{day.icon}</span>
            <span className="text-sm font-medium" style={{ color: "var(--color-text-primary)" }}>{day.temp}°</span>
          </div>
        ))}
      </div>
    </div>
  );
}
