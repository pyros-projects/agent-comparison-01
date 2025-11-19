import React from 'react';
import { api, ResearchItem } from '../api';
import { ItemCard } from './Dashboard';
import { Sparkles, Loader2 } from 'lucide-react';

export function Theory() {
  const [theory, setTheory] = React.useState('');
  const [answer, setAnswer] = React.useState<string | null>(null);
  const [relatedItems, setRelatedItems] = React.useState<ResearchItem[]>([]);
  const [loading, setLoading] = React.useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!theory.trim()) return;

    setLoading(true);
    setAnswer(null);
    try {
      const res = await api.analyzeTheory(theory);
      setAnswer(res.answer);
      setRelatedItems(res.related_items);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold text-slate-900 mb-8">Theory Analysis</h1>
      <p className="text-slate-600 mb-6">
        Enter a hypothesis or question. The system will find relevant research and synthesize an answer based on the database.
      </p>

      <form onSubmit={handleSubmit} className="mb-8">
        <div className="relative">
          <textarea
            value={theory}
            onChange={(e) => setTheory(e.target.value)}
            placeholder="e.g., 'Do transformers perform better than RNNs on small datasets?'"
            className="w-full p-4 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 shadow-sm min-h-[120px]"
          />
          <button
            type="submit"
            disabled={loading}
            className="absolute bottom-4 right-4 bg-purple-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-purple-700 transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            {loading ? <Loader2 className="animate-spin" size={18} /> : <><Sparkles size={18} /> Analyze</>}
          </button>
        </div>
      </form>

      {answer && (
        <div className="bg-white p-8 rounded-xl shadow-lg border border-purple-100 mb-8">
          <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2">
            <Sparkles className="text-purple-600" /> Analysis Result
          </h2>
          <div className="prose prose-slate max-w-none">
            <p className="whitespace-pre-wrap">{answer}</p>
          </div>
        </div>
      )}

      {relatedItems.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Supporting Evidence</h3>
          <div className="space-y-4">
            {relatedItems.map((item) => (
              <ItemCard key={item.id} item={item} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
