import React from 'react';
import { AlertTriangle, RefreshCcw } from 'lucide-react';

export default function ErrorFallback({ error, resetErrorBoundary }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[50vh] p-6 text-center space-y-4">
      <div className="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center text-red-500 mb-2">
        <AlertTriangle className="w-8 h-8" />
      </div>
      <h2 className="font-sans text-h3 font-bold text-slate-100">Something went wrong</h2>
      <p className="font-mono text-caption text-slate-400 max-w-md bg-[#070709] p-4 rounded-lg border border-slate-800/50 text-left overflow-hidden text-ellipsis">
        {error.message}
      </p>
      <button
        onClick={resetErrorBoundary}
        className="mt-6 flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg transition-all font-medium text-sm shadow-lg shadow-indigo-500/20"
      >
        <RefreshCcw className="w-4 h-4" />
        Try Again
      </button>
    </div>
  );
}
