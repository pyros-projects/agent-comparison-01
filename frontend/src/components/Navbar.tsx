import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Search, Brain, Network, Power, PowerOff } from 'lucide-react';
import { api } from '../api';

export function Navbar() {
  const location = useLocation();
  const [status, setStatus] = React.useState<{ingesting: boolean}>({ingesting: false});

  React.useEffect(() => {
    api.getStatus().then(setStatus);
    const interval = setInterval(() => {
      api.getStatus().then(setStatus);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const toggleIngest = async () => {
    const newStatus = await api.controlIngest(!status.ingesting);
    setStatus(newStatus);
  };

  const navItems = [
    { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/search', icon: Search, label: 'Search' },
    { path: '/theory', icon: Brain, label: 'Theory' },
    { path: '/graph', icon: Network, label: 'Graph' },
  ];

  return (
    <nav className="bg-slate-900 text-white w-64 min-h-screen flex flex-col p-4">
      <div className="text-xl font-bold mb-8 px-4">Research Catalog</div>
      
      <div className="flex-1 space-y-2">
        {navItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
              location.pathname === item.path
                ? 'bg-blue-600 text-white'
                : 'hover:bg-slate-800 text-slate-400'
            }`}
          >
            <item.icon size={20} />
            <span>{item.label}</span>
          </Link>
        ))}
      </div>

      <div className="mt-auto border-t border-slate-800 pt-4">
        <div className="flex items-center justify-between px-4 py-2 bg-slate-800 rounded-lg">
          <div className="flex flex-col">
            <span className="text-xs text-slate-400">Ingestion Status</span>
            <span className={`text-sm font-medium ${status.ingesting ? 'text-green-400' : 'text-slate-400'}`}>
              {status.ingesting ? 'Running' : 'Stopped'}
            </span>
          </div>
          <button
            onClick={toggleIngest}
            className={`p-2 rounded-full transition-colors ${
              status.ingesting 
                ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30' 
                : 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
            }`}
            title={status.ingesting ? 'Stop Ingestion' : 'Start Ingestion'}
          >
            {status.ingesting ? <PowerOff size={18} /> : <Power size={18} />}
          </button>
        </div>
      </div>
    </nav>
  );
}
