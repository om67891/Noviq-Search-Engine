"use client";

import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { 
  AgenticSearchResponse, 
  SearchResult, 
  RetrievalMode 
} from '../types/search';

// Loading stages to cycle through during agentic search
const LOADING_STAGES = [
  "Planning query...",
  "Retrieving sources...",
  "Checking source safety...",
  "Verifying evidence...",
  "Building answer..."
];

export default function Home() {
  const [query, setQuery] = useState('');
  const [mode, setMode] = useState<RetrievalMode>('hybrid');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [agenticResult, setAgenticResult] = useState<AgenticSearchResponse | null>(null);
  
  const [loading, setLoading] = useState(false);
  const [loadingStageIdx, setLoadingStageIdx] = useState(0);
  
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [expandedSources, setExpandedSources] = useState<Set<string>>(new Set());

  // Cycle loading messages for agentic mode
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (loading && mode === 'agentic') {
      interval = setInterval(() => {
        setLoadingStageIdx(prev => Math.min(prev + 1, LOADING_STAGES.length - 1));
      }, 1500); // Progress stage every 1.5 seconds
    }
    return () => clearInterval(interval);
  }, [loading, mode]);

  const toggleSource = (id: string) => {
    setExpandedSources(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) newSet.delete(id);
      else newSet.add(id);
      return newSet;
    });
  };

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;
    
    setLoading(true);
    setLoadingStageIdx(0);
    setError(null);
    setHasSearched(true);
    setAgenticResult(null);
    setExpandedSources(new Set());
    
    try {
      if (mode === 'agentic') {
        const res = await fetch(`http://localhost:8000/api/v1/agentic-search/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query, mode })
        });
        if (!res.ok) throw new Error('Failed to fetch agentic results from backend');
        const data: AgenticSearchResponse = await res.json();
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

  const currentLoadingText = mode === 'agentic' ? LOADING_STAGES[loadingStageIdx] : "Searching...";

  return (
    <div className={`flex flex-col items-center min-h-[calc(100vh-4rem)] px-4 bg-[var(--color-bg-secondary)] transition-all duration-500 ${hasSearched ? 'justify-start pt-8' : 'justify-center'}`}>
      
      {/* Hero Section */}
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
              Ask a question and Noviq will search, assess, verify, and explain the evidence.
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
            disabled={loading}
            className="flex-1 bg-transparent border-none outline-none text-lg py-3 px-2 text-[var(--color-text-primary)] placeholder-gray-400 disabled:opacity-50"
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
              disabled={loading}
              onClick={() => { setMode(m); if (hasSearched) setTimeout(handleSearch, 0); }}
              className={`px-4 py-1.5 text-sm font-medium rounded-md capitalize transition-colors disabled:opacity-50 ${
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
            <p className="text-gray-600 font-medium">{currentLoadingText}</p>
            {mode === 'agentic' && (
              <div className="flex gap-1 mt-3">
                {LOADING_STAGES.map((_, i) => (
                  <div key={i} className={`h-1.5 w-6 rounded-full transition-colors duration-300 ${i <= loadingStageIdx ? 'bg-[var(--color-brand-blue)]' : 'bg-gray-200'}`}></div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Error State */}
      {error && !loading && (
        <div className="w-full max-w-4xl bg-red-50 border border-red-200 text-red-800 rounded-xl p-6 my-4 shadow-sm">
          <div className="flex items-center gap-2 mb-2">
            <svg className="w-5 h-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
            </svg>
            <p className="font-bold text-lg">Search Failed</p>
          </div>
          <p className="text-sm">{error}</p>
          <button onClick={handleSearch} className="mt-4 px-4 py-2 bg-red-100 text-red-700 font-semibold rounded-md hover:bg-red-200 transition-colors">
            Retry Search
          </button>
        </div>
      )}

      {/* Agentic Result Panel */}
      {!loading && agenticResult && (
        <div className="w-full max-w-4xl bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden mb-8 text-left transition-all">
          
          <div className="p-6 md:p-8">
            <div className="flex justify-between items-start mb-6 pb-4 border-b border-gray-100">
              <div className="flex items-center gap-3">
                <h2 className="text-2xl font-bold text-gray-900">AI Answer</h2>
                <span className="bg-[var(--color-brand-violet)] text-white text-[10px] px-2 py-1 rounded font-bold uppercase tracking-wider">
                  Agentic Mode
                </span>
              </div>
              <div className="flex flex-col items-end gap-2">
                <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide border ${
                  agenticResult.confidence_score >= 80 ? 'bg-emerald-50 text-emerald-800 border-emerald-200' :
                  agenticResult.confidence_score >= 50 ? 'bg-yellow-50 text-yellow-800 border-yellow-200' :
                  'bg-orange-50 text-orange-800 border-orange-200'
                }`}>
                  {agenticResult.confidence_score >= 80 ? 'HIGH' : agenticResult.confidence_score >= 50 ? 'MEDIUM' : 'LOW'} Confidence ({agenticResult.confidence_score})
                </span>
                <span className="text-xs text-gray-400 font-medium">
                  {agenticResult.latency}s
                </span>
              </div>
            </div>
            
            <div className="prose prose-slate max-w-none mb-8 text-gray-800">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {agenticResult.answer}
              </ReactMarkdown>
            </div>

            {agenticResult.insufficient_evidence && (
              <div className="bg-orange-50 text-orange-800 text-sm p-4 rounded-lg mb-8 font-medium border border-orange-100 flex gap-3 items-start">
                <svg className="w-5 h-5 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p>Not enough reliable evidence was found to provide a highly confident answer. The response is based on limited available sources.</p>
              </div>
            )}

            {agenticResult.warnings && agenticResult.warnings.length > 0 && (
              <div className="bg-red-50 text-red-800 text-sm p-4 rounded-lg mb-8 font-medium border border-red-100">
                <div className="flex items-center gap-2 mb-2">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                  </svg>
                  <span className="font-bold text-base">Security / System Warnings</span>
                </div>
                <ul className="list-disc pl-7 space-y-1">
                  {agenticResult.warnings.map((w: string, i: number) => (
                    <li key={i}>{w}</li>
                  ))}
                </ul>
              </div>
            )}
            
            {agenticResult.conflicts && agenticResult.conflicts.length > 0 && (
              <div className="bg-yellow-50 text-yellow-900 text-sm p-4 rounded-lg mb-8 font-medium border border-yellow-200">
                <div className="flex items-center gap-2 mb-3">
                  <svg className="w-5 h-5 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="font-bold text-base">Sources Disagree</span>
                </div>
                <div className="space-y-4">
                  {agenticResult.conflicts.map((conflict, i) => (
                    <div key={i} className="bg-white p-3 rounded border border-yellow-100">
                      <p className="font-semibold text-yellow-800 mb-1">Claim in Question:</p>
                      <p className="mb-2 italic">"{conflict.claim}"</p>
                      <p className="font-semibold text-yellow-800 mb-1">Conflict Details:</p>
                      <p>{conflict.details}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              {/* Citations */}
              <div className="bg-gray-50 border border-gray-100 p-5 rounded-xl">
                <h3 className="text-sm font-bold uppercase tracking-wider text-gray-500 mb-3 flex items-center gap-2">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path></svg>
                  Citations
                </h3>
                {agenticResult.citations && agenticResult.citations.length > 0 ? (
                  <ul className="space-y-2">
                    {agenticResult.citations.map((c: any, i: number) => (
                      <li key={i} className="text-sm text-gray-700 flex items-start gap-2 bg-white p-2 rounded shadow-sm border border-gray-100">
                        <span className="font-bold text-[var(--color-brand-blue)] min-w-[24px]">[{c.citation_id}]</span>
                        <a href={c.url} target="_blank" rel="noopener noreferrer" className="hover:underline hover:text-[var(--color-brand-blue)] line-clamp-2">
                          {c.title || c.url}
                        </a>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-gray-500 italic">No direct citations available.</p>
                )}
              </div>
              
              {/* Why this answer? */}
              <div className="bg-gray-50 border border-gray-100 p-5 rounded-xl flex flex-col justify-between">
                <div className="mb-4">
                  <h3 className="text-sm font-bold uppercase tracking-wider text-gray-500 mb-3 flex items-center gap-2">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
                    Why this answer?
                  </h3>
                  <ul className="text-sm text-gray-700 space-y-2">
                    <li className="flex items-center gap-2">
                      <svg className="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path></svg>
                      Analyzed <b>{agenticResult.trust_summary.total_sources_used || 0}</b> sources across <b>{agenticResult.trust_summary.domain_diversity || 0}</b> unique domains.
                    </li>
                    <li className="flex items-center gap-2">
                      <svg className="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path></svg>
                      <b>{agenticResult.trust_summary.high_trust_sources || 0}</b> sources are classified as High Trust.
                    </li>
                    {agenticResult.warnings?.length === 0 && (
                      <li className="flex items-center gap-2">
                        <svg className="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path></svg>
                        No high-risk prompt injection threats detected.
                      </li>
                    )}
                    {agenticResult.conflicts?.length > 0 && (
                      <li className="flex items-center gap-2 text-yellow-700">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                        Identified {agenticResult.conflicts.length} conflict(s) among sources.
                      </li>
                    )}
                  </ul>
                </div>
                
                <div>
                  <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400 mb-2">Execution Trace</h3>
                  <div className="flex flex-wrap gap-1.5">
                    {agenticResult.execution_trace?.map((step: string, i: number) => (
                      <span key={i} className="flex items-center gap-1 text-[10px] bg-white border border-gray-200 text-gray-500 px-1.5 py-0.5 rounded shadow-sm">
                        {step.replace(/_/g, ' ')}
                        {i < agenticResult.execution_trace.length - 1 && (
                          <svg className="w-2.5 h-2.5 text-gray-300 ml-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"></path></svg>
                        )}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
              
            </div>
          </div>
        </div>
      )}

      {/* Results List */}
      {!loading && !error && hasSearched && (
        <div className="w-full max-w-4xl flex flex-col gap-5 pb-16 text-left">
          
          {agenticResult && results.length > 0 && (
            <h3 className="text-lg font-bold text-gray-800 border-b border-gray-200 pb-2 mb-2">Supporting Sources</h3>
          )}
          
          {results.length === 0 ? (
            <div className="bg-white border border-gray-100 rounded-2xl p-12 text-center shadow-sm">
              <div className="bg-gray-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p className="text-xl text-gray-800 font-medium mb-2">No reliable results found.</p>
              <p className="text-gray-500 max-w-md mx-auto">Your search - <strong>{query}</strong> - did not match any documents or reliable sources. Try adjusting your wording or selecting a broader search mode.</p>
            </div>
          ) : (
            results.map((result, idx) => {
              const isExpanded = expandedSources.has(result.id || idx.toString());
              
              return (
                <div key={result.id || idx} className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow text-left">
                  <div className="flex flex-wrap items-center gap-2 mb-3 text-sm">
                    <span className="font-semibold text-gray-900 bg-gray-100 px-2 py-0.5 rounded">{result.domain}</span>
                    <span className="text-gray-300">&bull;</span>
                    <a href={result.url} target="_blank" rel="noopener noreferrer" className="text-gray-500 hover:text-[var(--color-brand-blue)] truncate max-w-[200px] md:max-w-xs text-xs">
                      {result.url}
                    </a>
                    
                    {/* Badges Align Right */}
                    <div className="flex gap-1.5 ml-auto">
                      {result.retrieval_sources && (
                        <div className="flex gap-1">
                          {result.retrieval_sources.includes('bm25') && <span className="bg-blue-50 text-blue-700 border border-blue-100 text-[10px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider">BM25</span>}
                          {result.retrieval_sources.includes('vector') && <span className="bg-purple-50 text-purple-700 border border-purple-100 text-[10px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider">Semantic</span>}
                        </div>
                      )}
                      
                      {result.trust_level && (
                        <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase tracking-wider border ${
                          result.trust_level === 'High' ? 'bg-green-50 text-green-700 border-green-200' :
                          result.trust_level === 'Medium' ? 'bg-yellow-50 text-yellow-700 border-yellow-200' :
                          'bg-gray-50 text-gray-700 border-gray-200'
                        }`}>
                          Trust: {result.trust_level} ({result.trust_score})
                        </span>
                      )}
                      
                      {result.security_status && result.security_status !== 'SAFE' && (
                        <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase tracking-wider border flex items-center gap-1 ${
                          result.security_status === 'HIGH_RISK' ? 'bg-red-50 text-red-700 border-red-200' :
                          'bg-orange-50 text-orange-700 border-orange-200'
                        }`}>
                          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                          </svg>
                          {result.security_status}
                        </span>
                      )}
                    </div>
                  </div>
                  
                  <h2 className="text-xl font-bold mb-2">
                    <a href={result.url} target="_blank" rel="noopener noreferrer" className="text-[var(--color-brand-blue)] hover:underline">
                      {result.title || result.url}
                    </a>
                  </h2>
                  <p className="text-gray-700 leading-relaxed text-sm mb-3">
                    {result.snippet}
                  </p>
                  
                  {/* Expandable Details */}
                  {result.trust_reasons && result.trust_reasons.length > 0 && (
                    <div>
                      <button 
                        onClick={() => toggleSource(result.id || idx.toString())}
                        className="text-xs font-semibold text-gray-500 hover:text-gray-800 flex items-center gap-1 transition-colors"
                      >
                        {isExpanded ? 'Hide Details' : 'Show Details'}
                        <svg className={`w-3 h-3 transform transition-transform ${isExpanded ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                        </svg>
                      </button>
                      
                      {isExpanded && (
                        <div className="mt-3 bg-gray-50 p-4 rounded-lg border border-gray-100 text-sm text-gray-700 grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <p className="font-bold text-gray-900 mb-1">Trust Validation:</p>
                            <ul className="list-disc pl-5 space-y-1">
                              {result.trust_reasons.map((r, i) => (
                                <li key={i}>{r}</li>
                              ))}
                            </ul>
                          </div>
                          <div>
                            <p className="font-bold text-gray-900 mb-1">Verification Status:</p>
                            <p className="font-medium text-gray-600">
                              {result.verification_status || (mode === 'agentic' ? 'VERIFIED' : 'UNVERIFIED')}
                            </p>
                            {result.security_status === 'HIGH_RISK' && (
                              <p className="text-red-600 font-medium mt-2 flex items-center gap-1">
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                                </svg>
                                Excluded or Heavily Down-ranked
                              </p>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      )}

      {/* Feature Tease */}
      {!hasSearched && (
        <div className="mt-8 flex items-center justify-center gap-6 md:gap-10 text-sm text-gray-500 font-medium flex-wrap">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 text-[var(--color-brand-cyan)]" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path></svg>
            Verify Claims
          </div>
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 text-[var(--color-brand-blue)]" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path></svg>
            Safe & Secure
          </div>
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 text-[var(--color-brand-violet)]" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9.5a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z"></path></svg>
            Explainable AI
          </div>
        </div>
      )}
    </div>
  );
}
