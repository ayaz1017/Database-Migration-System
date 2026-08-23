import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { X, CheckCircle2, Database, Key, Link as LinkIcon, Code2, ArrowRight, Layers } from 'lucide-react'

export default function SchemaSidebar({ activeNode, edges = [], onClose }) {
  const [ddlTab, setDdlTab] = useState('target') // 'target' or 'original'

  if (!activeNode) return null

  const { tableName, dialect, columns = [], ddlOriginal, ddlTarget } = activeNode.data || {}

  // Calculate dependencies from edges
  const upstream = edges
    .filter(e => e.target === activeNode.id)
    .map(e => e.source)
  const downstream = edges
    .filter(e => e.source === activeNode.id)
    .map(e => e.target)

  return (
    <motion.aside
      initial={{ x: '100%' }}
      animate={{ x: 0 }}
      exit={{ x: '100%' }}
      transition={{ type: 'spring', damping: 25, stiffness: 250 }}
      className="fixed top-14 right-0 bottom-0 w-96 bg-bg-panel/95 backdrop-blur-xl border-l border-white/10 shadow-2xl z-40 flex flex-col overflow-hidden"
    >
      {/* Header */}
      <div className="p-5 border-b border-white/10 flex items-center justify-between bg-black/40">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-accent/15 border border-accent/30 flex items-center justify-center">
            <Database className="w-5 h-5 text-accent" />
          </div>
          <div>
            <h2 className="font-mono text-body font-semibold text-stark-white tracking-wide">{tableName}</h2>
            <span className="font-mono text-caption uppercase tracking-wider text-gray-400">{dialect || 'Database Table'}</span>
          </div>
        </div>
        
        <button 
          onClick={onClose}
          className="p-1.5 text-gray-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto p-5 space-y-6">
        
        {/* Migration Status */}
        <div className="space-y-2">
          <span className="font-sans text-caption text-gray-400 uppercase tracking-wider block font-medium">Migration Status</span>
          <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 font-sans text-caption font-bold">
            <CheckCircle2 className="w-4 h-4" />
            <span>Ready for Migration</span>
          </div>
        </div>

        {/* Dependencies */}
        <div className="space-y-3">
          <span className="font-sans text-caption text-gray-400 uppercase tracking-wider block font-medium">Dependencies</span>
          
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 bg-black/30 border border-white/10 rounded-xl space-y-1.5">
              <span className="font-sans text-caption text-gray-400 uppercase tracking-wider block">Upstream (FK To)</span>
              {upstream.length === 0 ? (
                <span className="font-sans text-caption text-gray-500 italic">None</span>
              ) : (
                upstream.map(tbl => (
                  <div key={tbl} className="font-mono text-caption font-bold text-accent-solid flex items-center gap-1">
                    <Layers className="w-3 h-3" /> {tbl}
                  </div>
                ))
              )}
            </div>

            <div className="p-3 bg-black/30 border border-white/10 rounded-xl space-y-1.5">
              <span className="font-sans text-caption text-gray-400 uppercase tracking-wider block">Downstream (FK From)</span>
              {downstream.length === 0 ? (
                <span className="font-sans text-caption text-gray-500 italic">None</span>
              ) : (
                downstream.map(tbl => (
                  <div key={tbl} className="font-mono text-caption font-bold text-accent-solid flex items-center gap-1">
                    <ArrowRight className="w-3 h-3" /> {tbl}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Schema Columns Table */}
        <div className="space-y-3">
          <span className="font-sans text-caption text-gray-400 uppercase tracking-wider block font-medium">
            Columns ({columns.length})
          </span>
          <div className="bg-black/40 border border-white/10 rounded-xl overflow-hidden divide-y divide-white/5">
            {columns.map((col, i) => (
              <div key={i} className="p-2.5 flex items-center justify-between font-mono text-body-sm">
                <div className="flex items-center gap-2">
                  {col.isPrimary ? (
                    <Key className="w-3.5 h-3.5 text-amber-400 shrink-0" title="Primary Key" />
                  ) : col.isForeign ? (
                    <LinkIcon className="w-3.5 h-3.5 text-accent-solid shrink-0" title="Foreign Key" />
                  ) : (
                    <span className="w-3.5 h-3.5" />
                  )}
                  <span className={col.isPrimary ? 'text-stark-white font-bold' : 'text-white/90'}>
                    {col.name}
                  </span>
                </div>
                <span className="text-gray-400 font-mono text-caption">{col.type}</span>
              </div>
            ))}
          </div>
        </div>

        {/* DDL Snippet Viewer */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="font-sans text-caption text-gray-400 uppercase tracking-wider block font-medium flex items-center gap-1.5">
              <Code2 className="w-4 h-4 text-accent" /> Compiled DDL
            </span>
            <div className="flex bg-black/40 border border-white/10 rounded-lg p-0.5 font-sans text-caption font-semibold">
              <button
                onClick={() => setDdlTab('target')}
                className={`px-2 py-0.5 rounded font-bold transition-colors ${ddlTab === 'target' ? 'bg-accent text-white' : 'text-gray-400 hover:text-white'}`}
              >
                Target DDL
              </button>
              <button
                onClick={() => setDdlTab('original')}
                className={`px-2 py-0.5 rounded font-bold transition-colors ${ddlTab === 'original' ? 'bg-accent text-white' : 'text-gray-400 hover:text-white'}`}
              >
                Original DDL
              </button>
            </div>
          </div>

          <div className="p-3 bg-black/60 border border-white/10 rounded-xl overflow-x-auto">
            <pre className="text-xs font-mono text-gray-300 whitespace-pre leading-relaxed">
              {ddlTab === 'target' ? ddlTarget : ddlOriginal}
            </pre>
          </div>
        </div>

      </div>
    </motion.aside>
  )
}
