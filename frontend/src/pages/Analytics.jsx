import React, { useState, useEffect, useMemo } from 'react'
import { motion } from 'framer-motion'
import KPICard from '../components/Analytics/KPICard'
import ThroughputChart from '../components/Analytics/ThroughputChart'
import DialectDistribution from '../components/Analytics/DialectDistribution'
import FailureRCACards from '../components/Analytics/FailureRCACards'
import apiClient from '../apiClient'
import { API_BASE_URL } from '../config'
import { Loader2 } from 'lucide-react'

export default function Analytics() {
  const [history, setHistory] = useState([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await apiClient.fetchWithAuth(`${API_BASE_URL}/api/migrations/history`)
        if (res.ok) {
          const data = await res.json()
          const items = Array.isArray(data) ? data : (data.items || [])
          setHistory(items)
        }
      } catch (e) {
        console.error('Failed to fetch migration history for analytics:', e)
      } finally {
        setIsLoading(false)
      }
    }
    fetchHistory()
  }, [])

  // Derived Metrics
  const { kpiData, throughputData, dialectData, failureData } = useMemo(() => {
    if (!history.length) {
      return {
        kpiData: {
          successRate: { value: 0, trend: 0, type: 'percentage', data: [] },
          totalRows: { value: 0, trend: 0, type: 'number', data: [] },
          dataMigrated: { value: 0, trend: 0, type: 'data', data: [] },
          avgThroughput: { value: 0, trend: 0, type: 'throughput', data: [] }
        },
        throughputData: [],
        dialectData: [],
        failureData: []
      }
    }

    let successCount = 0
    let totalRows = 0
    let totalDurationSeconds = 0

    const tData = []
    const dMap = {}
    const fData = []

    // Sort history chronologically for timeline charts
    const sortedHistory = [...history].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())

    sortedHistory.forEach((job, idx) => {
      const isSuccess = job.status === 'SUCCESS' || (job.status && job.status.startsWith('COMPLETED'))
      if (isSuccess) successCount++
      
      const rows = job.rows_migrated || 0
      totalRows += rows
      
      const durationStr = job.duration || '0s'
      const durationSeconds = parseFloat(durationStr.replace('s', '')) || 1
      totalDurationSeconds += durationSeconds

      const throughput = (rows * 0.0005) / durationSeconds // Mock MB/s calculation based on rows
      
      tData.push({
        timestamp: new Date(job.timestamp).getTime(),
        throughput: Math.floor(throughput),
        rows: Math.floor(rows / durationSeconds)
      })

      const mapping = `${job.source_db || 'Unknown'} -> ${job.target_db || 'Unknown'}`
      if (!dMap[mapping]) dMap[mapping] = { count: 0, failures: 0 }
      dMap[mapping].count++
      if (!isSuccess) dMap[mapping].failures++

      if (job.status === 'FAILED') {
        fData.push({
          id: job.id,
          errorType: 'Migration Failure',
          time: new Date(job.timestamp).toLocaleTimeString(),
          message: `Job ${job.id} failed during execution.`,
          querySnippet: `Source: ${job.source_db} | Target: ${job.target_db} | Tables: ${job.tables_migrated}`
        })
      }
    })

    const successRate = history.length > 0 ? (successCount / history.length) * 100 : 0
    const totalDataTB = (totalRows * 0.005) / 1000 // Mock 5GB per million rows
    const avgThroughput = totalDurationSeconds > 0 ? ((totalRows * 0.0005) / totalDurationSeconds) : 0

    // Build final KPI object
    const finalKpi = {
      successRate: { value: successRate, trend: 1.2, type: 'percentage', data: tData.map(d => ({val: (d.rows > 0 ? 100 : 0)})) },
      totalRows: { value: totalRows, trend: 5.4, type: 'number', data: tData.map(d => ({val: d.rows})) },
      dataMigrated: { value: totalDataTB, trend: 2.1, type: 'data', data: tData.map(d => ({val: d.throughput})) },
      avgThroughput: { value: Math.floor(avgThroughput), trend: 8.5, type: 'throughput', data: tData.map(d => ({val: d.throughput})) },
    }

    const finalDialect = Object.keys(dMap).map(name => ({
      name,
      value: dMap[name].count,
      failureRate: Math.round((dMap[name].failures / dMap[name].count) * 100)
    })).sort((a,b) => b.value - a.value).slice(0, 5) // top 5

    return { kpiData: finalKpi, throughputData: tData, dialectData: finalDialect, failureData: fData.slice(0, 10) }

  }, [history])

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-accent" />
      </div>
    )
  }

  return (
    <div className="p-8 max-w-[1600px] mx-auto w-full flex flex-col space-y-6 min-h-full">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 shrink-0">
        <div>
          <motion.h1 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="font-sans text-h1 font-bold text-text-primary tracking-tight"
          >
            Global Analytics
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="font-sans text-body text-text-secondary mt-2"
          >
            Enterprise fleet monitoring based on {history.length} historical migrations.
          </motion.p>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 shrink-0">
        <KPICard title="Migration Success Rate" value={kpiData.successRate.value} trend={kpiData.successRate.trend} type={kpiData.successRate.type} sparklineData={kpiData.successRate.data} color="#10b981" />
        <KPICard title="Total Rows Migrated" value={kpiData.totalRows.value} trend={kpiData.totalRows.trend} type={kpiData.totalRows.type} sparklineData={kpiData.totalRows.data} color="#3b82f6" />
        <KPICard title="Total Data Volume" value={kpiData.dataMigrated.value} trend={kpiData.dataMigrated.trend} type={kpiData.dataMigrated.type} sparklineData={kpiData.dataMigrated.data} color="#f59e0b" />
        <KPICard title="Average Throughput" value={kpiData.avgThroughput.value} trend={kpiData.avgThroughput.trend} type={kpiData.avgThroughput.type} sparklineData={kpiData.avgThroughput.data} color="#7c3aed" />
      </div>

      {/* Main Charts Row */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2">
          <ThroughputChart data={throughputData} />
        </div>
        <div className="xl:col-span-1">
          <DialectDistribution data={dialectData} />
        </div>
      </div>

      {/* Secondary Row */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <FailureRCACards data={failureData} />
      </div>
      
      {/* Bottom padding for scroll */}
      <div className="h-10 shrink-0" />
    </div>
  )
}
