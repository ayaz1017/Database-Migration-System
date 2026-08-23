import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import apiClient from '../apiClient'
import { API_BASE_URL } from '../config'
import { motion, AnimatePresence } from 'framer-motion'
import { ArrowLeft, CheckCircle2, Download, Copy, Check, ShieldCheck, Database, Layers, RefreshCw, FileText, GitCompare, AlertTriangle, XCircle, Loader2 } from 'lucide-react'
import SqlDiffViewer from '../components/Report/SqlDiffViewer'
import ValidationMatrix from '../components/Report/ValidationMatrix'
import ConstraintChecks from '../components/Report/ConstraintChecks'
import ObjectTranslationsViewer from '../components/Report/ObjectTranslationsViewer'
import { formatRows } from '../utils/formatRows'

export default function MigrationReport() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [copied, setCopied] = useState(false)
  const [activeTab, setActiveTab] = useState('all') // 'all', 'matrix', 'diff'

  const [jobData, setJobData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [fetchError, setFetchError] = useState(null)

  useEffect(() => {
    const fetchJob = async () => {
      setLoading(true)
      setFetchError(null)
      try {
        const res = await apiClient.get(`${API_BASE_URL}/api/migrations/${id}/details`)
        setJobData(res)
      } catch (e) {
        console.error('Failed to fetch migration details:', e)
        setFetchError(e.message || 'Failed to load report data')
      } finally {
        setLoading(false)
      }
    }
    if (id) fetchJob()
  }, [id])

  const statusStr = (jobData?.status || '').toLowerCase()
  const isFailed = statusStr === 'failed' || statusStr.includes('failed') || !!jobData?.error

  const validationReport = jobData?.validation_report || {}
  const matrixData = Array.isArray(validationReport.tables) ? validationReport.tables : []

  const rawScore = jobData?.validation_score ?? validationReport.validation_score ?? validationReport.summary?.overall_score
  const score = isFailed ? 0 : (typeof rawScore === 'number' ? rawScore : 100)

  const passedCount = isFailed ? 0 : matrixData.filter(t => t.row_count_match !== false && t.checksum_match !== false).length
  const failedCount = isFailed ? (matrixData.length || 1) : matrixData.filter(t => t.row_count_match === false || t.checksum_match === false).length
  const warnCount = 0

  const totalVerifiedRows = isFailed ? 0 : (jobData?.total_rows ?? matrixData.reduce((s, r) => s + (r.target_row_count ?? r.targetRows ?? 0), 0))
  const matchedTablesCount = isFailed ? 0 : matrixData.filter(t => t.row_count_match !== false).length
  const totalTablesCount = matrixData.length
  const checksumErrors = isFailed ? 0 : matrixData.filter(t => t.checksum_match === false).length

  const sourceSql = jobData?.source_sql || ''
  const targetSql = jobData?.target_sql || (Array.isArray(jobData?.ddl_statements) ? jobData.ddl_statements.join('\n\n') : '')

  const constraintData = {
    pk: {
      passed: isFailed ? 0 : matrixData.filter(t => t.pk_exists !== false).length,
      failed: isFailed ? matrixData.length : matrixData.filter(t => t.pk_exists === false).length,
      total: matrixData.length
    },
    fk: {
      passed: isFailed ? 0 : matrixData.filter(t => t.fk_exists !== false).length,
      failed: isFailed ? matrixData.length : matrixData.filter(t => t.fk_exists === false).length,
      total: matrixData.length
    },
    idx: {
      passed: isFailed ? 0 : matrixData.filter(t => t.indexes_match !== false).length,
      failed: isFailed ? matrixData.length : matrixData.filter(t => t.indexes_match === false).length,
      total: matrixData.length
    },
    view: {
      passed: isFailed ? 0 : matrixData.filter(t => t.constraints_match !== false).length,
      failed: isFailed ? matrixData.length : matrixData.filter(t => t.constraints_match === false).length,
      total: matrixData.length
    }
  }

  const totalConstraints = Object.values(constraintData).reduce((s, c) => s + c.total, 0)
  const passedConstraints = Object.values(constraintData).reduce((s, c) => s + c.passed, 0)
  const schemaIntegrity = totalConstraints > 0 ? Math.round((passedConstraints / totalConstraints) * 100) : (isFailed ? 0 : 100)

  const jobIdDisplay = id || 'N/A'

  const handleCopyJobId = () => {
    navigator.clipboard.writeText(jobIdDisplay)
    setCopied(true)
    setTimeout(() => setCopied(false), 1200)
  }

  const handleExportPDF = () => {
    document.body.classList.add('printing-report')
    const originalTitle = document.title
    document.title = `Fluxline-Report-${jobIdDisplay}`
    window.print()
    document.title = originalTitle
    document.body.classList.remove('printing-report')
  }

  const handleDownloadJSON = () => {
    const reportData = {
      job_id: jobIdDisplay,
      validation_score: score,
      status: isFailed ? 'FAILED' : 'VERIFIED',
      timestamp: jobData?.timestamp || new Date().toISOString(),
      error: jobData?.error || null,
      constraints: constraintData,
      matrix: matrixData,
      validation_report: validationReport,
      ddl_translation_log: jobData?.ddl_translation_log || []
    }
    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `validation_report_${jobIdDisplay}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  if (loading) {
    return (
      <div className="p-8 max-w-[1600px] mx-auto w-full min-h-[600px] flex flex-col items-center justify-center space-y-4">
        <Loader2 className="w-10 h-10 text-purple-400 animate-spin" />
        <p className="font-mono text-sm text-gray-400">Loading migration report details...</p>
      </div>
    )
  }

  if (fetchError) {
    return (
      <div className="p-8 max-w-[1600px] mx-auto w-full flex flex-col items-center justify-center space-y-6">
        <div className="w-16 h-16 rounded-2xl bg-red-500/10 border border-red-500/30 flex items-center justify-center">
          <AlertTriangle className="w-8 h-8 text-red-400" />
        </div>
        <div className="text-center">
          <h2 className="text-xl font-bold text-white">Report Not Found</h2>
          <p className="text-sm text-gray-400 mt-1">{fetchError}</p>
        </div>
        <button
          onClick={() => navigate('/app/history')}
          className="bg-white/10 hover:bg-white/20 text-white px-5 py-2.5 rounded-xl font-mono text-xs font-bold transition-colors flex items-center"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Migration History
        </button>
      </div>
    )
  }

  return (
    <div className="migration-report p-8 max-w-[1600px] mx-auto w-full flex flex-col space-y-6 min-h-full relative">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 shrink-0">
        <div className="flex items-center space-x-4">
          <button 
            onClick={() => navigate('/app/history')}
            className="w-10 h-10 flex items-center justify-center rounded-xl bg-white/5 hover:bg-white/10 text-white transition-colors border border-white/10"
            title="Back to Migration History"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center space-x-3">
              <h1 className="font-sans text-h1 font-bold text-text-primary tracking-tight flex items-center">
                Validation Report
              </h1>
              {isFailed ? (
                <span className="px-3 py-1 rounded-full bg-red-500/10 border border-red-500/30 text-red-400 font-mono text-xs font-bold flex items-center shadow-[0_0_15px_rgba(239,68,68,0.25)]">
                  <XCircle className="w-3.5 h-3.5 mr-1.5" />
                  FAILED
                </span>
              ) : (
                <span className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-mono text-xs font-bold flex items-center shadow-[0_0_15px_rgba(16,185,129,0.25)]">
                  <CheckCircle2 className="w-3.5 h-3.5 mr-1.5" />
                  VERIFIED {score}% PASS
                </span>
              )}
            </div>
            <div className="flex items-center space-x-3 font-mono mt-1 text-sm text-gray-400">
              <span>Job ID:</span>
              <button 
                onClick={handleCopyJobId}
                className="bg-white/[0.04] hover:bg-white/[0.08] border border-white/10 px-2.5 py-0.5 rounded-lg text-gray-200 font-semibold flex items-center space-x-1.5 transition-colors cursor-pointer relative"
                title="Copy Job ID"
              >
                <span>{jobIdDisplay}</span>
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-gray-400" />}
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
        
        {/* Header Action Buttons */}
        <div className="flex items-center space-x-3">
          <button 
            onClick={() => navigate(`/app/compare?jobA=${jobIdDisplay}`)}
            className="bg-purple-500/10 hover:bg-purple-500/20 text-purple-300 border border-purple-500/30 px-4 py-2 rounded-xl font-mono text-xs font-bold transition-colors flex items-center cursor-pointer"
          >
            <GitCompare className="w-4 h-4 mr-2 text-purple-400" />
            Compare Run
          </button>
          <button 
            onClick={handleDownloadJSON}
            className="bg-white/5 hover:bg-white/10 text-gray-300 border border-white/10 px-4 py-2 rounded-xl font-mono text-xs font-bold transition-colors flex items-center cursor-pointer"
          >
            <FileText className="w-4 h-4 mr-2 text-purple-400" />
            JSON Report
          </button>
          <button 
            onClick={handleExportPDF}
            className="bg-emerald-500 hover:bg-emerald-400 text-white px-5 py-2 rounded-xl font-mono text-xs font-bold transition-colors flex items-center shadow-[0_0_20px_rgba(16,185,129,0.35)] cursor-pointer"
          >
            <Download className="w-4 h-4 mr-2" />
            Export Report
          </button>
        </div>
      </div>

      {/* Prominent Failure Banner if Migration Failed */}
      {isFailed && (
        <motion.div 
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-r from-red-500/15 via-red-900/20 to-[#0c0c14] border border-red-500/40 rounded-2xl p-5 shrink-0 flex items-start space-x-4 shadow-[0_0_25px_rgba(239,68,68,0.15)]"
        >
          <div className="w-11 h-11 rounded-xl bg-red-500/20 border border-red-500/40 flex items-center justify-center shrink-0 mt-0.5">
            <AlertTriangle className="w-6 h-6 text-red-400 animate-pulse" />
          </div>
          <div className="flex-1">
            <h3 className="font-sans font-bold text-base text-red-400 flex items-center gap-2">
              Migration Execution Failed
            </h3>
            <p className="font-mono text-xs text-red-200/90 mt-1.5 bg-black/40 border border-red-500/20 rounded-xl p-3 whitespace-pre-wrap font-medium">
              {jobData?.error || 'An unexpected error halted the migration process. No tables or rows were migrated.'}
            </p>
          </div>
        </motion.div>
      )}

      {/* Navigation Tabs Bar */}
      <div className="flex items-center space-x-2 border-b border-white/10 pb-3 shrink-0">
        <button
          onClick={() => setActiveTab('all')}
          className={`px-4 py-2 rounded-xl font-sans font-medium text-body-sm transition-all transition-snappy cursor-pointer ${
            activeTab === 'all' 
              ? 'bg-purple-500/20 border border-purple-500/40 text-purple-300 shadow-[0_0_15px_rgba(168,85,247,0.2)]' 
              : 'bg-white/[0.03] text-gray-400 hover:text-white border border-white/5'
          }`}
        >
          All Overview
        </button>
        <button
          onClick={() => setActiveTab('diff')}
          className={`px-4 py-2 rounded-xl font-sans font-medium text-body-sm transition-all transition-snappy cursor-pointer ${
            activeTab === 'diff' 
              ? 'bg-purple-500/20 border border-purple-500/40 text-purple-300 shadow-[0_0_15px_rgba(168,85,247,0.2)]' 
              : 'bg-white/[0.03] text-gray-400 hover:text-white border border-white/5'
          }`}
        >
          DDL Schema Diff
        </button>
        <button
          onClick={() => setActiveTab('matrix')}
          className={`px-4 py-2 rounded-xl font-sans font-medium text-body-sm transition-all transition-snappy cursor-pointer ${
            activeTab === 'matrix' 
              ? 'bg-purple-500/20 border border-purple-500/40 text-purple-300 shadow-[0_0_15px_rgba(168,85,247,0.2)]' 
              : 'bg-white/[0.03] text-gray-400 hover:text-white border border-white/5'
          }`}
        >
          Data Consistency Matrix
        </button>
        <button
          onClick={() => setActiveTab('objects')}
          className={`px-4 py-2 rounded-xl font-sans font-medium text-body-sm transition-all transition-snappy cursor-pointer ${
            activeTab === 'objects' 
              ? 'bg-purple-500/20 border border-purple-500/40 text-purple-300 shadow-[0_0_15px_rgba(168,85,247,0.2)]' 
              : 'bg-white/[0.03] text-gray-400 hover:text-white border border-white/5'
          }`}
        >
          Views & Procedures ({jobData?.object_translations?.length || 0})
        </button>
      </div>

      {/* Validation Score Banner */}
      <div className="glass-panel rounded-2xl p-5 shrink-0 relative overflow-hidden">
        <div className="absolute right-0 top-0 bottom-0 w-96 bg-gradient-to-l from-emerald-500/10 via-purple-500/5 to-transparent pointer-events-none" />
        
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
          <div className="flex items-center space-x-5">
            {/* SVG Circular Radial Progress Gauge */}
            <div className="flex flex-col items-center shrink-0">
              <svg viewBox="0 0 120 120" className="w-28 h-28">
                <circle cx="60" cy="60" r="54" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="8" />
                <circle cx="60" cy="60" r="54" fill="none" 
                  stroke={isFailed ? '#ef4444' : score >= 80 ? '#10b981' : score >= 50 ? '#fbbf24' : '#ef4444'}
                  strokeWidth="8" strokeLinecap="round"
                  strokeDasharray={`${(score / 100) * 339.3} 339.3`}
                  transform="rotate(-90 60 60)" 
                  style={{ transition: 'stroke-dasharray 1s ease' }}
                />
                <text x="60" y="60" textAnchor="middle" dominantBaseline="central" 
                  fill="white" fontSize="28" fontWeight="700" fontFamily="var(--font-sans)"
                >{score}%</text>
              </svg>
              <div className="mt-2 text-[13px] font-medium text-center">
                {isFailed ? <span className="text-red-400">Migration Failed — 0% Verified</span> :
                 score > 90 ? <span className="text-emerald-400">Excellent — schema fully preserved</span> :
                 score >= 70 ? <span className="text-blue-400">Good — minor coercions applied</span> :
                 score >= 50 ? <span className="text-amber-400">Review recommended</span> :
                 <span className="text-red-400">Manual review required</span>}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-6 border-t lg:border-t-0 lg:border-l border-white/10 pt-4 lg:pt-0 lg:pl-6">
            <div>
              <span className="font-sans text-caption text-text-secondary uppercase tracking-wider block">Total Rows Verified</span>
              <span className="font-mono font-semibold text-text-primary mt-0.5 block">{formatRows(totalVerifiedRows)}</span>
            </div>
            <div>
              <span className="font-sans text-caption text-text-secondary uppercase tracking-wider block">Tables Checked</span>
              <span className={`font-mono font-semibold ${isFailed ? 'text-red-400' : matchedTablesCount === totalTablesCount && totalTablesCount > 0 ? 'text-emerald-400' : 'text-amber-400'} mt-0.5 block`}>
                {isFailed ? '0 / 0 Matched' : `${matchedTablesCount} / ${totalTablesCount} Matched`}
              </span>
            </div>
            <div>
              <span className="font-sans text-caption text-text-secondary uppercase tracking-wider block">Checksum Mismatch</span>
              <span className={`font-mono font-semibold ${isFailed || checksumErrors > 0 ? 'text-red-400' : 'text-emerald-400'} mt-0.5 block`}>
                {isFailed ? '0 Errors' : `${checksumErrors} Errors`}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Summary Bar */}
      <div className="flex items-center gap-4 px-4 py-3 rounded-xl bg-white/[0.03] border border-white/5 mb-4 mt-6 shrink-0">
        <span className="text-[13px] font-mono text-emerald-400">✓ {passedCount} tables passed</span>
        <span className="text-[13px] font-mono text-amber-400">⚠ {warnCount} warnings</span>
        <span className="text-[13px] font-mono text-red-400">✗ {failedCount} failed</span>
      </div>

      {/* Constraints Summary Cards */}
      {(activeTab === 'all' || activeTab === 'matrix') && (
        <div className="shrink-0">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`bg-gradient-to-r ${isFailed ? 'from-red-500/10 via-[#0c0c14]/90 to-[#0c0c14]/90 border-red-500/20' : 'from-emerald-500/10 via-[#0c0c14]/90 to-[#0c0c14]/90 border-emerald-500/20'} backdrop-blur-xl border rounded-2xl p-5 mb-4 flex items-center justify-between`}
          >
            <div className="flex items-center gap-4">
              <div className={`w-12 h-12 rounded-xl ${isFailed ? 'bg-red-500/15 border-red-500/30' : 'bg-emerald-500/15 border-emerald-500/30'} border flex items-center justify-center`}>
                <ShieldCheck className={`w-6 h-6 ${isFailed ? 'text-red-400' : 'text-emerald-400'}`} />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white font-mono">Schema Integrity: {schemaIntegrity}%</h3>
                <p className="text-xs text-text-secondary mt-0.5 font-mono">
                  {passedConstraints}/{totalConstraints} constraints verified • {formatRows(totalVerifiedRows)} rows validated
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {isFailed ? (
                <span className="text-[10px] font-mono font-bold text-red-400 bg-red-500/10 border border-red-500/30 px-3 py-1.5 rounded-full flex items-center gap-1">
                  <XCircle className="w-3.5 h-3.5" />
                  FAILED
                </span>
              ) : (
                <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-3 py-1.5 rounded-full flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  {schemaIntegrity === 100 ? 'ALL PASSED' : `${schemaIntegrity}% PASSED`}
                </span>
              )}
            </div>
          </motion.div>
          <ConstraintChecks data={constraintData} />
        </div>
      )}

      {/* Main Content Grid */}
      {activeTab === 'all' && (
        <div className="flex flex-col space-y-6">
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            <div className="xl:col-span-1 flex flex-col">
              <SqlDiffViewer sourceSql={sourceSql} targetSql={targetSql} />
            </div>
            <div className="xl:col-span-1 flex flex-col">
              <ValidationMatrix data={matrixData} />
            </div>
          </div>

          {jobData?.object_translations?.length > 0 && (
            <ObjectTranslationsViewer objectTranslations={jobData.object_translations} />
          )}
        </div>
      )}

      {activeTab === 'diff' && (
        <div className="w-full">
          <SqlDiffViewer sourceSql={sourceSql} targetSql={targetSql} />
        </div>
      )}

      {activeTab === 'matrix' && (
        <div className="w-full">
          <ValidationMatrix data={matrixData} />
        </div>
      )}

      {activeTab === 'objects' && (
        <div className="w-full">
          <ObjectTranslationsViewer objectTranslations={jobData?.object_translations || []} />
        </div>
      )}
      
      {/* Bottom padding for scroll */}
      <div className="h-10 shrink-0" />
    </div>
  )
}
