import React from 'react'
import { motion } from 'framer-motion'
import { AlertTriangle, Terminal, Cpu, ArrowRight, Zap, CheckCircle2 } from 'lucide-react'
import { toast } from 'sonner'

export default function FailureRCACards({ data }) {
  const handleAutoFix = (id) => {
    toast.promise(
      new Promise(resolve => setTimeout(resolve, 2000)),
      {
        loading: 'AI Agent analyzing root cause and applying schema patch...',
        success: 'Patch applied successfully. Resuming migration.',
        error: 'Manual intervention required.'
      }
    )
  }

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="col-span-full xl:col-span-1 p-6 bg-bg-raised backdrop-blur-xl border border-border-default rounded-2xl w-full h-[400px] flex flex-col shadow-sm"
    >
      <div className="flex items-center space-x-3 mb-6 shrink-0">
        <div className="w-8 h-8 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-400">
          <AlertTriangle className="w-4 h-4" />
        </div>
        <div>
          <h2 className="text-[12px] uppercase font-semibold tracking-[0.06em] font-sans text-text-primary">Failure RCA & Auto-Fix</h2>
          <p className="font-sans text-caption text-text-secondary mt-1">AI-detected anomalies requiring attention</p>
        </div>
      </div>

      <div className="flex-1 w-full overflow-y-auto space-y-4 pr-2 custom-scrollbar">
        {data.map((issue, idx) => (
          <motion.div 
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: idx * 0.1 }}
            key={issue.id} 
            className="p-4 bg-bg-overlay border border-border-default rounded-xl hover:border-error/30 transition-all group"
          >
            <div className="flex justify-between items-start mb-3">
              <div className="flex items-center space-x-2">
                <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                <span className="font-sans text-body-sm font-bold text-text-primary">{issue.errorType}</span>
              </div>
              <span className="font-mono text-caption text-text-secondary bg-bg-sunken px-2 py-0.5 rounded">{issue.time}</span>
            </div>
            
            <p className="text-xs text-text-secondary mb-4 line-clamp-2">{issue.message}</p>
            
            <div className="flex flex-col space-y-3">
              {/* Context terminal block */}
              <div className="bg-bg-sunken p-2 rounded-lg border border-border-subtle flex items-start space-x-2">
                <Terminal className="w-3 h-3 text-text-tertiary mt-0.5 shrink-0" />
                <code className="text-[10px] font-mono text-error break-all">{issue.querySnippet}</code>
              </div>

              {/* Action row */}
              <div className="flex items-center justify-between pt-2">
                <div className="flex items-center space-x-1.5 text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded">
                  <Cpu className="w-3 h-3" />
                  <span>AI Patch Available</span>
                </div>
                <button 
                  onClick={() => handleAutoFix(issue.id)}
                  className="flex items-center space-x-1.5 text-[10px] font-mono text-white bg-accent/20 hover:bg-accent hover:text-white border border-accent/40 hover:shadow-[0_0_15px_rgba(124,58,237,0.5)] transition-all px-3 py-1 rounded"
                >
                  <Zap className="w-3 h-3" />
                  <span>Auto-Fix</span>
                </button>
              </div>
            </div>
          </motion.div>
        ))}
        {data.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-3 opacity-50">
            <CheckCircle2 className="w-8 h-8 text-emerald-400" />
            <p className="text-sm font-mono text-text-tertiary">Zero active critical anomalies.</p>
          </div>
        )}
      </div>
    </motion.div>
  )
}
