import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

import ArticleList from './components/ArticleList';
import SearchBar from './components/SearchBar';

export interface Article {
  id: string;
  title: string;
  description?: string | null;
  url: string;
  source?: string | null;
  published_at?: string | null;
}

interface StatusResponse {
  metrics: Record<string, unknown>;
}

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';

async function fetchArticles(params: Record<string, string | number | undefined>) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.set(key, String(value));
    }
  });
  const response = await axios.get<Article[]>(`${API_BASE}/articles`, { params });
  return response.data;
}

async function fetchStatus() {
  const response = await axios.get<StatusResponse>(`${API_BASE}/status`);
  return response.data;
}

export default function App() {
  const [sourceFilter, setSourceFilter] = useState<string>('');
  const [query, setQuery] = useState<string>('');

  const { data: articles = [], isLoading } = useQuery({
    queryKey: ['articles', sourceFilter, query],
    queryFn: () => fetchArticles({ source: sourceFilter || undefined, q: query || undefined }),
    refetchInterval: 120000,
  });

  const { data: status } = useQuery({
    queryKey: ['status'],
    queryFn: fetchStatus,
    refetchInterval: 300000,
  });

  const sources = useMemo(() => {
    if (!status?.metrics) return [] as string[];
    const rawSources = (status.metrics['sources'] as string[]) ?? [];
    return Array.from(new Set(rawSources)).sort();
  }, [status]);

  return (
    <main>
      <header className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Google News Drive Sync</h1>
          <p className="text-slate-400">
            Live dashboard of the latest articles ready for Drive synchronisation.
          </p>
        </div>
        <div className="text-xs uppercase tracking-wide text-slate-400">
          Articles processed: {status?.metrics?.articles ?? 0}
        </div>
      </header>

      <SearchBar
        sources={sources}
        onFilterChange={setSourceFilter}
        onQueryChange={setQuery}
        selectedSource={sourceFilter}
      />

      <ArticleList articles={articles} loading={isLoading} />
    </main>
  );
}
