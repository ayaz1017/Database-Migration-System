import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown, Activity } from 'lucide-react'
import { LineChart, Line, ResponsiveContainer, YAxis } from 'recharts'

const formatValue = (val, type) => {
  if (type === 'percentage') return `${val}%`
  if (type === 'data') return `${typeof val === 'number' ? val.toFixed(2) : val} TB`
  if (type === 'throughput') return `${val} MB/s`
  if (type === 'time') return `${val}m`
  if (val >= 1000000) return `${(val / 1000000).toFixed(1)}M`
  if (val >= 1000) return `${(val / 1000).toFixed(1)}K`
  return val
}

export default function KPICard({ title, value, type, trend, sparklineData, color = '#7c3aed' }) {
  const [displayValue, setDisplayValue] = useState(0)

  // Number animation
  useEffect(() => {
    let startTimestamp = null;
    const step = (timestamp) => {
      if (!startTimestamp) startTimestamp = timestamp;
      const progress = Math.min((timestamp - startTimestamp) / 1000, 1);
      setDisplayValue(Math.floor(progress * value));
      if (progress < 1) {
        window.requestAnimationFrame(step);
      } else {
        setDisplayValue(value)
      }
    };
    window.requestAnimationFrame(step);
  }, [value]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-5 bg-bg-raised backdrop-blur-xl border border-border-default rounded-2xl relative overflow-hidden group hover:border-border-strong transition-all duration-300 shadow-sm"
    >
      {/* Background glow on hover */}
      <div 
        className="absolute inset-0 opacity-0 group-hover:opacity-[0.03] transition-opacity duration-500 blur-2xl pointer-events-none"
        style={{ backgroundColor: color }}
      />
      
      <div className="flex justify-between items-start mb-4 relative z-10">
        <h3 className="text-[11px] uppercase tracking-[0.06em] font-sans text-text-tertiary font-semibold">{title}</h3>
        {trend > 0 ? (
          <div className="flex items-center space-x-1 text-success bg-success-muted px-2 py-0.5 rounded text-[10px] font-bold font-mono">
            <TrendingUp className="w-3 h-3" />
            <span>{trend}%</span>
          </div>
        ) : trend < 0 ? (
          <div className="flex items-center space-x-1 text-error bg-error-muted px-2 py-0.5 rounded text-[10px] font-bold font-mono">
            <TrendingDown className="w-3 h-3" />
            <span>{Math.abs(trend)}%</span>
          </div>
        ) : null}
      </div>

      <div className="flex items-end justify-between relative z-10 gap-2">
        <div className="text-2xl sm:text-3xl font-bold font-sans text-text-primary tracking-tight truncate">
          {formatValue(displayValue, type)}
        </div>
        
        {/* Mini Sparkline */}
        <div className="w-24 h-10 opacity-70 group-hover:opacity-100 transition-opacity">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={sparklineData}>
              <YAxis domain={['dataMin', 'dataMax']} hide />
              <Line 
                type="monotone" 
                dataKey="val" 
                stroke={color} 
                strokeWidth={2} 
                dot={false}
                isAnimationActive={true}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
      
      {/* Live Activity indicator */}
      <div className="absolute top-5 right-5 w-2 h-2 rounded-full bg-emerald-400 animate-ping opacity-75" />
    </motion.div>
  )
}
