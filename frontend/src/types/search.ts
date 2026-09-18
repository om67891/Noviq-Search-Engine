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

export interface DiscoveryMeta {
  discovered: number;
  indexed: number;
  provider: string;
}

export interface SearchResult {
  id: string;
  url: string;
  domain: string;
  title: string;
  snippet: string;
  score: number;
  retrieval_sources?: string[];
  retrieval_source_label?: string;
  trust_score?: number;
  trust_level?: string;
  security_risk?: number;
  security_status?: string;
  verification_status?: string;
  trust_reasons?: string[];
  source?: string;
}

export type WidgetType = 'weather' | 'finance';

export interface WidgetData {
  type: WidgetType;
  data: any;
}

export interface SearchResponse {
  query: string;
  mode: RetrievalMode;
  page: number;
  page_size: number;
  total: number;
  results: SearchResult[];
  retrieval_source?: string;
  discovery_meta?: DiscoveryMeta;
  generated_at: string;
  latency_ms?: number;
  warnings?: string[];
  widget?: WidgetData;
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
  discovery_meta?: DiscoveryMeta;
  widget?: WidgetData;
}

export type SortKey = 'relevance' | 'trust' | 'domain';
export type SourceFilter = 'all' | 'bm25' | 'vector' | 'both';
export type TrustFilter = 'any' | 'low' | 'medium' | 'high';

export interface FilterState {
  sort: SortKey;
  source: SourceFilter;
  minTrust: TrustFilter;
  safeOnly: boolean;
}

export const DEFAULT_FILTERS: FilterState = {
  sort: 'relevance',
  source: 'all',
  minTrust: 'any',
  safeOnly: false,
};
