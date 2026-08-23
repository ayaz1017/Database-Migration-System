import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Database, Zap, Clock, DollarSign } from 'lucide-react'

export default function VolumeCalculator() {
  const [rows, setRows] = useState(10) // in millions

  // Simple pricing logic
  const cost = 0 // $0 (Free)
  const timeHours = (rows / 50).toFixed(1) // 50M rows per hour approx
  const dataTB = (rows * 0.005).toFixed(2) // 5GB per million rows approx

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-black/40 backdrop-blur-xl border border-white/10 rounded-3xl p-8 lg:p-12 max-w-4xl mx-auto mt-16"
    >
      <div className="text-center mb-10">
        <h2 className="font-sans text-h3 font-bold text-stark-white tracking-tight">Calculate Your Migration Cost</h2>
        <p className="font-sans text-body text-gray-400 mt-3">Interactive slider based on source data volume</p>
      </div>

      <div className="mb-12 relative">
        {/* Slider Track background */}
        <div className="absolute top-1/2 left-0 right-0 h-2 bg-white/5 rounded-full -translate-y-1/2" />
        
        {/* Slider Active Track */}
        <div 
          className="absolute top-1/2 left-0 h-2 bg-gradient-to-r from-accent to-blue-500 rounded-full -translate-y-1/2 shadow-[0_0_20px_rgba(124,58,237,0.5)]" 
          style={{ width: `${(rows / 500) * 100}%` }}
        />

        <input 
          type="range" 
          min="1" 
          max="500" 
          value={rows}
          onChange={(e) => setRows(Number(e.target.value))}
          className="w-full relative z-10 opacity-0 cursor-pointer h-8"
        />

        <div 
          className="absolute top-1/2 w-6 h-6 bg-white rounded-full border-4 border-accent -translate-y-1/2 -ml-3 pointer-events-none shadow-xl transition-all"
          style={{ left: `${(rows / 500) * 100}%` }}
        />

        <div className="flex justify-between mt-6 font-sans text-caption text-gray-500 uppercase tracking-wider">
          <span>1M Rows</span>
          <span>500M Rows</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white/[0.02] border border-white/5 rounded-2xl p-6 flex flex-col items-center justify-center text-center">
          <Database className="w-6 h-6 text-blue-400 mb-3" />
          <div className="font-sans text-h3 font-bold text-white mb-1">{rows}M</div>
          <div className="font-sans text-caption text-gray-500 uppercase tracking-wider">Total Rows (Est. {dataTB} TB)</div>
        </div>
        
        <div className="bg-white/[0.02] border border-white/5 rounded-2xl p-6 flex flex-col items-center justify-center text-center relative overflow-hidden group">
          <div className="absolute inset-0 bg-accent/5 opacity-0 group-hover:opacity-100 transition-opacity" />
          <DollarSign className="w-6 h-6 text-emerald-400 mb-3 relative z-10" />
          <div className="font-sans text-h3 font-bold text-emerald-400 mb-1 relative z-10">${cost}</div>
          <div className="font-sans text-caption text-gray-500 uppercase tracking-wider relative z-10">Estimated Cost</div>
        </div>

        <div className="bg-white/[0.02] border border-white/5 rounded-2xl p-6 flex flex-col items-center justify-center text-center">
          <Clock className="w-6 h-6 text-accent mb-3" />
          <div className="font-sans text-h3 font-bold text-white mb-1">{timeHours}h</div>
          <div className="font-sans text-caption text-gray-500 uppercase tracking-wider">Est. Migration Time</div>
        </div>
      </div>
    </motion.div>
  )
}
