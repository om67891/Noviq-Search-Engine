"use client";
import { useCallback, useEffect, useState } from "react";

const KEY = "noviq-search-history";
const MAX = 12;

export function useSearchHistory() {
  const [history, setHistory] = useState<string[]>([]);

  useEffect(() => {
    try {
      const stored = JSON.parse(localStorage.getItem(KEY) ?? "[]");
      if (Array.isArray(stored)) setHistory(stored);
    } catch {}
  }, []);

  const add = useCallback((query: string) => {
    const q = query.trim();
    if (!q) return;
    setHistory((prev) => {
      const next = [q, ...prev.filter((h) => h !== q)].slice(0, MAX);
      localStorage.setItem(KEY, JSON.stringify(next));
      return next;
    });
  }, []);

  const remove = useCallback((query: string) => {
    setHistory((prev) => {
      const next = prev.filter((h) => h !== query);
      localStorage.setItem(KEY, JSON.stringify(next));
      return next;
    });
  }, []);

  const clear = useCallback(() => {
    setHistory([]);
    localStorage.removeItem(KEY);
  }, []);

  return { history, add, remove, clear };
}
