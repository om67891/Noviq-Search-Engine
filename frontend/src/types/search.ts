export type RetrievalMode = 'keyword' | 'semantic' | 'hybrid' | 'agentic';

export interface Citation {
  citation_id: string;
  source_id: string;
  url: string;
  title: string;
}

export interface TrustSummary {
  total_sources_used: number;
  high_trust_sources: number;
  average_trust_score: number;
  domain_diversity: number;
  evidence_coverage: string;
}

export interface Conflict {
  claim: string;
  details: string;
  source_ids: string[];
}

export interface SearchResult {
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
  verification_status?: string;
  trust_reasons?: string[];
}

export interface AgenticSearchResponse {
  query: string;
  answer: string;
  confidence_score: number;
  citations: Citation[];
  trust_summary: TrustSummary;
  conflicts: Conflict[];
  warnings: string[];
  execution_trace: string[];
  sources: SearchResult[];
  latency: number;
  insufficient_evidence: boolean;
}
