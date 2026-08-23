import React, { useState, useEffect, useMemo } from 'react'
import { LineChart, Line, ResponsiveContainer, YAxis, Tooltip, CartesianGrid, ReferenceLine } from 'recharts'
import { Activity, Cpu, HardDrive, Wifi, Zap } from 'lucide-react'
import { useMigrationStore } from '../../store/useMigrationStore'

const formatNumber = (num) => new Intl.NumberFormat('en-US').format(Math.floor(num || 0))

const CustomTooltip = React.memo(function CustomTooltip({ active, payload }) {
  if (active && payload && payload.length) {
    return (
      <div className="bg-[#12121a]/95 backdrop-blur-md border border-white/10 p-2.5 rounded-xl shadow-2xl text-xs font-mono space-y-1">
        <div className="text-purple-300 flex items-center justify-between space-x-3">
          <span>CPU:</span>
          <span className="font-bold">{payload[0].value.toFixed(1)}%</span>
        </div>
        <div className="text-blue-300 flex items-center justify-between space-x-3">
          <span>Memory:</span>
          <span className="font-bold">{payload[1].value.toFixed(1)}%</span>
        </div>
      </div>
    )
  }
  return null
})

function ResourceMonitor({ rowsPerSec }) {
  const storeRowsPerSec = useMigrationStore((state) => state.rowsPerSec)
  const liveRowsPerSec = rowsPerSec !== undefined ? rowsPerSec : storeRowsPerSec

  const [data, setData] = useState(() =>
    Array.from({ length: 25 }, (_, i) => ({
      time: i,
      cpu: 92 + Math.random() * 8,
      ram: 60 + Math.random() * 10,
      net: 400 + Math.random() * 67,
    }))
  )

  useEffect(() => {
    const interval = setInterval(() => {
      setData((prev) => {
        const last = prev[prev.length - 1]
        const newCpu = Math.min(100, Math.max(40, last.cpu + (Math.random() * 14 - 7)))
        const newRam = Math.min(100, Math.max(0, last.ram + (Math.random() * 4 - 2)))
        const newNet = Math.max(0, last.net + (Math.random() * 40 - 20))

        // Maintain fixed window size of 25 points
        const next = prev.length >= 25 ? prev.slice(1) : [...prev]
        next.push({
          time: last.time + 1,
          cpu: newCpu,
          ram: newRam,
          net: newNet,
        })
        return next
      })
    }, 1000)

    return () => clearInterval(interval)
  }, [])

  const current = data[data.length - 1] || { cpu: 0, ram: 0, net: 0, time: 0 }

  const getCpuColorClasses = (cpuVal) => {
    if (cpuVal > 90) return 'text-[#ff7f50] bg-[#ff7f50]/10 border-[#ff7f50]/30 shadow-[0_0_12px_rgba(255,127,80,0.2)]'
    if (cpuVal >= 70) return 'text-amber-400 bg-amber-500/10 border-amber-500/30'
    return 'text-blue-400 bg-blue-500/10 border-blue-500/20'
  }

  const strokeColor = useMemo(() => {
    return current.cpu > 90 ? '#ff7f50' : current.cpu >= 70 ? '#f59e0b' : '#3b82f6'
  }, [current.cpu])

  return (
    <div className="bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl p-5 flex flex-col h-[420px]">
      <div className="flex items-center justify-between mb-4 shrink-0">
        <div className="flex items-center space-x-2">
          <Activity className="w-4 h-4 text-emerald-400" />
          <h3 className="font-sans font-semibold text-body-sm text-stark-white uppercase tracking-wider">
            Resource Telemetry
          </h3>
        </div>
        <span className="text-[10px] font-mono text-gray-500 uppercase font-semibold">Real-Time Sync</span>
      </div>

      {/* 4 Metric Cards Grid */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-3 mb-4 shrink-0">
        {/* CPU Card */}
        <div className={`border p-3 rounded-xl flex flex-col items-center justify-center transition-all ${getCpuColorClasses(current.cpu)}`}>
          <Cpu className="w-4 h-4 mb-1" />
          <span className="text-base font-bold font-mono tracking-tight">{current.cpu.toFixed(1)}%</span>
          <span className="font-sans text-caption uppercase tracking-wide opacity-80">CPU</span>
        </div>

        {/* Memory Card */}
        <div className="bg-blue-500/10 border border-blue-500/20 p-3 rounded-xl flex flex-col items-center justify-center text-blue-400">
          <HardDrive className="w-4 h-4 mb-1" />
          <span className="text-base font-bold font-mono text-white tracking-tight">{current.ram.toFixed(1)}%</span>
          <span className="font-sans text-caption uppercase tracking-wide text-blue-400/80">Memory</span>
        </div>

        {/* Network Card */}
        <div className="bg-emerald-500/10 border border-emerald-500/20 p-3 rounded-xl flex flex-col items-center justify-center text-emerald-400">
          <Wifi className="w-4 h-4 mb-1" />
          <span className="text-base font-bold font-mono text-white tracking-tight">{current.net.toFixed(0)}</span>
          <span className="font-sans text-caption uppercase tracking-wide text-emerald-400/80">MB/s</span>
        </div>

        {/* Rows/Sec Card */}
        <div className="bg-purple-500/10 border border-purple-500/20 p-3 rounded-xl flex flex-col items-center justify-center text-purple-400">
          <Zap className="w-4 h-4 mb-1 text-purple-400 animate-pulse" />
          <span className="text-base font-bold font-mono text-white tracking-tight">{formatNumber(liveRowsPerSec)}</span>
          <span className="font-sans text-caption uppercase tracking-wide text-purple-400/80">Rows/Sec</span>
        </div>
      </div>

      {/* Chart Section */}
      <div className="flex-1 w-full min-h-0 relative pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <CartesianGrid stroke="rgba(255, 255, 255, 0.05)" vertical={false} />
            <YAxis
              domain={[0, 100]}
              ticks={[0, 50, 100]}
              stroke="#6b7280"
              tick={{ fill: '#6b7280', fontSize: 10, fontFamily: 'monospace' }}
              width={35}
            />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine
              x={current.time}
              stroke="#7c3aed"
              strokeDasharray="3 3"
              label={{ value: 'NOW', fill: '#a78bfa', fontSize: 9, position: 'top', fontFamily: 'monospace' }}
            />
            <Line
              type="monotone"
              dataKey="cpu"
              stroke={strokeColor}
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
            <Line type="monotone" dataKey="ram" stroke="#3b82f6" strokeWidth={2} dot={false} isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 bg-gradient-to-b from-transparent to-black/20 pointer-events-none" />
      </div>
    </div>
  )
}

export default React.memo(ResourceMonitor)
