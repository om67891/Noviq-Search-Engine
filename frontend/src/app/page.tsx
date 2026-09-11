"use client";

import React, { useState } from 'react';

type SearchResult = {
  id: string;
  url: string;
  domain: string;
  title: string;
  snippet: string;
  score: number;
  retrieval_sources?: string[];
  trust_score?: number;
  trust_level?: string;
  security_risk?: number;
  security_status?: string;
};

export default function Home() {
  const [query, setQuery] = useState('');
  const [mode, setMode] = useState<'hybrid' | 'semantic' | 'keyword' | 'agentic'>('hybrid');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [agenticResult, setAgenticResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);
  
  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;
    
    setLoading(true);
    setError(null);
    setHasSearched(true);
    setAgenticResult(null);
    
    try {
      if (mode === 'agentic') {
        const res = await fetch(`http://localhost:8000/api/v1/agentic-search/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query, mode })
        });
        if (!res.ok) throw new Error('Failed to fetch agentic results from backend');
        const data = await res.json();
        setAgenticResult(data);
        setResults(data.sources || []);
      } else {
        const res = await fetch(`http://localhost:8000/api/v1/search/?q=${encodeURIComponent(query)}&mode=${mode}`);
        if (!res.ok) throw new Error('Failed to fetch results from backend');
        const data = await res.json();
        setResults(data.results || []);
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred during search. Please ensure the backend is running.');
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`flex flex-col items-center min-h-[calc(100vh-4rem)] px-4 bg-[var(--color-bg-secondary)] transition-all duration-500 ${hasSearched ? 'justify-start pt-8' : 'justify-center'}`}>
      
      {/* Hero Section (smaller when searched) */}
      <div className={`max-w-3xl w-full text-center space-y-4 mb-8 transition-all duration-500 ${hasSearched ? 'scale-75 mb-4' : 'scale-100 mb-12'}`}>
        <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-[var(--color-navy-900)]">
          N<span className="gradient-text">o</span>viq
        </h1>
        
        {!hasSearched && (
          <>
            <p className="text-xl md:text-2xl font-medium text-[var(--color-text-primary)]">
              Search. Verify. Discover.
            </p>
            <p className="text-base md:text-lg text-[var(--color-text-secondary)] max-w-2xl mx-auto leading-relaxed">
              A secure, trust-aware AI search experience <br className="hidden md:block"/>
              built to find relevant information, evaluate sources, and explain the evidence.
            </p>
          </>
        )}
      </div>

      {/* Search Bar */}
      <div className="w-full max-w-2xl relative group mb-2">
        <div className="absolute -inset-0.5 gradient-bg rounded-2xl blur opacity-25 group-hover:opacity-50 transition duration-500"></div>
        <form onSubmit={handleSearch} className="relative bg-white rounded-2xl shadow-sm border border-gray-100 flex items-center p-2 focus-within:ring-2 focus-within:ring-[var(--color-brand-blue)] focus-within:border-transparent transition-all">
          <div className="pl-4 pr-2 text-gray-400">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            </svg>
          </div>
          <input 
            type="text" 
            placeholder="Search the web..." 
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1 bg-transparent border-none outline-none text-lg py-3 px-2 text-[var(--color-text-primary)] placeholder-gray-400"
          />
          <button 
            type="submit"
            disabled={loading || !query.trim()}
            className="gradient-bg text-white px-6 py-3 rounded-xl font-medium shadow-md hover:shadow-lg transform hover:-translate-y-0.5 transition-all disabled:opacity-50 disabled:hover:translate-y-0"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </form>
      </div>

      {/* Mode Selector */}
      <div className="w-full max-w-2xl flex justify-center mb-8">
        <div className="inline-flex bg-white rounded-lg p-1 shadow-sm border border-gray-100">
          {(['keyword', 'semantic', 'hybrid', 'agentic'] as const).map((m) => (
            <button
              key={m}
              onClick={() => { setMode(m); if (hasSearched) setTimeout(handleSearch, 0); }}
              className={`px-4 py-1.5 text-sm font-medium rounded-md capitalize transition-colors ${
                mode === m 
                  ? 'bg-[var(--color-brand-blue)] text-white shadow-sm' 
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }`}
            >
              {m}
            </button>
          ))}
        </div>
      </div>
      
      {/* Loading State */}
      {loading && (
        <div className="w-full max-w-4xl flex justify-center my-12">
          <div className="flex flex-col items-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-brand-blue)] mb-4"></div>
            <p className="text-gray-500">Searching and verifying...</p>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && !loading && (
        <div className="w-full max-w-4xl bg-red-50 border border-red-200 text-red-800 rounded-xl p-4 my-8">
          <p className="font-medium">Error</p>
          <p className="text-sm mt-1">{error}</p>
        </div>
      )}

      {/* Agentic Result Panel */}
      {!loading && agenticResult && (
        <div className="w-full max-w-4xl bg-white border border-gray-200 rounded-xl shadow-sm p-6 mb-8 text-left transition-all">
          <div className="flex justify-between items-start mb-4 border-b border-gray-100 pb-4">
            <h2 className="text-xl font-bold text-gray-900">Final Answer</h2>
            <div className="flex flex-col items-end gap-2">
              <span className={`px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wide ${
                agenticResult.confidence_score >= 80 ? 'bg-emerald-100 text-emerald-800' :
                agenticResult.confidence_score >= 50 ? 'bg-yellow-100 text-yellow-800' :
                'bg-red-100 text-red-800'
              }`}>
                {agenticResult.confidence_score}% Confidence
              </span>
              <span className="text-xs text-gray-500 font-medium">
                Latency: {agenticResult.latency}s
              </span>
            </div>
          </div>
          
          <p className="text-gray-800 leading-relaxed mb-6 whitespace-pre-wrap">{agenticResult.answer}</p>

          {agenticResult.insufficient_evidence && (
            <div className="bg-orange-50 text-orange-800 text-sm p-3 rounded-md mb-6 font-medium border border-orange-100">
              ⚠️ Insufficient evidence to confidently answer the query.
            </div>
          )}

          {agenticResult.warnings && agenticResult.warnings.length > 0 && (
            <div className="bg-red-50 text-red-800 text-sm p-3 rounded-md mb-6 font-medium border border-red-100">
              <span className="font-bold">Security / System Warnings:</span>
              <ul className="list-disc pl-5 mt-1">
                {agenticResult.warnings.map((w: string, i: number) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          )}
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Citations */}
            {agenticResult.citations && agenticResult.citations.length > 0 && (
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="text-xs font-bold uppercase tracking-wider text-gray-500 mb-2">Citations</h3>
                <ul className="space-y-1">
                  {agenticResult.citations.map((c: any, i: number) => (
                    <li key={i} className="text-sm text-gray-700">
                      <span className="font-medium mr-2">[{c.citation_id}]</span>
                      <a href={c.url} target="_blank" rel="noopener noreferrer" className="text-[var(--color-brand-blue)] hover:underline truncate inline-block max-w-[250px] align-bottom">
                        {c.title || c.url}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            
            {/* Trust Summary & Trace */}
            <div className="bg-gray-50 p-4 rounded-lg flex flex-col justify-between">
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-gray-500 mb-2">Trust Summary</h3>
                <div className="text-sm text-gray-700 mb-4">
                  <p>Sources Used: <b>{agenticResult.trust_summary.total_sources_used || 0}</b></p>
                  <p>High Trust: <span className="text-green-600 font-medium">{agenticResult.trust_summary.high_trust_sources || 0}</span></p>
                </div>
              </div>
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-gray-500 mb-2">Execution Trace</h3>
                <div className="flex flex-wrap gap-1">
                  {agenticResult.execution_trace?.map((step: string, i: number) => (
                    <span key={i} className="text-[10px] bg-gray-200 text-gray-600 px-1.5 py-0.5 rounded uppercase">
                      {step}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Results List */}
      {!loading && !error && hasSearched && (
        <div className="w-full max-w-4xl flex flex-col gap-4 pb-12 text-left">
          {results.length === 0 ? (
            <div className="bg-white border border-gray-100 rounded-2xl p-12 text-center shadow-sm">
              <p className="text-xl text-gray-800 font-medium mb-2">No results found</p>
              <p className="text-gray-500">Your search - <strong>{query}</strong> - did not match any documents.</p>
            </div>
          ) : (
            results.map((result, idx) => (
              <div key={result.id || idx} className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow text-left">
                <div className="flex items-center gap-2 mb-2 text-sm">
                  <span className="font-medium text-gray-700 truncate">{result.domain}</span>
                  <span className="text-gray-400">&bull;</span>
                  <a href={result.url} target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-[var(--color-brand-blue)] truncate flex-1">
                    {result.url}
                  </a>
                  {result.retrieval_sources && (
                    <div className="flex gap-1">
                      {result.retrieval_sources.includes('bm25') && <span className="bg-blue-100 text-blue-800 text-[10px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider">BM25</span>}
                      {result.retrieval_sources.includes('vector') && <span className="bg-purple-100 text-purple-800 text-[10px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider">Semantic</span>}
                    </div>
                  )}
                  
                  {/* Part 4: Trust and Security Badges */}
                  <div className="flex gap-1 ml-auto">
                    {result.trust_level && (
                      <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider ${
                        result.trust_level === 'High' ? 'bg-green-100 text-green-800' :
                        result.trust_level === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {result.trust_level} Trust ({result.trust_score})
                      </span>
                    )}
                    
                    {result.security_status && result.security_status !== 'SAFE' && (
                      <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider flex items-center gap-1 ${
                        result.security_status === 'HIGH_RISK' ? 'bg-red-100 text-red-800' :
                        'bg-orange-100 text-orange-800'
                      }`}>
                        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                        </svg>
                        {result.security_status}
                      </span>
                    )}
                    {result.security_status === 'SAFE' && (
                      <span className="bg-emerald-100 text-emerald-800 text-[10px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider flex items-center gap-1">
                        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        SAFE
                      </span>
                    )}
                  </div>
                </div>
                <h2 className="text-xl font-semibold mb-2">
                  <a href={result.url} target="_blank" rel="noopener noreferrer" className="text-[var(--color-brand-blue)] hover:underline">
                    {result.title || result.url}
                  </a>
                </h2>
                <p className="text-gray-600 leading-relaxed text-sm">
                  {result.snippet}
                </p>
              </div>
            ))
          )}
        </div>
      )}

      {/* Future feature tease / trust badges - only show initially */}
      {!hasSearched && (
        <div className="mt-8 flex items-center justify-center gap-8 text-sm text-gray-500 font-medium">
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-[var(--color-brand-cyan)]" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path></svg>
            Verify Claims
          </div>
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-[var(--color-brand-blue)]" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path></svg>
            Safe & Secure
          </div>
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-[var(--color-brand-violet)]" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9.5a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z"></path></svg>
            Explainable AI
          </div>
        </div>
      )}
    </div>
  );
}
