import React from 'react';
import { api, ResearchItem } from '../api';
import { ItemCard } from './Dashboard';
import { Search as SearchIcon, Loader2 } from 'lucide-react';

export function Search() {
  const [query, setQuery] = React.useState('');
  const [mode, setMode] = React.useState<'text' | 'semantic'>('text');
  const [results, setResults] = React.useState<ResearchItem[]>([]);
  const [loading, setLoading] = React.useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    try {
      const res = await api.search(query, mode);
      setResults(res);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold text-slate-900 mb-8">Search Database</h1>

      <form onSubmit={handleSearch} className="mb-8 space-y-4">
        <div className="flex gap-4">
          <div className="flex-1 relative">
            <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search for papers, repos, or topics..."
              className="w-full pl-10 pr-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 shadow-sm"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="bg-blue-600 text-white px-6 py-3 rounded-xl font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            {loading ? <Loader2 className="animate-spin" /> : 'Search'}
          </button>
        </div>

        <div className="flex gap-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="mode"
              checked={mode === 'text'}
              onChange={() => setMode('text')}
              className="w-4 h-4 text-blue-600"
            />
            <span className="text-slate-700">Text Match</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="mode"
              checked={mode === 'semantic'}
              onChange={() => setMode('semantic')}
              className="w-4 h-4 text-blue-600"
            />
            <span className="text-slate-700">Semantic Search (Vector)</span>
          </label>
        </div>
      </form>

      <div className="space-y-4">
        {results.map((item) => (
          <ItemCard key={item.id} item={item} />
        ))}
        {results.length === 0 && !loading && query && (
          <div className="text-center text-slate-500 py-12">
            No results found. Try a different query or enable semantic search.
          </div>
        )}
      </div>
    </div>
  );
}
