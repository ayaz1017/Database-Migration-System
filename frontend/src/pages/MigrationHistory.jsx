import { useState, useEffect, useMemo, useCallback } from 'react'
import apiClient from '../apiClient'
import { Link, useNavigate } from 'react-router-dom'
import { Search, SlidersHorizontal, ChevronRight, CheckCircle2, ShieldAlert, Calendar, Clock, Layers, Database, RefreshCw, X, Plus, Zap, GitCompare } from 'lucide-react'
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion'
import { DialectIcon } from '../components/DialectBadge'
import EmptyState from '../components/EmptyState'
import { getRelativeTime } from './Dashboard'
import { API_BASE_URL } from '../config'
import { formatRows } from '../utils/formatRows'

export default function MigrationHistory() {
  const [history, setHistory] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('ALL')
  const [sourceDialect, setSourceDialect] = useState('ALL')
  const [targetDialect, setTargetDialect] = useState('ALL')
  const [sortBy, setSortBy] = useState('recent') // 'recent', 'oldest', 'duration', 'rows'
  const [selectedJobs, setSelectedJobs] = useState([])

  // Pagination
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 8

  const navigate = useNavigate()
  const shouldReduceMotion = useReducedMotion()

  const fetchHistory = useCallback(async () => {
    setIsLoading(true)
    try {
      const data = await apiClient.get(`${API_BASE_URL}/api/migrations/history?page=1&page_size=200`)
      const items = Array.isArray(data) ? data : (data?.items || [])
      const mapped = items.map(job => ({
        id: job.id,
        name: job.id,
        date: job.timestamp,
        sourceType: (job.source_db || 'UNKNOWN').toUpperCase(),
        targetType: (job.target_db || 'UNKNOWN').toUpperCase(),
        tables: job.tables_migrated || 0,
        rows: job.rows_migrated || 0,
        time: job.duration ? parseFloat(job.duration.replace('s', '')) || 0 : 0,
        score: job.status === 'SUCCESS' ? 100 : (job.status || '').startsWith('COMPLETED') ? 95 : 0,
        status: job.status || 'UNKNOWN'
      }))
      setHistory(mapped)
    } catch (e) {
      console.error('Failed to fetch migration history:', e)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchHistory()
  }, [fetchHistory])

  // Memoized search, filters, and sorting calculation
  const filteredHistory = useMemo(() => {
    let result = [...history]

    // Search filter (id or names)
    if (search.trim()) {
      const query = search.toLowerCase()
      result = result.filter(item =>
        item.id.toLowerCase().includes(query) ||
        item.sourceType.toLowerCase().includes(query) ||
        item.targetType.toLowerCase().includes(query) ||
        item.name.toLowerCase().includes(query)
      )
    }

    // Status filter
    if (statusFilter !== 'ALL') {
      result = result.filter(item => {
        if (statusFilter === 'SUCCESS') return item.status === 'SUCCESS'
        if (statusFilter === 'FAILED') return item.status === 'FAILED'
        if (statusFilter === 'IN_PROGRESS') return item.status === 'IN_PROGRESS' || item.status === 'RUNNING'
        if (statusFilter === 'PARTIAL') return item.status === 'PARTIAL' || item.status.startsWith('COMPLETED')
        return true
      })
    }

    if (sourceDialect !== 'ALL') {
      result = result.filter(item => item.sourceType.toLowerCase() === sourceDialect.toLowerCase())
    }


    if (targetDialect !== 'ALL') {
      result = result.filter(item => item.targetType.toLowerCase() === targetDialect.toLowerCase())
    }


    result.sort((a, b) => {
      if (sortBy === 'recent') {
        return new Date(b.date) - new Date(a.date)
      }
      if (sortBy === 'oldest') {
        return new Date(a.date) - new Date(b.date)
      }
      if (sortBy === 'duration') {
        return b.time - a.time
      }
      if (sortBy === 'rows') {
        return b.rows - a.rows
      }
      return 0
    })

    return result
  }, [history, search, statusFilter, sourceDialect, targetDialect, sortBy])

  // Get current items
  const indexOfLastItem = currentPage * itemsPerPage
  const indexOfFirstItem = indexOfLastItem - itemsPerPage
  const currentItems = filteredHistory.slice(indexOfFirstItem, indexOfLastItem)
  const totalPages = Math.ceil(filteredHistory.length / itemsPerPage)

  const handleClearFilters = () => {
    setSearch('')
    setStatusFilter('ALL')
    setSourceDialect('ALL')
    setTargetDialect('ALL')
    setSortBy('recent')
  }

  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.04
      }
    }
  }

  const cardVariants = {
    hidden: { opacity: 0, y: 12 },
    show: {
      opacity: 1,
      y: 0,
      transition: {
        type: 'spring',
        stiffness: 260,
        damping: 24
      }
    },
    exit: {
      opacity: 0,
      scale: 0.95,
      transition: { duration: 0.15 }
    }
  }

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8 relative min-h-[calc(100vh-4rem)]">
      {/* Background ambient glows */}
      <div className="absolute top-[-10%] left-[10%] w-[500px] h-[500px] rounded-full bg-accent/5 blur-[120px] -z-10 pointer-events-none"></div>
      <div className="absolute bottom-[-10%] right-[10%] w-[450px] h-[450px] rounded-full bg-info/5 blur-[100px] -z-10 pointer-events-none"></div>

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-border-default pb-6">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-text-secondary mb-2">
            <Link to="/app" className="hover:text-text-primary transition-colors">Dashboard</Link>
            <span>/</span>
            <span className="text-text-primary font-semibold">History</span>
          </div>
          <h1 className="font-sans text-h1 font-bold text-text-primary tracking-tight">
            Migration History
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            Browse and filter through all past database migration execution results.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <motion.button
            whileHover={shouldReduceMotion ? {} : { scale: 1.02 }}
            whileTap={shouldReduceMotion ? {} : { scale: 0.98 }}
            onClick={fetchHistory}
            className="p-2.5 bg-bg-raised hover:bg-bg-overlay border border-border-default text-text-secondary hover:text-text-primary rounded-xl transition-all"
            title="Refresh History"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-accent-solid' : ''}`} />
          </motion.button>

          <motion.div
            whileHover={shouldReduceMotion ? {} : { scale: 1.02 }}
            whileTap={shouldReduceMotion ? {} : { scale: 0.98 }}
          >
            <Link
              to="/app/new"
              className="inline-flex items-center space-x-2 px-5 py-2.5 bg-accent-solid hover:bg-accent-hover text-text-inverse text-xs font-semibold rounded-md transition-all shadow-sm"
            >
              <Plus className="w-4 h-4" />
              <span>New Migration</span>
            </Link>
          </motion.div>
        </div>
      </div>

      {/* Filter and Search Panel */}
      <div className="bg-bg-raised/80 backdrop-blur-xl border border-border-default rounded-xl p-5 shadow-md space-y-4">
        <div className="flex flex-col lg:flex-row gap-4">

          {/* Search box */}
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-text-tertiary" />
            <input
              type="text"
              placeholder="Search by job ID, database type..."
              value={search}
              onChange={e => { setSearch(e.target.value); setCurrentPage(1); }}
              className="w-full bg-bg-overlay border border-border-default rounded-md pl-10 pr-4 py-2.5 text-sm text-text-primary placeholder-text-tertiary focus:border-accent focus:ring-1 focus:ring-accent focus:outline-none transition-all"
            />
            {search && (
              <button
                onClick={() => { setSearch(''); setCurrentPage(1); }}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-text-secondary hover:text-text-primary"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Quick Filters Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 lg:w-auto">
            {/* Status select */}
            <div className="flex flex-col space-y-1.5">
              <select
                value={statusFilter}
                onChange={e => { setStatusFilter(e.target.value); setCurrentPage(1); }}
                className="bg-bg-overlay border border-border-default rounded-md px-3 py-2.5 font-sans text-caption text-text-primary focus:border-accent focus:ring-1 focus:ring-accent focus:outline-none transition-all cursor-pointer font-medium appearance-none"
              >
                <option value="ALL">Status: All</option>
                <option value="SUCCESS">Completed</option>
                <option value="PARTIAL">Partial</option>
                <option value="FAILED">Failed</option>
                <option value="IN_PROGRESS">In Progress</option>
              </select>
            </div>

            {/* Source Dialect select */}
            <div className="flex flex-col space-y-1.5">
              <select
                value={sourceDialect}
                onChange={e => { setSourceDialect(e.target.value); setCurrentPage(1); }}
                className="bg-bg-overlay border border-border-default rounded-md px-3 py-2.5 font-sans text-caption text-text-primary focus:border-accent focus:ring-1 focus:ring-accent focus:outline-none transition-all cursor-pointer font-medium appearance-none"
              >
                <option value="ALL">Source: All</option>
                <option value="MSSQL">MSSQL</option>
                <option value="MYSQL">MySQL</option>
                <option value="POSTGRES">PostgreSQL</option>
                <option value="ORACLE">Oracle</option>
              </select>
            </div>

            {/* Target Dialect select */}
            <div className="flex flex-col space-y-1.5">
              <select
                value={targetDialect}
                onChange={e => { setTargetDialect(e.target.value); setCurrentPage(1); }}
                className="bg-bg-overlay border border-border-default rounded-md px-3 py-2.5 font-sans text-caption text-text-primary focus:border-accent focus:ring-1 focus:ring-accent focus:outline-none transition-all cursor-pointer font-medium appearance-none"
              >
                <option value="ALL">Target: All</option>
                <option value="POSTGRES">PostgreSQL</option>
                <option value="MYSQL">MySQL</option>
                <option value="MSSQL">MSSQL</option>
                <option value="ORACLE">Oracle</option>
              </select>
            </div>

            {/* Sort order select */}
            <div className="flex flex-col space-y-1.5">
              <select
                value={sortBy}
                onChange={e => { setSortBy(e.target.value); setCurrentPage(1); }}
                className="bg-bg-overlay border border-border-default rounded-md px-3 py-2.5 font-sans text-caption text-text-primary focus:border-accent focus:ring-1 focus:ring-accent focus:outline-none transition-all cursor-pointer font-medium appearance-none"
              >
                <option value="recent">Sort: Most Recent</option>
                <option value="oldest">Sort: Oldest First</option>
                <option value="duration">Sort: Duration</option>
                <option value="rows">Sort: Row Count</option>
              </select>
            </div>

          </div>
        </div>

        {/* Filters Summary / Clear action */}
        {(statusFilter !== 'ALL' || sourceDialect !== 'ALL' || targetDialect !== 'ALL' || search || sortBy !== 'recent') && (
          <div className="flex items-center justify-between pt-2 border-t border-border-default text-xs">
            <span className="text-text-secondary font-medium">
              Found {filteredHistory.length} matches in history
            </span>
            <button
              onClick={handleClearFilters}
              className="text-accent hover:text-accent-solid font-bold flex items-center gap-1 transition-colors"
            >
              <X className="w-3 h-3" /> Clear all filters
            </button>
          </div>
        )}
      </div>

      {/* Main Grid View */}
      {isLoading ? (
        <div className="space-y-4">
          <div className="h-24 bg-bg-raised/30 border border-border-default rounded-xl animate-pulse"></div>
          <div className="h-24 bg-bg-raised/30 border border-border-default rounded-xl animate-pulse"></div>
          <div className="h-24 bg-bg-raised/30 border border-border-default rounded-xl animate-pulse"></div>
          <div className="h-24 bg-bg-raised/30 border border-border-default rounded-xl animate-pulse"></div>
        </div>
      ) : history.length === 0 ? (
        <EmptyState
          icon={Database}
          title="No migrations found"
          description="It looks like you haven't run any database replication sessions yet. Build a new pipeline config and start the replication engine."
          actionLabel="Start a migration"
          onAction={() => navigate('/app/new')}
        />
      ) : filteredHistory.length === 0 ? (
        <EmptyState
          icon={SlidersHorizontal}
          title="No results match your filters"
          description="Try broadening your criteria, clearing your search query, or checking for other database dialect flows."
          actionLabel="Clear Filters"
          onAction={handleClearFilters}
        />
      ) : (
        <div className="space-y-6">
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="show"
            className="grid gap-4"
          >
            <AnimatePresence mode="popLayout">
              {currentItems.map(m => (
                <motion.div
                  key={m.id}
                  layout={!shouldReduceMotion}
                  variants={cardVariants}
                  whileHover={shouldReduceMotion ? {} : { y: -3, borderColor: 'var(--color-accent)', boxShadow: 'var(--shadow-md)' }}
                  className="bg-bg-raised/50 hover:bg-bg-raised border border-border-default rounded-xl transition-all duration-300 relative overflow-hidden group shadow-sm"
                >
                  {m.status === 'IN_PROGRESS' && (
                    <div className="absolute top-0 left-0 w-full h-[2px] bg-accent animate-pulse"></div>
                  )}

                  <Link to={`/app/report/${m.id}`} className="block p-6">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">

                      <div className="space-y-3">
                        <div className="flex flex-wrap items-center gap-3">
                          <input
                            type="checkbox"
                            checked={selectedJobs.includes(m.id)}
                            onChange={(e) => {
                              e.stopPropagation()
                              if (selectedJobs.includes(m.id)) {
                                setSelectedJobs(selectedJobs.filter(j => j !== m.id))
                              } else {
                                if (selectedJobs.length >= 2) {
                                  setSelectedJobs([selectedJobs[1], m.id])
                                } else {
                                  setSelectedJobs([...selectedJobs, m.id])
                                }
                              }
                            }}
                            onClick={(e) => e.stopPropagation()}
                            className="w-4 h-4 rounded border-border-default bg-bg-sunken accent-purple-500 cursor-pointer shrink-0"
                            title="Select for comparison"
                          />
                          <h3 className="font-mono text-body-sm font-bold text-text-primary tracking-tight">{m.name}</h3>

                          {m.status === 'SUCCESS' ? (
                            <span className="inline-flex items-center space-x-1 py-0.5 px-2 rounded-md bg-success-muted border border-success/20 text-success text-[10px] font-mono font-medium shadow-sm">
                              <CheckCircle2 className="w-3 h-3 text-success" />
                              <span>COMPLETED</span>
                            </span>
                          ) : m.status.toUpperCase().includes('AUTO-APPROVE') ? (
                            <>
                              <span className="inline-flex items-center space-x-1 py-0.5 px-2 rounded-md bg-warning-muted border border-warning/20 text-warning text-[10px] font-mono font-medium shadow-sm">
                                <CheckCircle2 className="w-3 h-3 text-warning" />
                                <span>PARTIAL</span>
                              </span>
                              <span className="inline-flex items-center space-x-1 py-0.5 px-2 rounded-md bg-accent-muted border border-accent/20 text-accent-solid text-[10px] font-mono font-bold shadow-sm uppercase tracking-wider">
                                <Zap className="w-3 h-3 text-accent-solid" />
                                <span>AUTO</span>
                              </span>
                            </>
                          ) : m.status === 'PARTIAL' || m.status.toUpperCase().startsWith('COMPLETED') ? (
                            <span className="inline-flex items-center space-x-1 py-0.5 px-2 rounded-md bg-warning-muted border border-warning/20 text-warning text-[10px] font-mono font-medium shadow-sm">
                              <CheckCircle2 className="w-3 h-3 text-warning" />
                              <span>PARTIAL</span>
                            </span>
                          ) : m.status === 'IN_PROGRESS' || m.status === 'RUNNING' ? (
                            <span className="inline-flex items-center space-x-1.5 py-0.5 px-2 rounded-md bg-accent-muted border border-accent/25 text-accent-solid text-[10px] font-mono font-medium shadow-sm">
                              <span className="w-1.5 h-1.5 rounded-full bg-accent animate-ping"></span>
                              <span>IN_PROGRESS</span>
                            </span>
                          ) : (
                            <span className="inline-flex items-center space-x-1 py-0.5 px-2 rounded-md bg-error-muted border border-error/20 text-error text-[10px] font-mono font-medium shadow-sm">
                              <ShieldAlert className="w-3 h-3 text-error" />
                              <span>FAILED</span>
                            </span>
                          )}

                          <span className="text-xs text-text-secondary font-mono flex items-center gap-1.5">
                            <Calendar className="w-3.5 h-3.5 text-text-tertiary" />
                            {getRelativeTime(m.date)}
                          </span>
                        </div>

                        {/* Dialect flow info */}
                        <div className="flex items-center space-x-3">
                          <DialectIcon dialect={m.sourceType.toLowerCase()} className="w-4 h-4" />
                          <span className="text-xs text-text-tertiary font-mono">&rarr;</span>
                          <DialectIcon dialect={m.targetType.toLowerCase()} className="w-4 h-4" />
                          <span className="text-xs font-mono font-bold text-text-primary bg-bg-sunken border border-border-default px-2 py-0.5 rounded-md uppercase">
                            {m.sourceType} to {m.targetType}
                          </span>
                        </div>
                      </div>

                      {/* Specs detail row */}
                      <div className="flex flex-wrap items-center text-xs text-text-secondary gap-6 font-mono">
                        <div className="flex items-center gap-2 bg-bg-sunken border border-border-default px-3 py-1.5 rounded-md">
                          <Layers className="w-3.5 h-3.5 text-accent" />
                          <span>{m.tables} <span className="text-text-tertiary text-[10px] uppercase font-bold">Tables</span></span>
                        </div>
                        <div className="flex items-center gap-2 bg-bg-sunken border border-border-default px-3 py-1.5 rounded-md">
                          <Database className="w-3.5 h-3.5 text-[#06B6D4]" />
                          <span>{formatRows(m.rows)} <span className="text-text-tertiary text-[10px] uppercase font-bold">Rows</span></span>
                        </div>
                        <div className="flex items-center gap-2 bg-bg-sunken border border-border-default px-3 py-1.5 rounded-md">
                          <Clock className="w-3.5 h-3.5 text-warning" />
                          <span>{m.time?.toFixed(2)}s</span>
                        </div>
                      </div>

                      {/* Chevron action */}
                      <div className="self-end md:self-center">
                        <ChevronRight className="w-5 h-5 text-text-secondary group-hover:text-text-primary group-hover:translate-x-1 transition-all duration-200" />
                      </div>

                    </div>
                  </Link>
                </motion.div>
              ))}
            </AnimatePresence>
          </motion.div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between border-t border-border-default pt-6">
              <span className="text-xs text-text-secondary font-medium">
                Page <span className="text-text-primary font-mono">{currentPage}</span> of <span className="text-text-primary font-mono">{totalPages}</span> ({filteredHistory.length} total items)
              </span>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                  disabled={currentPage === 1}
                  className="px-3.5 py-2 bg-bg-raised border border-border-default rounded-md text-xs font-semibold text-text-secondary hover:text-text-primary disabled:opacity-40 disabled:hover:text-text-secondary disabled:cursor-not-allowed transition-colors"
                >
                  Previous
                </button>
                <button
                  onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                  disabled={currentPage === totalPages}
                  className="px-3.5 py-2 bg-bg-raised border border-border-default rounded-md text-xs font-semibold text-text-secondary hover:text-text-primary disabled:opacity-40 disabled:hover:text-text-secondary disabled:cursor-not-allowed transition-colors"
                >
                  Next
                </button>
              </div>
            </div>
          )}

          {/* Floating Action Bar for Comparing 2 Selected Jobs */}
          <AnimatePresence>
            {selectedJobs.length === 2 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 20 }}
                className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 bg-[#0e0e18] border border-purple-500/40 rounded-2xl px-6 py-3 shadow-[0_0_30px_rgba(168,85,247,0.3)] flex items-center space-x-6 backdrop-blur-xl"
              >
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 rounded-lg bg-purple-500/20 border border-purple-500/40 flex items-center justify-center text-purple-400">
                    <GitCompare className="w-4 h-4" />
                  </div>
                  <span className="font-mono text-xs text-white font-bold">
                    2 Migration Jobs Selected
                  </span>
                </div>

                <div className="flex items-center space-x-3">
                  <button
                    onClick={() => setSelectedJobs([])}
                    className="text-xs font-mono text-gray-400 hover:text-white px-3 py-1.5 rounded-lg border border-white/10 hover:bg-white/5 transition-colors cursor-pointer"
                  >
                    Clear Selection
                  </button>
                  <button
                    onClick={() => navigate(`/app/compare?jobA=${selectedJobs[0]}&jobB=${selectedJobs[1]}`)}
                    className="bg-purple-600 hover:bg-purple-500 text-white font-mono text-xs font-bold px-4 py-2 rounded-xl transition-all shadow-[0_0_15px_rgba(168,85,247,0.4)] flex items-center cursor-pointer"
                  >
                    <GitCompare className="w-3.5 h-3.5 mr-2" />
                    Compare Selected
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}
    </div>
  )
}
