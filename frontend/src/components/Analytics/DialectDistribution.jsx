import React from 'react'
import { motion } from 'framer-motion'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis } from 'recharts'
import { Database } from 'lucide-react'

const PIE_COLORS = ['#7c3aed', '#3b82f6', '#f59e0b', '#14b8a6', '#ec4899', '#f97316']

export default function DialectDistribution({ data }) {
  
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-bg-panel/90 backdrop-blur-md border border-white/10 p-3 rounded-lg shadow-2xl space-y-1 text-sm font-mono">
          <div className="text-text-primary font-bold">{payload[0].payload.name}</div>
          <div className="text-text-secondary">Migrations: <span className="text-text-primary">{payload[0].value}</span></div>
          {payload[0].payload.failureRate !== undefined && (
             <div className="text-red-400">Fail Rate: {payload[0].payload.failureRate}%</div>
          )}
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
      <div className="flex items-center space-x-3 mb-6 shrink-0">
        <div className="w-8 h-8 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
          <Database className="w-4 h-4" />
        </div>
        <div>
          <h2 className="text-[12px] uppercase font-semibold tracking-[0.06em] font-sans text-text-primary">Dialect Pipeline Distribution</h2>
          <p className="font-sans text-caption text-text-secondary mt-1">Source to Target engine mappings</p>
        </div>
      </div>

      <div className="flex-1 w-full min-h-0 flex flex-col md:flex-row gap-6 items-center">
        {/* Donut Chart */}
        <div className="flex-1 w-full h-full relative">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                innerRadius="60%"
                outerRadius="90%"
                paddingAngle={5}
                dataKey="value"
                stroke="none"
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none flex-col">
            <span className="font-sans text-h3 font-bold text-text-primary tracking-tighter">
              {data.reduce((a, b) => a + b.value, 0)}
            </span>
            <span className="font-sans text-caption text-text-secondary tracking-widest mt-1">Total Pipes</span>
          </div>
        </div>

        {/* Legend / Bar Info */}
        <div className="flex-1 w-full space-y-2.5 overflow-y-auto pr-1">
          {data.map((item, index) => (
            <div key={item.name} className="p-2.5 bg-bg-overlay border border-border-default rounded-xl hover:border-border-strong transition-colors flex items-center justify-between gap-2">
              <div className="flex items-center space-x-2 min-w-0">
                <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: PIE_COLORS[index % PIE_COLORS.length] }} />
                <span className="font-sans text-xs font-semibold text-text-primary truncate" title={item.name}>
                  {item.name.replace(' -> ', ' \u2192 ')}
                </span>
              </div>
              <div className="text-right shrink-0">
                <div className="font-mono text-xs font-bold text-text-primary">{item.value}</div>
                <div className="font-sans text-[10px] text-text-secondary whitespace-nowrap">{item.failureRate}% Fail Rate</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  )
}
