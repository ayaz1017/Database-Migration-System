import React, { useState, useEffect, useMemo } from 'react'
import { motion } from 'framer-motion'
import { CheckCircle2, CircleDashed, Loader2, AlertCircle } from 'lucide-react'
import { useMigrationStore } from '../../store/useMigrationStore'

const DEFAULT_STAGES = [
  { id: 'connect', label: 'Connect Source', status: 'pending' },
  { id: 'discovery', label: 'Extract Schema', status: 'pending' },
  { id: 'schema', label: 'Transform DDL', status: 'pending' },
  { id: 'data', label: 'Migrate Data', status: 'pending' },
  { id: 'validation', label: 'Data Verification', status: 'pending' },
  { id: 'objects', label: 'Migrate Objects', status: 'pending' },
]

function PipelineVisualizer({ stages }) {
  const storeStages = useMigrationStore((state) => state.pipelineStages)
  const pipelineStages = stages || storeStages || DEFAULT_STAGES
  const [isTimedOut, setIsTimedOut] = useState(false)

  useEffect(() => {
    const hasActivity = pipelineStages.some(s => s.status !== 'pending')
    if (hasActivity) {
      setIsTimedOut(false)
      return
    }

    const timer = setTimeout(() => {
      setIsTimedOut(true)
    }, 30000)

    return () => clearTimeout(timer)
  }, [pipelineStages])

  return (
    <div className="flex flex-col w-full space-y-4">
      {isTimedOut && (
        <motion.div 
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full bg-red-500/10 border border-red-500/30 text-red-400 p-3 rounded-xl flex items-center justify-center font-mono text-xs"
        >
          <AlertCircle className="w-4 h-4 mr-2 shrink-0 text-red-400" />
          <span>No response from pipeline after 30 seconds — check backend logs or database connectivity.</span>
        </motion.div>
      )}
      <div className="p-6 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl w-full flex items-center justify-between overflow-x-auto custom-scrollbar">
        {pipelineStages.map((stage, idx) => {
          const isLast = idx === pipelineStages.length - 1
          const isRunning = stage.status === 'running' || stage.status === 'in_progress'
          const isCompleted = stage.status === 'completed' || stage.status === 'done'
          const isFailed = stage.status === 'failed'
          
          return (
            <React.Fragment key={stage.id}>
              <div className="flex flex-col items-center shrink-0 min-w-[120px] relative z-10">
                <div 
                  className={`w-12 h-12 rounded-full flex items-center justify-center border-2 mb-3 relative transition-all duration-300 ${
                    isCompleted ? 'border-emerald-500 bg-emerald-500/10 text-emerald-400' :
                    isRunning ? 'border-purple-500 bg-purple-500/10 text-purple-400 shadow-[0_0_20px_rgba(168,85,247,0.5)]' :
                    isFailed ? 'border-red-500 bg-red-500/10 text-red-400 shadow-[0_0_20px_rgba(239,68,68,0.5)]' :
                    'border-dashed border-gray-600/80 bg-white/[0.02] text-gray-500'
                  }`}
                >
                  {isCompleted && <CheckCircle2 className="w-6 h-6 text-emerald-400" />}
                  {isRunning && (
                    <>
                      <Loader2 className="w-6 h-6 animate-spin text-purple-400" />
                      <div className="absolute inset-0 rounded-full border-2 border-purple-500 animate-ping opacity-60 pointer-events-none" />
                    </>
                  )}
                  {isFailed && <AlertCircle className="w-6 h-6 text-red-400" />}
                  {!isCompleted && !isRunning && !isFailed && <CircleDashed className="w-6 h-6 text-gray-500" />}
                </div>
                <span className={`font-sans font-medium text-body-sm text-center ${
                  isCompleted ? 'text-emerald-400' : isRunning ? 'text-purple-300' : isFailed ? 'text-red-400' : 'text-gray-500'
                }`}>
                  {stage.label}
                </span>
                <span className={`text-caption font-mono mt-1 uppercase ${
                  isCompleted ? 'text-emerald-500/80' : isRunning ? 'text-purple-400 animate-pulse' : isFailed ? 'text-red-400' : 'text-gray-600'
                }`}>
                  {isRunning ? 'In Progress' : isCompleted ? 'Completed' : isFailed ? 'Failed' : 'Pending'}
                </span>
              </div>

              {!isLast && (
                <div className="flex-1 h-0.5 mx-4 flex items-center relative -translate-y-4">
                  <div className="absolute inset-0 bg-white/10" />
                  <div 
                    style={{ width: isCompleted ? '100%' : (isRunning || isFailed) ? '50%' : '0%' }}
                    className={`absolute left-0 h-full transition-all duration-500 ${isRunning ? 'bg-purple-500' : isFailed ? 'bg-red-500' : 'bg-emerald-500'}`}
                  />
                </div>
              )}
            </React.Fragment>
          )
        })}
      </div>
    </div>
  )
}

export default React.memo(PipelineVisualizer)
