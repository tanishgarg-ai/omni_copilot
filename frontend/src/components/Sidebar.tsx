import React, { useState } from 'react';
import { Database, FolderPlus, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { api } from '../api';

export const Sidebar: React.FC = () => {
  const [path, setPath] = useState('');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<{ type: 'success' | 'error', message: string } | null>(null);

  const handleIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!path.trim()) return;

    setLoading(true);
    setStatus(null);
    try {
      const res = await api.ingest(path);
      setStatus({ type: 'success', message: res.status });
    } catch (err: any) {
      setStatus({ 
        type: 'error', 
        message: err.response?.data?.detail || err.message || 'Ingestion failed' 
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-80 bg-surface border-r border-border h-full flex flex-col pt-6 pb-6 px-4 shrink-0">
      <div className="flex items-center gap-3 px-2 mb-8">
        <div className="p-2 bg-primary/10 text-primary rounded-xl">
          <Database size={24} />
        </div>
        <h1 className="text-xl font-bold tracking-tight text-white">RAG Brain</h1>
      </div>

      <div className="flex-1">
        <h2 className="text-xs font-semibold text-textMuted uppercase tracking-wider mb-4 px-2">
          Knowledge Base
        </h2>
        
        <form onSubmit={handleIngest} className="space-y-4 px-2">
          <div>
            <label className="block text-sm font-medium text-textMuted mb-2">
              Directory Path
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-textMuted">
                <FolderPlus size={16} />
              </div>
              <input
                type="text"
                value={path}
                onChange={(e) => setPath(e.target.value)}
                placeholder="./docs"
                className="block w-full pl-10 pr-3 py-2 border border-border rounded-xl leading-5 bg-background text-textMain placeholder-textMuted focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary sm:text-sm transition-shadow"
                disabled={loading}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || !path.trim()}
            className="w-full flex justify-center items-center py-2 px-4 border border-transparent rounded-xl shadow-sm text-sm font-medium text-white bg-primary hover:bg-primaryHover focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary focus:ring-offset-surface disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? (
              <Loader2 size={18} className="animate-spin" />
            ) : (
              'Sync Directory'
            )}
          </button>
        </form>

        {status && (
          <div className={`mt-6 p-4 rounded-xl border flex gap-3 text-sm animate-in fade-in slide-in-from-top-2 ${
            status.type === 'success' 
            ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' 
            : 'bg-red-500/10 border-red-500/20 text-red-400'
          }`}>
            {status.type === 'success' ? <CheckCircle2 size={18} className="shrink-0 mt-0.5" /> : <AlertCircle size={18} className="shrink-0 mt-0.5"/>}
            <div className="break-words w-full">{status.message}</div>
          </div>
        )}
      </div>
    </div>
  );
};
