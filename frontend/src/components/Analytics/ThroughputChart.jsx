import React, { useState } from 'react'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts'
import { motion } from 'framer-motion'
import { format } from 'date-fns'

export default function ThroughputChart({ data }) {
  const [timeRange, setTimeRange] = useState('1H')

  // Custom Tooltip for Glassmorphism Dark Theme
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-bg-panel/90 backdrop-blur-md border border-white/10 p-3 rounded-lg shadow-2xl">
          <p className="text-text-secondary text-xs font-mono mb-2">{format(new Date(label), 'HH:mm:ss')}</p>
          {payload.map((entry, index) => (
            <div key={index} className="flex items-center space-x-2 text-sm font-bold font-mono">
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
              <span className="text-text-primary">
                {entry.value} {entry.name === 'throughput' ? 'MB/s' : 'Rows/s'}
              </span>
            </div>
          ))}
        </div>
      )
    }
    return null
  }

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-6 bg-bg-raised backdrop-blur-xl border border-border-default rounded-2xl w-full h-[400px] flex flex-col shadow-sm"
    >
      <div className="flex items-center justify-between mb-6 shrink-0">
        <div>
          <h2 className="text-[12px] uppercase font-semibold tracking-[0.06em] font-sans text-text-primary">Live Execution Throughput</h2>
          <p className="font-sans text-caption text-text-secondary mt-1">Real-time data ingestion speed & row processing</p>
        </div>
        <div className="flex bg-bg-overlay border border-border-default rounded-lg p-1 font-mono text-caption">
          {['15M', '1H', '12H', '24H'].map(range => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`px-3 py-1 rounded transition-colors text-[13px] font-medium font-sans ${timeRange === range ? 'bg-accent text-white' : 'text-text-secondary hover:text-text-primary'}`}
            >
              {range}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 w-full min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorThroughput" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#7c3aed" stopOpacity={0.4}/>
                <stop offset="95%" stopColor="#7c3aed" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="colorRows" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4}/>
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
            <XAxis 
              dataKey="timestamp" 
              tickFormatter={(tick) => format(new Date(tick), 'HH:mm')} 
              stroke="rgba(255,255,255,0.2)"
              tick={{ fill: '#9ca3af', fontSize: 10, fontFamily: 'monospace' }}
              dy={10}
            />
            <YAxis 
              yAxisId="left"
              stroke="rgba(255,255,255,0.2)"
              tick={{ fill: '#9ca3af', fontSize: 10, fontFamily: 'monospace' }}
              dx={-10}
            />
            <YAxis 
              yAxisId="right"
              orientation="right"
              stroke="rgba(255,255,255,0.2)"
              tick={{ fill: '#9ca3af', fontSize: 10, fontFamily: 'monospace' }}
              dx={10}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ fontSize: '12px', fontFamily: 'monospace', paddingTop: '10px' }} />
            <Area 
              yAxisId="left"
              type="monotone" 
              dataKey="throughput" 
              name="throughput"
              stroke="#7c3aed" 
              strokeWidth={2}
              fillOpacity={1} 
              fill="url(#colorThroughput)" 
              activeDot={{ r: 6, fill: '#7c3aed', stroke: '#fff' }}
            />
            <Area 
              yAxisId="right"
              type="monotone" 
              dataKey="rows" 
              name="rows"
              stroke="#3b82f6" 
              strokeWidth={2}
              fillOpacity={1} 
              fill="url(#colorRows)" 
              activeDot={{ r: 6, fill: '#3b82f6', stroke: '#fff' }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  )
}
