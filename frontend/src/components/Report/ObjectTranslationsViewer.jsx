import { useState } from 'react'
import { Eye, Code, Zap, CheckCircle2, AlertTriangle, XCircle, ChevronDown, ChevronUp, Copy, Check } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

export default function ObjectTranslationsViewer({ objectTranslations = [] }) {
  const [expandedIndex, setExpandedIndex] = useState(null)
  const [copiedIndex, setCopiedIndex] = useState(null)

  if (!objectTranslations || objectTranslations.length === 0) {
    return (
      <div className="glass-panel rounded-2xl p-6 border border-white/10 text-center text-gray-400 font-mono text-xs">
        No non-table database objects (views, procedures, triggers) were selected for this migration.
      </div>
    )
  }

  const handleCopy = (text, idx) => {
    navigator.clipboard.writeText(text)
    setCopiedIndex(idx)
    setTimeout(() => setCopiedIndex(null), 1200)
  }

  const getTypeIcon = (type) => {
    switch ((type || '').toLowerCase()) {
      case 'view': return <Eye className="w-4 h-4 text-sky-400" />
      case 'procedure':
      case 'function': return <Code className="w-4 h-4 text-purple-400" />
      case 'trigger': return <Zap className="w-4 h-4 text-amber-400" />
      default: return <Code className="w-4 h-4 text-gray-400" />
    }
  }

  const getStatusBadge = (item) => {
    const status = (item.status || item.compile_status || '').toLowerCase()
    const error = item.translation_error || item.error_detail

    if (status.includes('applied') || status.includes('compiled') || item.approved_by_user) {
      return (
        <span className="px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-caption font-mono font-bold flex items-center gap-1.5">
          <CheckCircle2 className="w-3.5 h-3.5" />
          APPLIED
        </span>
      )
    }
    if (status.includes('warning') || item.needs_human_review) {
      return (
        <span className="px-2.5 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-caption font-mono font-bold flex items-center gap-1.5">
          <AlertTriangle className="w-3.5 h-3.5" />
          NEEDS REVIEW
        </span>
      )
    }
    if (status.includes('fail') || error) {
      return (
        <span className="px-2.5 py-1 rounded-full bg-red-500/10 border border-red-500/30 text-red-400 text-caption font-mono font-bold flex items-center gap-1.5">
          <XCircle className="w-3.5 h-3.5" />
          FAILED
        </span>
      )
    }
    return (
      <span className="px-2.5 py-1 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400 text-caption font-mono font-bold flex items-center gap-1.5">
        TRANSLATED
      </span>
    )
  }

  return (
    <div className="glass-panel rounded-2xl p-6 border border-white/10 flex flex-col space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-h3 font-bold text-white font-sans">Database Objects Migration</h2>
          <p className="text-caption font-mono text-gray-400 mt-0.5">
            {objectTranslations.length} views, procedures, & triggers transpiled and executed
          </p>
        </div>
        <span className="text-xs font-mono text-purple-300 bg-purple-500/10 px-3 py-1 rounded-full border border-purple-500/30 font-bold">
          {objectTranslations.filter(o => o.status === 'applied' || o.approved_by_user || o.compile_status === 'Compiled successfully').length} / {objectTranslations.length} Ready
        </span>
      </div>

      <div className="divide-y divide-white/10 rounded-xl border border-white/10 overflow-hidden bg-black/40">
        {objectTranslations.map((item, idx) => {
          const isExpanded = expandedIndex === idx
          const ddl = item.translated_definition || item.source_definition || ''
          const error = item.translation_error || item.error_detail

          return (
            <div key={idx} className="flex flex-col transition-colors">
              <div 
                onClick={() => setExpandedIndex(isExpanded ? null : idx)}
                className="p-4 flex items-center justify-between cursor-pointer hover:bg-white/[0.03] transition-colors"
              >
                <div className="flex items-center space-x-3">
                  <div className="p-2 rounded-lg bg-white/5 border border-white/10">
                    {getTypeIcon(item.object_type)}
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-mono text-sm font-bold text-white">{item.name || item.object_name}</span>
                      <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-white/5 border border-white/10 text-gray-400">
                        {item.object_type}
                      </span>
                    </div>
                    {error && (
                      <p className="text-xs font-mono text-red-400 mt-0.5 truncate max-w-md">{error}</p>
                    )}
                  </div>
                </div>

                <div className="flex items-center space-x-4">
                  {getStatusBadge(item)}
                  <button className="text-gray-400 hover:text-white transition-colors">
                    {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              <AnimatePresence>
                {isExpanded && (
                  <motion.div 
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden border-t border-white/10 bg-black/60 p-4 space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono text-gray-400 uppercase tracking-wider">Target SQL / DDL Definition</span>
                      {ddl && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleCopy(ddl, idx)
                          }}
                          className="px-2.5 py-1 rounded bg-white/5 hover:bg-white/10 text-xs font-mono text-gray-300 border border-white/10 flex items-center space-x-1.5 transition-colors"
                        >
                          {copiedIndex === idx ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                          <span>{copiedIndex === idx ? 'Copied' : 'Copy DDL'}</span>
                        </button>
                      )}
                    </div>

                    {ddl ? (
                      <pre className="p-4 rounded-xl bg-[#09090d] border border-white/10 font-mono text-xs text-purple-200 overflow-x-auto whitespace-pre-wrap leading-relaxed">
                        {ddl}
                      </pre>
                    ) : (
                      <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-300 font-mono text-xs">
                        No DDL definition generated. Error: {error || 'Unknown error'}
                      </div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          )
        })}
      </div>
    </div>
  )
}
