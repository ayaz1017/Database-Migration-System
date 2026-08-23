import { useEffect, useState, useMemo, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { ArrowLeft, CheckCircle2, ShieldAlert, XCircle, Copy, Check, Clock } from 'lucide-react'
import StreamingTerminal from '../components/Progress/StreamingTerminal'
import PipelineVisualizer from '../components/Progress/PipelineVisualizer'
import TableProgressGrid from '../components/Progress/TableProgressGrid'
import ResourceMonitor from '../components/Progress/ResourceMonitor'
import useMigrationSocket from '../hooks/useMigrationSocket'
import { useMigrationStore } from '../store/useMigrationStore'

const formatNumber = (num) => new Intl.NumberFormat('en-US').format(Math.floor(num || 0))

export default function MigrationProgress() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [copied, setCopied] = useState(false)

  const jobIdDisplay = id || 'mig_1785226553330'

  // Initialize WebSocket streaming connection (streams directly to Zustand)
  useMigrationSocket(id)

  // Subscribe only to the granular header & progress bar state slices
  const migrationStatus = useMigrationStore((state) => state.migrationStatus)
  const overallProgress = useMigrationStore((state) => state.overallProgress)
  const totalRows = useMigrationStore((state) => state.totalRows)
  const completedRows = useMigrationStore((state) => state.completedRows)
  const rowsPerSec = useMigrationStore((state) => state.rowsPerSec)

  const isRunning = migrationStatus === 'running' || migrationStatus === 'connecting'
  const isCompleted = migrationStatus === 'completed'
  const isFailed = migrationStatus === 'failed'

  // Keydown listener for Esc key navigation
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        navigate('/app')
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [navigate])

  // Copy Job ID to clipboard
  const handleCopyJobId = useCallback(() => {
    navigator.clipboard.writeText(jobIdDisplay)
    setCopied(true)
    setTimeout(() => setCopied(false), 1200)
  }, [jobIdDisplay])

  // Memoized ETA Calculation
  const etaText = useMemo(() => {
    if (completedRows >= totalRows && totalRows > 0) return '0 sec'
    if (rowsPerSec <= 0 || totalRows === 0) return '--'
    const remainingRows = totalRows - completedRows
    if (remainingRows <= 0) return '0 sec'
    const sec = Math.ceil(remainingRows / rowsPerSec)
    if (sec < 60) return `~${sec} sec remaining`
    const mins = Math.floor(sec / 60)
    const remSec = sec % 60
    return `~${mins} min ${remSec} sec remaining`
  }, [completedRows, totalRows, rowsPerSec])

  const formattedCompletedRows = useMemo(() => formatNumber(completedRows), [completedRows])
  const formattedTotalRows = useMemo(() => formatNumber(totalRows), [totalRows])
  const formattedRowsPerSec = useMemo(() => formatNumber(rowsPerSec), [rowsPerSec])

  return (
    <div className="p-8 max-w-[1600px] mx-auto w-full flex flex-col gap-6 min-h-full relative">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 shrink-0">
        <div className="flex items-center space-x-4">
          <button 
            onClick={() => navigate('/app')}
            className="w-10 h-10 flex items-center justify-center rounded-xl bg-white/5 hover:bg-white/10 text-white transition-colors border border-white/10 cursor-pointer"
            title="Back to Dashboard (Esc)"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center space-x-3">
              <h1 className="font-sans text-h1 font-bold text-stark-white tracking-tight">
                {isCompleted ? 'Migration Complete' : isFailed ? 'Migration Failed' : 'Active Migration'}
              </h1>
              {isRunning && (
                <motion.span 
                  animate={{ opacity: [0.7, 1, 0.7] }}
                  transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                  className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-mono text-caption flex items-center shadow-[0_0_12px_rgba(16,185,129,0.2)]"
                >
                  <span className="relative flex h-2 w-2 mr-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-400"></span>
                  </span>
                  RUNNING
                </motion.span>
              )}
              {isCompleted && (
                <span className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-mono text-caption flex items-center">
                  <CheckCircle2 className="w-3.5 h-3.5 mr-1.5" />
                  COMPLETED
                </span>
              )}
              {isFailed && (
                <span className="px-3 py-1 rounded-full bg-red-500/10 border border-red-500/30 text-red-400 font-mono text-caption flex items-center">
                  <XCircle className="w-3.5 h-3.5 mr-1.5" />
                  FAILED
                </span>
              )}
            </div>
            <div className="flex items-center space-x-2 font-mono mt-1 text-sm text-gray-400">
              <span>Job ID:</span>
              <span className="text-gray-200 font-semibold">{jobIdDisplay}</span>
              <button 
                onClick={handleCopyJobId}
                className="p-1 hover:bg-white/10 rounded transition-colors text-gray-400 hover:text-white relative cursor-pointer"
                title="Copy Job ID"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <AnimatePresence>
                  {copied && (
                    <motion.span 
                      initial={{ opacity: 0, y: 5 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -5 }}
                      className="absolute -top-7 left-1/2 -translate-x-1/2 bg-emerald-500 text-black text-[10px] font-bold px-2 py-0.5 rounded shadow"
                    >
                      Copied!
                    </motion.span>
                  )}
                </AnimatePresence>
              </button>
            </div>
          </div>
        </div>
        
        <div className="flex flex-col items-end">
          <div className="flex space-x-3">
            {isCompleted ? (
              <motion.button 
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                onClick={() => navigate(`/app/report/${jobIdDisplay}`)}
                className="bg-emerald-500 hover:bg-emerald-400 text-white px-6 py-2.5 rounded-xl font-mono font-bold transition-colors flex items-center shadow-[0_0_20px_rgba(16,185,129,0.4)] cursor-pointer"
              >
                <CheckCircle2 className="w-5 h-5 mr-2" />
                View Validation Report
              </motion.button>
            ) : isFailed ? (
              <button 
                onClick={() => navigate('/app')}
                className="bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 px-6 py-2.5 rounded-xl font-mono font-bold transition-colors flex items-center cursor-pointer"
              >
                <XCircle className="w-4 h-4 mr-2" />
                Back to Dashboard
              </button>
            ) : (
              <button 
                onClick={() => navigate('/app')}
                className="bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 px-6 py-2.5 rounded-xl font-mono font-bold transition-colors flex items-center cursor-pointer"
              >
                <ShieldAlert className="w-4 h-4 mr-2" />
                Abort Job
              </button>
            )}
          </div>
          <span className="text-[11px] font-mono text-gray-500 mt-1.5">Press Esc to go back</span>
        </div>
      </div>

      {/* Global Progress Bar */}
      <div className="glass-panel border border-white/10 rounded-2xl p-6 shrink-0">
        <div className="flex justify-between items-center mb-4">
          <span className="font-sans font-semibold text-body-sm text-gray-400 uppercase tracking-wider">Overall Progress</span>
          <div className="flex items-center space-x-4">
            <span className="text-xs font-mono text-gray-300 font-medium">
              {formattedCompletedRows} / {formattedTotalRows} rows • <span className="text-purple-300 font-semibold">{formattedRowsPerSec} rows/sec</span>
            </span>
            <div className="flex items-center space-x-1.5 bg-white/[0.04] px-2.5 py-0.5 rounded-md border border-white/5">
              <Clock className="w-3 h-3 text-purple-400" />
              <span className="text-xs font-mono text-gray-400">ETA: <span className="text-gray-200 font-semibold">{etaText}</span></span>
            </div>
            <span className="text-sm font-mono font-bold text-white bg-accent/20 px-2 py-0.5 rounded border border-accent/30">{overallProgress}%</span>
          </div>
        </div>
        <div className="w-full h-3 bg-black/60 rounded-full overflow-hidden flex relative p-0.5 border border-white/5">
          <div 
            style={{ 
              width: `${overallProgress}%`,
              transition: 'width 0.5s ease-out'
            }}
            className={`h-full rounded-full relative overflow-hidden ${
              isFailed ? 'bg-red-500' : isCompleted ? 'bg-emerald-500' : 'bg-gradient-to-r from-purple-600 via-purple-500 to-indigo-500'
            }`}
          >
            {isRunning && overallProgress < 1 && (
              <div 
                className="absolute inset-0 w-full h-full"
                style={{
                  background: 'linear-gradient(90deg, #7c3aed 0%, #a78bfa 50%, #7c3aed 100%)',
                  backgroundSize: '200% 100%',
                  animation: 'shimmer 1.5s infinite linear'
                }}
              />
            )}
          </div>
        </div>
      </div>

      {/* Pipeline Stage Visualizer */}
      <div className="shrink-0">
        <PipelineVisualizer />
      </div>

      {/* Grid Content */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Terminal logs (Span 2 columns) */}
        <div className="xl:col-span-2 flex flex-col">
          <StreamingTerminal />
        </div>

        {/* Resources & Tables (Span 1 column) */}
        <div className="xl:col-span-1 flex flex-col space-y-6">
          <ResourceMonitor />
          <TableProgressGrid />
        </div>
      </div>
      
      {/* Bottom padding for scroll */}
      <div className="h-10 shrink-0" />
    </div>
  )
}
