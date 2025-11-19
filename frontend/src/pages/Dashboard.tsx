import React from 'react';
import { api, ResearchItem } from '../api';
import { ExternalLink, Tag, BookOpen, GitBranch } from 'lucide-react';

export function Dashboard() {
  const [stats, setStats] = React.useState({
    total_items: 0,
    total_papers: 0,
    total_repos: 0,
    total_relationships: 0
  });
  const [recentItems, setRecentItems] = React.useState<ResearchItem[]>([]);

  React.useEffect(() => {
    const loadData = async () => {
      const [s, i] = await Promise.all([api.getStats(), api.getItems(0, 10)]);
      setStats(s);
      setRecentItems(i);
    };
    loadData();
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-8 space-y-8">
      <h1 className="text-3xl font-bold text-slate-900">Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatCard label="Total Items" value={stats.total_items} />
        <StatCard label="Papers" value={stats.total_papers} />
        <StatCard label="Repositories" value={stats.total_repos} />
        <StatCard label="Relationships" value={stats.total_relationships} />
      </div>

      <div>
        <h2 className="text-xl font-semibold mb-4 text-slate-800">Recent Ingestions</h2>
        <div className="grid gap-4">
          {recentItems.map((item) => (
            <ItemCard key={item.id} item={item} />
          ))}
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
      <p className="text-sm text-slate-500 font-medium">{label}</p>
      <p className="text-3xl font-bold text-slate-900 mt-2">{value}</p>
    </div>
  );
}

export function ItemCard({ item }: { item: ResearchItem }) {
  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3 mb-2">
          {item.type === 'paper' ? (
            <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs font-medium flex items-center gap-1">
              <BookOpen size={14} /> Paper
            </span>
          ) : (
            <span className="bg-purple-100 text-purple-700 px-2 py-1 rounded text-xs font-medium flex items-center gap-1">
              <GitBranch size={14} /> Repo
            </span>
          )}
          <span className="text-slate-400 text-xs">{new Date(item.ingested_date).toLocaleDateString()}</span>
        </div>
        <div className="flex gap-2">
          <ScoreBadge label="Relevancy" score={item.relevancy_score} />
          <ScoreBadge label="Interest" score={item.interesting_score} />
        </div>
      </div>

      <h3 className="text-lg font-semibold text-slate-900 mb-2">{item.title}</h3>
      <p className="text-slate-600 text-sm mb-4 line-clamp-2">{item.summary}</p>

      <div className="flex flex-wrap gap-2 mb-4">
        {item.tags.slice(0, 5).map((tag) => (
          <span key={tag} className="text-xs bg-slate-100 text-slate-600 px-2 py-1 rounded-full flex items-center gap-1">
            <Tag size={12} /> {tag}
          </span>
        ))}
      </div>

      <div className="flex justify-end">
        <a 
          href={item.url} 
          target="_blank" 
          rel="noopener noreferrer"
          className="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1 font-medium"
        >
          View Source <ExternalLink size={14} />
        </a>
      </div>
    </div>
  );
}

function ScoreBadge({ label, score }: { label: string; score: number }) {
  const color = score >= 8 ? 'text-green-600 bg-green-50' : score >= 5 ? 'text-yellow-600 bg-yellow-50' : 'text-slate-600 bg-slate-50';
  return (
    <div className={`flex flex-col items-end px-2 py-1 rounded ${color}`}>
      <span className="text-[10px] uppercase font-bold opacity-70">{label}</span>
      <span className="text-sm font-bold">{score}/10</span>
    </div>
  );
}
