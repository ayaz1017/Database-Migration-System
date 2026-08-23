import React from 'react'
import { motion } from 'framer-motion'
import { Key, Link as LinkIcon, Layers, Eye, CheckCircle2, AlertCircle } from 'lucide-react'

export default function ConstraintChecks({ data }) {
  const cards = [
    { 
      id: 'pk', 
      label: 'Primary Keys', 
      icon: Key, 
      color: 'text-purple-400', 
      bg: 'bg-purple-500/10', 
      border: 'border-purple-500/30', 
      gradient: 'from-purple-500 to-indigo-500',
      glow: 'hover:shadow-[0_0_25px_rgba(168,85,247,0.2)]',
      stat: data.pk 
    },
    { 
      id: 'fk', 
      label: 'Foreign Keys', 
      icon: LinkIcon, 
      color: 'text-blue-400', 
      bg: 'bg-blue-500/10', 
      border: 'border-blue-500/30', 
      gradient: 'from-blue-500 to-cyan-500',
      glow: 'hover:shadow-[0_0_25px_rgba(59,130,246,0.2)]',
      stat: data.fk 
    },
    { 
      id: 'idx', 
      label: 'Indexes', 
      icon: Layers, 
      color: 'text-emerald-400', 
      bg: 'bg-emerald-500/10', 
      border: 'border-emerald-500/30', 
      gradient: 'from-emerald-500 to-teal-400',
      glow: 'hover:shadow-[0_0_25px_rgba(16,185,129,0.2)]',
      stat: data.idx 
    },
    { 
      id: 'view', 
      label: 'Views & Objects', 
      icon: Eye, 
      color: 'text-amber-400', 
      bg: 'bg-amber-500/10', 
      border: 'border-amber-500/30', 
      gradient: 'from-amber-500 to-orange-400',
      glow: 'hover:shadow-[0_0_25px_rgba(245,158,11,0.2)]',
      stat: data.view 
    },
  ]

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, idx) => {
        const passPercent = card.stat.total > 0 ? (card.stat.passed / card.stat.total) * 100 : 100
        const isAllPassed = card.stat.failed === 0

        return (
          <motion.div 
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.08, duration: 0.3 }}
            key={card.id}
            className={`bg-[#0c0c14]/90 backdrop-blur-xl border border-white/10 rounded-2xl p-4 flex flex-col justify-between transition-all duration-300 glass-card ${card.glow}`}
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-3">
                <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${card.bg} ${card.border} border shrink-0`}>
                  <card.icon className={`w-4 h-4 ${card.color}`} />
                </div>
                <h4 className="font-sans font-semibold text-body-sm text-gray-200 uppercase tracking-wider">
                  {card.label}
                </h4>
              </div>

              {isAllPassed ? (
                <span className="flex items-center text-[10px] font-mono font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 rounded-full shrink-0">
                  <CheckCircle2 className="w-3 h-3 mr-1" />
                  100%
                </span>
              ) : (
                <span className="flex items-center text-[10px] font-mono font-bold text-red-400 bg-red-500/10 border border-red-500/30 px-2 py-0.5 rounded-full shrink-0">
                  <AlertCircle className="w-3 h-3 mr-1 animate-pulse" />
                  {card.stat.failed} Failed
                </span>
              )}
            </div>

            <div className="space-y-2 mt-1">
              <div className="flex justify-between items-baseline font-mono">
                <div>
                  <span className="font-mono text-h4 font-bold text-white tracking-tight">{card.stat.passed}</span>
                  <span className="text-gray-500 text-xs font-medium ml-1.5">/ {card.stat.total} verified</span>
                </div>
                <span className="text-xs font-semibold text-gray-400">{passPercent.toFixed(0)}%</span>
              </div>

              <div className="w-full h-1.5 bg-black/60 rounded-full overflow-hidden flex border border-white/5">
                <motion.div 
                  initial={{ width: 0 }}
                  animate={{ width: `${passPercent}%` }}
                  transition={{ duration: 0.6, ease: 'easeOut' }}
                  className={`h-full ${isAllPassed ? `bg-gradient-to-r ${card.gradient}` : 'bg-red-500'}`}
                />
              </div>
            </div>
          </motion.div>
        )
      })}
    </div>
  )
}
