import React, { useState, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { GitCompare, ArrowLeft, CheckCircle2, AlertCircle, Clock, Database, Layers, ArrowUpRight, ArrowDownRight, Equal, Table } from 'lucide-react'
import apiClient from '../apiClient'
import { API_BASE_URL } from '../config'
import { formatRows } from '../utils/formatRows'
import toast from 'react-hot-toast'

export default function MigrationCompare() {
  const [searchParams, setSearchParams] = useSearchParams()
  const navigate = useNavigate()

  const initialJobA = searchParams.get('jobA') || ''
  const initialJobB = searchParams.get('jobB') || ''

  const [jobIdA, setJobIdA] = useState(initialJobA)
  const [jobIdB, setJobIdB] = useState(initialJobB)

  const [historyJobs, setHistoryJobs] = useState([])
  const [comparisonData, setComparisonData] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchHistory()
  }, [])

  useEffect(() => {
    if (jobIdA && jobIdB) {
      fetchComparison(jobIdA, jobIdB)
    }
  }, [jobIdA, jobIdB])

  const fetchHistory = async () => {
    try {
      const res = await apiClient.fetchWithAuth(`${API_BASE_URL}/api/migrations/history`)
      if (res.ok) {
        const data = await res.json()
        const list = Array.isArray(data) ? data : (data.items || [])
        setHistoryJobs(list)
        
        // Auto-select top 2 jobs if none passed
        if (!jobIdA && !jobIdB && list.length >= 2) {
          setJobIdA(list[1].id)
          setJobIdB(list[0].id)
          setSearchParams({ jobA: list[1].id, jobB: list[0].id })
        } else if (!jobIdA && list.length >= 1) {
          setJobIdA(list[0].id)
        }
      }
    } catch (e) {
      console.error(e)
    }
  }

  const fetchComparison = async (idA, idB) => {
    setLoading(true)
    try {
      const res = await apiClient.fetchWithAuth(`${API_BASE_URL}/api/migrations/compare`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_id_a: idA, job_id_b: idB })
      })

      if (res.ok) {
        const data = await res.json()
        setComparisonData(data)
      } else {
        toast.error('Failed to fetch migration comparison data')
      }
    } catch (e) {
      toast.error('Error fetching comparison')
    } finally {
      setLoading(false)
    }
  }

  const handleSelectJobA = (id) => {
    setJobIdA(id)
    setSearchParams({ jobA: id, jobB: jobIdB })
  }

  const handleSelectJobB = (id) => {
    setJobIdB(id)
    setSearchParams({ jobA: jobIdA, jobB: id })
  }

  const getStatusBadge = (status) => {
    const s = (status || '').toUpperCase()
    if (s.includes('SUCCESS') || s.includes('COMPLETED') || s === 'VERIFIED') {
      return <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-mono text-[11px] font-bold">SUCCESS</span>
    }
    if (s.includes('FAIL')) {
      return <span className="px-2.5 py-0.5 rounded-full bg-red-500/10 border border-red-500/30 text-red-400 font-mono text-[11px] font-bold">FAILED</span>
    }
    return <span className="px-2.5 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 font-mono text-[11px] font-bold">{s}</span>
  }

  return (
    <div className="p-8 max-w-[1600px] mx-auto w-full flex flex-col space-y-6 min-h-full">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 shrink-0">
        <div className="flex items-center space-x-4">
          <button 
            onClick={() => navigate('/app/history')}
            className="w-10 h-10 flex items-center justify-center rounded-xl bg-white/5 hover:bg-white/10 text-white transition-colors border border-white/10 cursor-pointer"
            title="Back to Migration History"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
                <GitCompare className="w-5 h-5" />
              </div>
              <h1 className="font-sans text-h1 font-bold text-text-primary tracking-tight">
                Migration Job Comparison
              </h1>
            </div>
            <p className="text-muted-slate text-sm mt-1 font-mono">
              Side-by-side diff matrix comparing tables, row counts, performance, and checksum verification across migration runs.
            </p>
          </div>
        </div>
      </div>

      {/* Selectors Bar */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 shrink-0 glass-panel rounded-2xl p-4">
        <div>
          <label className="text-xs font-mono text-gray-400 font-bold block mb-1">Job A (Baseline)</label>
          <select
            value={jobIdA}
            onChange={(e) => handleSelectJobA(e.target.value)}
            className="w-full bg-[#050508] border border-white/10 rounded-xl px-3 py-2 text-white font-mono text-xs focus:outline-none focus:border-purple-500"
          >
            <option value="">-- Select Job A --</option>
            {historyJobs.map(j => (
              <option key={j.id} value={j.id}>
                {j.id} ({j.source_db || 'DB'} &rarr; {j.target_db || 'DB'}) - {j.timestamp || ''}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-xs font-mono text-gray-400 font-bold block mb-1">Job B (Comparison)</label>
          <select
            value={jobIdB}
            onChange={(e) => handleSelectJobB(e.target.value)}
            className="w-full bg-[#050508] border border-white/10 rounded-xl px-3 py-2 text-white font-mono text-xs focus:outline-none focus:border-purple-500"
          >
            <option value="">-- Select Job B --</option>
            {historyJobs.map(j => (
              <option key={j.id} value={j.id}>
                {j.id} ({j.source_db || 'DB'} &rarr; {j.target_db || 'DB'}) - {j.timestamp || ''}
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="p-16 text-center text-gray-400 font-mono bg-white/[0.02] border border-white/5 rounded-2xl">
          Calculating side-by-side migration comparison diff...
        </div>
      ) : !comparisonData ? (
        <div className="p-16 text-center border border-dashed border-white/10 rounded-2xl bg-white/[0.02] font-mono text-gray-400">
          Select two migration jobs above to display comparison analysis.
        </div>
      ) : (
        <>
          {/* Side-by-Side Job Headers */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 shrink-0">
            {/* Job A Card */}
            <div className="glass-panel rounded-2xl p-5 relative">
              <div className="flex items-center justify-between border-b border-white/10 pb-3 mb-3">
                <span className="text-xs font-mono text-purple-400 font-bold uppercase tracking-wider">Baseline — Job A</span>
                {getStatusBadge(comparisonData.job_a.status)}
              </div>
              <h3 className="text-lg font-bold text-white font-mono">{comparisonData.job_a.id}</h3>
              <div className="grid grid-cols-2 gap-3 font-mono text-xs mt-3">
                <div>
                  <span className="text-gray-400 block">Tables:</span>
                  <span className="text-white font-semibold">{comparisonData.job_a.tables_migrated || 0}</span>
                </div>
                <div>
                  <span className="text-gray-400 block">Total Rows:</span>
                  <span className="text-emerald-400 font-semibold">{formatRows(comparisonData.job_a.rows_migrated || 0)}</span>
                </div>
                <div>
                  <span className="text-gray-400 block">Duration:</span>
                  <span className="text-white font-semibold">{comparisonData.job_a.duration || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-gray-400 block">Date:</span>
                  <span className="text-white font-semibold">{comparisonData.job_a.timestamp?.slice(0, 10) || 'N/A'}</span>
                </div>
              </div>
            </div>

            {/* Job B Card */}
            <div className="glass-panel rounded-2xl p-5 relative">
              <div className="flex items-center justify-between border-b border-white/10 pb-3 mb-3">
                <span className="text-xs font-mono text-emerald-400 font-bold uppercase tracking-wider">Comparison — Job B</span>
                {getStatusBadge(comparisonData.job_b.status)}
              </div>
              <h3 className="text-lg font-bold text-white font-mono">{comparisonData.job_b.id}</h3>
              <div className="grid grid-cols-2 gap-3 font-mono text-xs mt-3">
                <div>
                  <span className="text-gray-400 block">Tables:</span>
                  <span className="text-white font-semibold">{comparisonData.job_b.tables_migrated || 0}</span>
                </div>
                <div>
                  <span className="text-gray-400 block">Total Rows:</span>
                  <span className="text-emerald-400 font-semibold">{formatRows(comparisonData.job_b.rows_migrated || 0)}</span>
                </div>
                <div>
                  <span className="text-gray-400 block">Duration:</span>
                  <span className="text-white font-semibold">{comparisonData.job_b.duration || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-gray-400 block">Date:</span>
                  <span className="text-white font-semibold">{comparisonData.job_b.timestamp?.slice(0, 10) || 'N/A'}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Metric Summary Diff Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 shrink-0">
            <div className="glass-panel rounded-2xl p-4 flex items-center justify-between">
              <div>
                <span className="text-xs font-mono text-gray-400 uppercase">Rows Diff (B vs A)</span>
                <div className="text-xl font-bold font-mono mt-1 text-white flex items-center">
                  {comparisonData.summary_diff.rows_diff > 0 ? (
                    <span className="text-emerald-400 flex items-center">
                      <ArrowUpRight className="w-5 h-5 mr-1" /> +{formatRows(comparisonData.summary_diff.rows_diff)}
                    </span>
                  ) : comparisonData.summary_diff.rows_diff < 0 ? (
                    <span className="text-red-400 flex items-center">
                      <ArrowDownRight className="w-5 h-5 mr-1" /> -{formatRows(Math.abs(comparisonData.summary_diff.rows_diff))}
                    </span>
                  ) : (
                    <span className="text-gray-300 flex items-center">
                      <Equal className="w-5 h-5 mr-1" /> 0 (Identical)
                    </span>
                  )}
                </div>
              </div>
              <span className="px-2.5 py-1 rounded-lg bg-white/5 border border-white/10 text-xs font-mono font-bold text-purple-300">
                {comparisonData.summary_diff.rows_pct_change}% diff
              </span>
            </div>

            <div className="glass-panel rounded-2xl p-4 flex items-center justify-between">
              <div>
                <span className="text-xs font-mono text-gray-400 uppercase">Tables Diff</span>
                <div className="text-xl font-bold font-mono mt-1 text-white">
                  {comparisonData.summary_diff.tables_diff >= 0 ? `+${comparisonData.summary_diff.tables_diff}` : comparisonData.summary_diff.tables_diff} tables
                </div>
              </div>
              <span className="px-2.5 py-1 rounded-lg bg-white/5 border border-white/10 text-xs font-mono font-bold text-gray-300">
                Tables Count
              </span>
            </div>

            <div className="glass-panel rounded-2xl p-4 flex items-center justify-between">
              <div>
                <span className="text-xs font-mono text-gray-400 uppercase">Status Parity</span>
                <div className="text-xl font-bold font-mono mt-1 text-white">
                  {comparisonData.summary_diff.status_match ? (
                    <span className="text-emerald-400 flex items-center">
                      <CheckCircle2 className="w-5 h-5 mr-1.5" /> Matched
                    </span>
                  ) : (
                    <span className="text-amber-400 flex items-center">
                      <AlertCircle className="w-5 h-5 mr-1.5" /> Mismatched
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Full Comparison Table Matrix */}
          <div className="glass-panel rounded-2xl p-5">
            <h3 className="text-base font-bold text-white font-mono mb-4 flex items-center">
              <Table className="w-4 h-4 mr-2 text-purple-400" />
              Per-Table Comparison Matrix ({comparisonData.matrix.length} Tables)
            </h3>

            <div className="overflow-x-auto custom-scrollbar">
              <table className="w-full text-left font-mono text-xs">
                <thead>
                  <tr className="border-b border-white/10 text-gray-400 uppercase tracking-wider">
                    <th className="pb-3 px-3">Table Name</th>
                    <th className="pb-3 px-3">Job A Rows</th>
                    <th className="pb-3 px-3">Job B Rows</th>
                    <th className="pb-3 px-3">Difference</th>
                    <th className="pb-3 px-3">% Change</th>
                    <th className="pb-3 px-3">Checksum Integrity</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {comparisonData.matrix.map(row => (
                    <tr key={row.table} className="hover:bg-white/[0.02] transition-colors">
                      <td className="py-3.5 px-3 font-semibold text-white flex items-center">
                        <Table className="w-3.5 h-3.5 mr-2 text-gray-400" />
                        {row.table}
                      </td>
                      <td className="py-3.5 px-3 text-gray-300">
                        {row.in_job_a ? formatRows(row.job_a_rows) : <span className="text-red-400">N/A</span>}
                      </td>
                      <td className="py-3.5 px-3 text-gray-300">
                        {row.in_job_b ? formatRows(row.job_b_rows) : <span className="text-red-400">N/A</span>}
                      </td>
                      <td className="py-3.5 px-3 font-bold">
                        {row.diff_rows > 0 ? (
                          <span className="text-emerald-400">+{formatRows(row.diff_rows)}</span>
                        ) : row.diff_rows < 0 ? (
                          <span className="text-red-400">-{formatRows(Math.abs(row.diff_rows))}</span>
                        ) : (
                          <span className="text-gray-400">0</span>
                        )}
                      </td>
                      <td className="py-3.5 px-3">
                        <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                          row.pct_diff > 0 ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' :
                          row.pct_diff < 0 ? 'bg-red-500/10 text-red-400 border border-red-500/30' :
                          'bg-gray-500/10 text-gray-400 border border-gray-500/30'
                        }`}>
                          {row.pct_diff > 0 ? `+${row.pct_diff}%` : `${row.pct_diff}%`}
                        </span>
                      </td>
                      <td className="py-3.5 px-3">
                        {row.checksum_match ? (
                          <span className="text-emerald-400 flex items-center text-[11px]">
                            <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Checksum Matched
                          </span>
                        ) : (
                          <span className="text-amber-400 flex items-center text-[11px]">
                            <AlertCircle className="w-3.5 h-3.5 mr-1" /> Checksum Changed
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
