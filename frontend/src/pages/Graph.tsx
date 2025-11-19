import React from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { api, GraphData } from '../api';

export function Graph() {
  const [data, setData] = React.useState<GraphData>({ nodes: [], links: [] });
  const containerRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    api.getGraph().then(setData);
  }, []);

  return (
    <div className="h-screen flex flex-col">
      <div className="p-4 bg-white border-b border-slate-200 flex justify-between items-center">
        <h1 className="text-xl font-bold text-slate-900">Knowledge Graph</h1>
        <div className="flex gap-4 text-sm text-slate-500">
          <span className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-blue-500"></span> Paper
          </span>
          <span className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-purple-500"></span> Repository
          </span>
        </div>
      </div>
      
      <div className="flex-1 bg-slate-50 relative" ref={containerRef}>
        <ForceGraph2D
          width={containerRef.current?.clientWidth}
          height={containerRef.current?.clientHeight}
          graphData={data}
          nodeLabel="title"
          nodeColor={(node: any) => node.type === 'paper' ? '#3b82f6' : '#a855f7'}
          nodeRelSize={6}
          linkColor={() => '#cbd5e1'}
          linkWidth={1}
          onNodeClick={(node: any) => {
            // In a real app, show modal details or navigate
            console.log('Clicked', node);
          }}
        />
        {data.nodes.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center text-slate-400">
            No data to visualize yet. Start ingestion.
          </div>
        )}
      </div>
    </div>
  );
}
