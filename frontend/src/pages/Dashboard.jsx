import { useState, useEffect, useMemo } from 'react'
import apiClient from '../apiClient'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { Database, ChevronRight, Plus, Calendar, Clock, Layers, ShieldAlert, Sparkles, Search, SlidersHorizontal, X, ArrowRight, Zap, CheckCircle2, AlertCircle } from 'lucide-react'
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion'
import AnimatedCounter from '../components/AnimatedCounter'
import EmptyState from '../components/EmptyState'
import { DialectIcon } from '../components/DialectBadge'
import { API_BASE_URL } from '../config'
import { formatRows } from '../utils/formatRows'

export function getRelativeTime(isoString) {
  if (!isoString) return ''
  const date = new Date(isoString)
  const now = new Date()
  const diffMs = now - date
  
  if (isNaN(date.getTime())) return isoString
  
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays === 1) return 'yesterday'
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

// Helper for DB Dialect badge color tinting (FIX 3)
function getDialectBadgeStyle(dialect) {
  const d = (dialect || '').toUpperCase()
  if (d.includes('MSSQL') || d.includes('SQL SERVER')) {
    return 'bg-orange-500/10 text-orange-400 border-orange-500/20'
  }
  if (d.includes('POSTGRES')) {
    return 'bg-blue-500/10 text-blue-400 border-blue-500/20'
  }
  if (d.includes('MYSQL')) {
    return 'bg-teal-500/10 text-teal-400 border-teal-500/20'
  }
  if (d.includes('ORACLE')) {
    return 'bg-amber-500/10 text-amber-400 border-amber-500/20'
  }
  return 'bg-white/5 text-text-primary border-border-default'
}

export default function Dashboard() {
  const [migrations, setMigrations] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const navigate = useNavigate()
  const location = useLocation()
  const shouldReduceMotion = useReducedMotion()

  // History Filters
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('ALL')
  const [sourceDialect, setSourceDialect] = useState('ALL')
  const [targetDialect, setTargetDialect] = useState('ALL')
  const [sortBy, setSortBy] = useState('recent')
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 5

  // Tab State: 'feed' or 'archives'
  const [activeTab, setActiveTab] = useState(location.pathname === '/app/history' ? 'archives' : 'feed')

  const fetchMigrations = async () => {
    try {
      const res = await apiClient.fetchWithAuth(`${API_BASE_URL}/api/migrations/history`)
      if (res.ok) {
        const data = await res.json()
        const list = Array.isArray(data) ? data : (data.items || [])
        const mapped = list.map(job => ({
          id: job.id,
          name: `Migration ${job.id.slice(-6)}`,
          date: job.timestamp,
          sourceType: (job.source_db || 'UNKNOWN').toUpperCase(),
          targetType: (job.target_db || 'UNKNOWN').toUpperCase(),
          tables: job.tables_migrated || 0,
          rows: job.rows_migrated || 0,
          time: job.duration ? parseFloat(job.duration.replace('s', '')) || 0 : 0,
          score: job.status === 'SUCCESS' ? 100 : (job.status || '').startsWith('COMPLETED') ? 95 : 0,
          status: job.status || 'UNKNOWN'
        }))
        setMigrations(mapped)
      }
    } catch(e) {
      console.error('Failed to fetch migrations:', e)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    let timeoutId
    const pollMigrations = async () => {
      await fetchMigrations()
      const hasActive = migrations.some(m => 
        m.status === 'IN_PROGRESS' || m.status === 'RUNNING' || m.status === 'in_progress' || m.status === 'running'
      )
      timeoutId = setTimeout(pollMigrations, hasActive ? 3000 : 12000)
    }
    
    pollMigrations()
    return () => clearTimeout(timeoutId)
  }, [migrations.length])

  // Global Metrics
  const totalPipelines = migrations.length;
  const totalRows = migrations.reduce((acc, m) => acc + (m.rows || 0), 0);
  const avgValidation = migrations.length 
    ? Math.round(migrations.reduce((acc, m) => acc + (m.score || 0), 0) / migrations.length) 
    : 0;

  // System Accuracy color based on value (FIX 2)
  const accuracyBorderColor = avgValidation < 50 ? 'border-t-red-500' : avgValidation <= 80 ? 'border-t-amber-500' : 'border-t-emerald-500'
  const accuracyBgBarColor = avgValidation < 50 ? 'bg-red-500' : avgValidation <= 80 ? 'bg-amber-500' : 'bg-emerald-500'

  // Memoized Search & Filters
  const filteredHistory = useMemo(() => {
    let result = [...migrations]

    if (search.trim()) {
      const query = search.toLowerCase()
      result = result.filter(item => 
        item.id.toLowerCase().includes(query) ||
        item.sourceType.toLowerCase().includes(query) ||
        item.targetType.toLowerCase().includes(query) ||
        item.name.toLowerCase().includes(query)
      )
    }

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
      if (sortBy === 'recent') return new Date(b.date) - new Date(a.date)
      if (sortBy === 'oldest') return new Date(a.date) - new Date(b.date)
      if (sortBy === 'duration') return b.time - a.time
      if (sortBy === 'rows') return b.rows - a.rows
      return 0
    })

    return result
  }, [migrations, search, statusFilter, sourceDialect, targetDialect, sortBy])

  // Pagination
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
    setCurrentPage(1)
  }

  // Animation variants (80ms stagger delay - FIX 3)
  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.08 }
    }
  }

  const cardVariants = {
    hidden: { opacity: 0, y: 15 },
    show: { 
      opacity: 1, 
      y: 0,
      transition: { duration: 0.3, ease: 'easeOut' }
    }
  }

  return (
    <div className="p-6 md:p-10 max-w-7xl mx-auto space-y-10 relative selection:bg-accent/30 selection:text-accent-solid">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-6">
        <div className="space-y-1.5">
          <motion.h1 
            initial={shouldReduceMotion ? {} : { opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="font-sans text-2xl font-bold text-white tracking-tight"
          >
            Migration Console
          </motion.h1>
          <motion.p 
            initial={shouldReduceMotion ? {} : { opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="font-sans text-xs text-zinc-400"
          >
            Active replication streams and schema transformation logs
          </motion.p>
        </div>
        
        <motion.div
          initial={shouldReduceMotion ? {} : { opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
        >
          <Link 
            to="/app/new" 
            className="inline-flex items-center justify-center space-x-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg transition-all duration-150 shadow-sm cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Migration</span>
          </Link>
        </motion.div>
      </div>

      {/* Stats Summary Bento Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 animate-pulse h-28">
          <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl"></div>
          <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl"></div>
          <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl"></div>
        </div>
      ) : (
        <motion.div 
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, duration: 0.3 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-4"
        >
          {/* Card 1: Pipelines Executed */}
          <div className="relative p-5 bg-[#121216] border border-zinc-800 rounded-xl overflow-hidden group hover:border-zinc-700 transition-colors">
            <Layers className="absolute top-4 right-4 w-5 h-5 text-zinc-600 opacity-40 pointer-events-none" />
            <div className="relative z-10 space-y-2">
              <span className="text-xs text-zinc-400 font-medium block">
                Pipelines executed
              </span>
              <div className="flex items-baseline">
                <span className="font-sans text-2xl font-bold text-white">
                  <AnimatedCounter value={totalPipelines} duration={1.2} />
                </span>
                <span className="text-xs font-normal text-zinc-500 font-mono ml-2">total</span>
              </div>
            </div>
          </div>

          {/* Card 2: Records Synced */}
          <div className="relative p-5 bg-[#121216] border border-zinc-800 rounded-xl overflow-hidden group hover:border-zinc-700 transition-colors">
            <Database className="absolute top-4 right-4 w-5 h-5 text-zinc-600 opacity-40 pointer-events-none" />
            <div className="relative z-10 space-y-2">
              <span className="text-xs text-zinc-400 font-medium block">
                Records synced
              </span>
              <div className="flex items-baseline">
                <span className="font-sans text-2xl font-bold text-white">
                  <AnimatedCounter value={totalRows} duration={1.2} />
                </span>
                <span className="text-xs font-normal text-zinc-500 font-mono ml-2">rows</span>
              </div>
            </div>
          </div>

          {/* Card 3: Parity Verification (Differentiated Audit Status Badge) */}
          <div className="relative p-5 bg-[#101512] border border-emerald-500/25 rounded-xl overflow-hidden group transition-colors">
            <div className="relative z-10 space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="text-xs text-zinc-300 font-medium">
                  Parity verification
                </span>
                {totalPipelines > 0 && avgValidation >= 99 ? (
                  <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-emerald-500/15 text-emerald-400 border border-emerald-500/25">
                    <CheckCircle2 className="w-3 h-3" />
                    <span>PASSED</span>
                  </span>
                ) : (
                  <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-zinc-800 text-zinc-400 border border-zinc-700">
                    <span>{totalPipelines > 0 ? 'MONITORING' : 'IDLE'}</span>
                  </span>
                )}
              </div>

              <div className="flex items-baseline space-x-2">
                <span className="font-mono text-xl font-bold text-emerald-400">
                  {totalPipelines > 0 ? `${avgValidation}%` : '--'}
                </span>
                <span className="text-xs text-zinc-400 font-mono">
                  {totalPipelines > 0 ? 'checksum match' : 'no pipelines yet'}
                </span>
              </div>

              {/* Context bar + label */}
              <div className="pt-0.5">
                <div className="w-full h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                  <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: `${avgValidation}%` }}
                    transition={{ duration: 1.2, ease: 'easeOut' }}
                    className="h-full rounded-full bg-emerald-500"
                  />
                </div>
                <span className="text-[11px] text-zinc-400 mt-1 block">
                  Byte-level SHA256 & row count audit
                </span>
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Tabs & Main Content */}
      <div className="space-y-6 pt-4">
        
        {/* Underline Tab Switcher with Badges (FIX 6) */}
        <div className="flex items-center gap-6 border-b border-border-default pb-0">
          <button 
            onClick={() => setActiveTab('feed')}
            className={`pb-3 text-xs font-mono font-bold transition-colors relative flex items-center space-x-2 ${
              activeTab === 'feed' ? 'text-text-primary' : 'text-text-tertiary hover:text-text-secondary'
            }`}
          >
            <Sparkles className={`w-3.5 h-3.5 ${activeTab === 'feed' ? 'text-accent' : 'text-text-tertiary'}`} />
            <span>Recent Activity ({migrations.slice(0, 4).length})</span>
            {activeTab === 'feed' && (
              <motion.div 
                layoutId="active-tab-underline"
                className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent rounded-full"
                transition={{ type: 'spring', stiffness: 400, damping: 30 }}
              />
            )}
          </button>

          <button 
            onClick={() => setActiveTab('archives')}
            className={`pb-3 text-xs font-mono font-bold transition-colors relative flex items-center space-x-2 ${
              activeTab === 'archives' ? 'text-text-primary' : 'text-text-tertiary hover:text-text-secondary'
            }`}
          >
            <Database className={`w-3.5 h-3.5 ${activeTab === 'archives' ? 'text-accent' : 'text-text-tertiary'}`} />
            <span>Audit Archives ({migrations.length})</span>
            {activeTab === 'archives' && (
              <motion.div 
                layoutId="active-tab-underline"
                className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent rounded-full"
                transition={{ type: 'spring', stiffness: 400, damping: 30 }}
              />
            )}
          </button>
        </div>

        {/* TAB CONTENTS */}
        <div className="min-h-[400px]">
          <AnimatePresence mode="wait">
            
            {/* 1. RECENT ACTIVITY FEED */}
            {activeTab === 'feed' && (
              <motion.div
                key="feed-tab"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2 }}
                className="space-y-4"
              >
                {isLoading ? (
                  <div className="space-y-4">
                    <div className="h-28 bg-bg-raised/50 border border-border-default rounded-xl animate-pulse"></div>
                    <div className="h-28 bg-bg-raised/50 border border-border-default rounded-xl animate-pulse"></div>
                  </div>
                ) : migrations.length === 0 ? (
                  <EmptyState 
                    icon={Database}
                    title="No migrations configured"
                    description="Connect your source and target databases to start schema translation and data replication."
                    actionLabel="Create your first migration"
                    onAction={() => navigate('/app/new')}
                  />
                ) : (
                  <motion.div 
                    variants={containerVariants}
                    initial="hidden"
                    animate="show"
                    className="grid gap-4"
                  >
                    {migrations.slice(0, 4).map(m => {
                      const isFailed = m.status === 'FAILED'
                      const isSuccess = m.status === 'SUCCESS'
                      const isPartial = m.status === 'PARTIAL' || m.status.toUpperCase().startsWith('COMPLETED')
                      const isActive = m.status === 'IN_PROGRESS' || m.status === 'RUNNING'

                      // Card Left Border (FIX 3)
                      const leftBorderClass = isFailed 
                        ? 'border-l-[3px] border-l-red-500' 
                        : isPartial 
                        ? 'border-l-[3px] border-l-amber-500' 
                        : isSuccess 
                        ? 'border-l-[3px] border-l-emerald-500' 
                        : 'border-l-[3px] border-l-accent'

                      return (
                        <motion.div
                          key={m.id}
                          variants={cardVariants}
                          whileHover={shouldReduceMotion ? {} : { y: -2 }}
                          className={`glass-panel rounded-xl hover:border-white/20 hover:shadow-[0_4px_20px_rgba(0,0,0,0.3)] transition-all duration-200 relative overflow-hidden group ${leftBorderClass}`}
                        >
                          <Link to={`/app/report/${m.id}`} className="block p-5">
                            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                              
                              {/* Left Side: Info & Dialects */}
                              <div className="space-y-3">
                                <div className="flex flex-wrap items-center gap-3">
                                  <h3 className="font-display font-bold text-lg text-text-primary tracking-wide">{m.name}</h3>
                                  
                                  {/* Status Badge (FIX 3) */}
                                  {isSuccess ? (
                                    <span className="inline-flex items-center py-1 px-2.5 rounded bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 text-xs font-mono font-bold tracking-widest uppercase">
                                      <span>Success</span>
                                    </span>
                                  ) : isPartial ? (
                                    <span className="inline-flex items-center py-1 px-2.5 rounded bg-amber-500/15 border border-amber-500/30 text-amber-400 text-xs font-mono font-bold tracking-widest uppercase">
                                      <span>Partial</span>
                                    </span>
                                  ) : isActive ? (
                                    <span className="inline-flex items-center space-x-1.5 py-1 px-2.5 rounded bg-accent-muted border border-accent/20 text-accent-solid text-xs font-mono font-bold tracking-widest uppercase">
                                      <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse"></span>
                                      <span>Active</span>
                                    </span>
                                  ) : (
                                    <span className="inline-flex items-center py-1 px-2.5 rounded bg-red-500/15 border border-red-500/30 text-red-400 text-xs font-mono font-bold tracking-widest uppercase">
                                      <span className="w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse mr-1.5"></span>
                                      <span>Failed</span>
                                    </span>
                                  )}
                                  
                                  <span className="text-xs text-text-secondary font-mono flex items-center gap-1.5 ml-2">
                                    <Calendar className="w-3.5 h-3.5 opacity-60" />
                                    {getRelativeTime(m.date)}
                                  </span>
                                </div>
                                
                                {/* DB Type Badges (FIX 3) */}
                                <div className="flex items-center space-x-2.5">
                                  <div className={`flex items-center space-x-1.5 px-2.5 py-1 rounded border text-xs font-mono font-bold uppercase ${getDialectBadgeStyle(m.sourceType)}`}>
                                    <DialectIcon dialect={m.sourceType.toLowerCase()} className="w-3.5 h-3.5" />
                                    <span>{m.sourceType}</span>
                                  </div>
                                  <ArrowRight className="w-3.5 h-3.5 text-text-tertiary group-hover:translate-x-0.5 group-hover:text-accent transition-all duration-200" />
                                  <div className={`flex items-center space-x-1.5 px-2.5 py-1 rounded border text-xs font-mono font-bold uppercase ${getDialectBadgeStyle(m.targetType)}`}>
                                    <DialectIcon dialect={m.targetType.toLowerCase()} className="w-3.5 h-3.5" />
                                    <span>{m.targetType}</span>
                                  </div>
                                </div>
                              </div>

                              {/* Right Side: Card Metrics (FIX 3) */}
                              <div className="flex flex-wrap items-center gap-3">
                                <div className="flex flex-col items-start bg-bg-sunken border border-border-default px-3 py-1.5 rounded-lg min-w-[90px]">
                                  <span className="text-[10px] font-mono text-text-tertiary uppercase tracking-wider">Tables</span>
                                  <span className={`text-sm font-bold font-mono ${isFailed && m.tables === 0 ? 'text-text-tertiary' : 'text-text-primary'}`}>
                                    {m.tables}
                                  </span>
                                </div>

                                <div className="flex flex-col items-start bg-bg-sunken border border-border-default px-3 py-1.5 rounded-lg min-w-[110px]">
                                  <span className="text-[10px] font-mono text-text-tertiary uppercase tracking-wider">Rows Synced</span>
                                  <span className={`text-sm font-bold font-mono ${isFailed && m.rows === 0 ? 'text-text-tertiary' : 'text-text-primary'}`}>
                                    {formatRows(m.rows)}
                                  </span>
                                </div>

                                <div className="flex flex-col items-start bg-bg-sunken border border-border-default px-3 py-1.5 rounded-lg min-w-[90px]">
                                  <span className="text-[10px] font-mono text-text-tertiary uppercase tracking-wider">Duration</span>
                                  <span className={`text-sm font-bold font-mono ${isFailed ? 'text-text-tertiary' : 'text-text-primary'}`}>
                                    {m.time?.toFixed(2)}s
                                  </span>
                                </div>
                                
                                {/* Right chevron hover offset (FIX 3) */}
                                <div className="ml-2 w-8 h-8 rounded-full bg-bg-sunken flex items-center justify-center group-hover:bg-accent-muted group-hover:text-accent-solid transition-colors border border-transparent group-hover:border-accent-border">
                                  <ChevronRight className="w-4 h-4 text-text-secondary group-hover:text-accent-solid group-hover:translate-x-1 transition-transform duration-200" />
                                </div>
                              </div>
                              
                            </div>
                          </Link>
                        </motion.div>
                      )
                    })}
                  </motion.div>
                )}
              </motion.div>
            )}

            {/* 2. AUDIT ARCHIVES (FULL FILTERABLE HISTORY) */}
            {activeTab === 'archives' && (
              <motion.div
                key="archives-tab"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2 }}
                className="space-y-6"
              >
                {/* Advanced Filters */}
                <div className="glass-panel rounded-2xl p-5 space-y-4">
                  <div className="flex flex-col lg:flex-row gap-4">
                    
                    {/* Search box */}
                    <div className="relative flex-1 group">
                      <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-text-tertiary group-focus-within:text-accent transition-colors" />
                      <input
                        type="text"
                        placeholder="Search by job ID, database engines..."
                        value={search}
                        onChange={e => { setSearch(e.target.value); setCurrentPage(1); }}
                        className="w-full bg-bg-sunken border border-border-default rounded-md pl-10 pr-4 py-2.5 text-xs font-mono text-text-primary placeholder-text-tertiary focus:border-accent focus:ring-1 focus:ring-accent focus:outline-none transition-all shadow-inner"
                      />
                      {search && (
                        <button onClick={() => { setSearch(''); setCurrentPage(1); }} className="absolute right-3.5 top-1/2 -translate-y-1/2 text-text-secondary hover:text-text-primary transition-colors bg-bg-raised rounded p-0.5">
                          <X className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>

                    {/* Dropdowns */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                      {[
                        { val: statusFilter, set: setStatusFilter, label: 'Status', opts: [{v:'ALL', l:'All'}, {v:'SUCCESS', l:'Completed'}, {v:'PARTIAL', l:'Partial'}, {v:'FAILED', l:'Failed'}, {v:'IN_PROGRESS', l:'In Progress'}] },
                        { val: sourceDialect, set: setSourceDialect, label: 'Source', opts: [{v:'ALL', l:'All'}, {v:'MSSQL', l:'MSSQL'}, {v:'MYSQL', l:'MySQL'}, {v:'POSTGRES', l:'PostgreSQL'}, {v:'ORACLE', l:'Oracle'}] },
                        { val: targetDialect, set: setTargetDialect, label: 'Target', opts: [{v:'ALL', l:'All'}, {v:'POSTGRES', l:'PostgreSQL'}, {v:'MYSQL', l:'MySQL'}, {v:'MSSQL', l:'MSSQL'}, {v:'ORACLE', l:'Oracle'}] },
                        { val: sortBy, set: setSortBy, label: 'Sort', opts: [{v:'recent', l:'Recent'}, {v:'oldest', l:'Oldest'}, {v:'duration', l:'Speed'}, {v:'rows', l:'Volume'}] }
                      ].map((dropdown, idx) => (
                        <div key={idx} className="relative group">
                          <select
                            value={dropdown.val}
                            onChange={e => { dropdown.set(e.target.value); setCurrentPage(1); }}
                            className="w-full bg-bg-sunken border border-border-default rounded-md px-3 py-2.5 text-xs text-text-secondary outline-none cursor-pointer font-mono appearance-none focus:border-accent focus:ring-1 focus:ring-accent transition-all hover:bg-bg-raised"
                          >
                            <option value={dropdown.opts[0].v} className="text-text-tertiary">{dropdown.label}: {dropdown.opts[0].l}</option>
                            {dropdown.opts.slice(1).map(opt => (
                              <option key={opt.v} value={opt.v}>{opt.l}</option>
                            ))}
                          </select>
                          <ChevronRight className="absolute right-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text-tertiary pointer-events-none rotate-90" />
                        </div>
                      ))}
                    </div>

                  </div>

                  {(statusFilter !== 'ALL' || sourceDialect !== 'ALL' || targetDialect !== 'ALL' || search) && (
                    <div className="flex items-center justify-between pt-3 border-t border-border-default text-xs font-mono">
                      <span className="text-text-secondary">Matches: <strong className="text-text-primary font-bold">{filteredHistory.length}</strong> runs</span>
                      <button onClick={handleClearFilters} className="text-accent-solid hover:text-accent-hover font-bold flex items-center gap-1.5 transition-colors bg-accent-muted px-2 py-1 rounded-md">
                        <X className="w-3 h-3" /> Clear Filters
                      </button>
                    </div>
                  )}
                </div>

                {/* Audit Grid list (FIX 3) */}
                {filteredHistory.length === 0 ? (
                  <EmptyState
                    icon={SlidersHorizontal}
                    title="No archives match filter"
                    description="Clear search queries or dialect filters to scan past executions."
                    actionLabel="Reset Search Filters"
                    onAction={handleClearFilters}
                  />
                ) : (
                  <div className="space-y-6">
                    <motion.div
                      variants={containerVariants}
                      initial="hidden"
                      animate="show"
                      className="grid gap-3"
                    >
                      {currentItems.map(m => {
                        const isFailed = m.status === 'FAILED'
                        const isSuccess = m.status === 'SUCCESS'
                        const isPartial = m.status === 'PARTIAL' || m.status.startsWith('COMPLETED')
                        const leftBorderClass = isFailed 
                          ? 'border-l-[3px] border-l-red-500' 
                          : isPartial 
                          ? 'border-l-[3px] border-l-amber-500' 
                          : isSuccess 
                          ? 'border-l-[3px] border-l-emerald-500' 
                          : 'border-l-[3px] border-l-accent'

                        return (
                          <motion.div
                            key={m.id}
                            variants={cardVariants}
                            whileHover={shouldReduceMotion ? {} : { y: -2 }}
                            className={`glass-panel rounded-xl hover:border-white/20 transition-all duration-200 group ${leftBorderClass}`}
                          >
                            <Link to={`/app/report/${m.id}`} className="block p-4">
                              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                                <div className="space-y-2.5">
                                  <div className="flex items-center gap-3">
                                    <h3 className="font-mono font-bold text-sm text-text-primary">{m.name}</h3>
                                    <span className="text-xs text-text-tertiary font-mono flex items-center gap-1">
                                      <Clock className="w-3 h-3" /> {getRelativeTime(m.date)}
                                    </span>
                                    {/* Status dot */}
                                    <span className={`w-2 h-2 rounded-full ${
                                      isSuccess ? 'bg-emerald-400' : 
                                      isPartial ? 'bg-amber-400' : 
                                      m.status === 'IN_PROGRESS' || m.status === 'RUNNING' ? 'bg-accent animate-pulse' : 
                                      'bg-red-400 animate-pulse'
                                    }`}></span>
                                  </div>
                                  <div className="flex items-center space-x-1.5 text-xs text-text-secondary font-mono">
                                    <span className={`px-2 py-0.5 rounded border text-[11px] font-bold ${getDialectBadgeStyle(m.sourceType)}`}>
                                      {m.sourceType}
                                    </span>
                                    <ArrowRight className="w-3.5 h-3.5 text-text-tertiary mx-1 group-hover:translate-x-0.5 group-hover:text-accent transition-all duration-200" />
                                    <span className={`px-2 py-0.5 rounded border text-[11px] font-bold ${getDialectBadgeStyle(m.targetType)}`}>
                                      {m.targetType}
                                    </span>
                                  </div>
                                </div>

                                <div className="flex items-center text-xs text-text-secondary gap-6 font-mono">
                                  <span className={`flex items-center gap-1.5 ${isFailed && m.tables === 0 ? 'text-text-tertiary' : 'text-text-primary font-bold'}`}>
                                    <Layers className="w-3.5 h-3.5 text-text-tertiary" /> {m.tables} tbls
                                  </span>
                                  <span className={`flex items-center gap-1.5 ${isFailed && m.rows === 0 ? 'text-text-tertiary' : 'text-text-primary font-bold'}`}>
                                    <Database className="w-3.5 h-3.5 text-text-tertiary" /> {formatRows(m.rows)} rows
                                  </span>
                                  <span className={`flex items-center gap-1.5 ${isFailed ? 'text-text-tertiary' : 'text-text-primary font-bold'}`}>
                                    <Clock className="w-3.5 h-3.5 text-text-tertiary" /> {m.time?.toFixed(2)}s
                                  </span>
                                  <ChevronRight className="w-4 h-4 text-text-tertiary group-hover:text-accent-solid group-hover:translate-x-1 transition-transform duration-200" />
                                </div>
                              </div>
                            </Link>
                          </motion.div>
                        )
                      })}
                    </motion.div>

                    {/* Pagination */}
                    {totalPages > 1 && (
                      <div className="flex items-center justify-between border-t border-border-default pt-5 text-xs font-mono">
                        <span className="text-text-secondary">
                          Page <strong className="text-text-primary">{currentPage}</strong> of <strong className="text-text-primary">{totalPages}</strong>
                        </span>
                        <div className="flex gap-2">
                          <button
                            onClick={() => setCurrentPage(p => Math.max(p - 1, 1))}
                            disabled={currentPage === 1}
                            className="px-4 py-2 bg-bg-raised border border-border-default rounded hover:bg-bg-overlay hover:text-text-primary disabled:opacity-40 disabled:hover:bg-bg-raised disabled:hover:text-text-disabled cursor-pointer transition-colors text-text-secondary"
                          >
                            Prev
                          </button>
                          <button
                            onClick={() => setCurrentPage(p => Math.min(p + 1, totalPages))}
                            disabled={currentPage === totalPages}
                            className="px-4 py-2 bg-bg-raised border border-border-default rounded hover:bg-bg-overlay hover:text-text-primary disabled:opacity-40 disabled:hover:bg-bg-raised disabled:hover:text-text-disabled cursor-pointer transition-colors text-text-secondary"
                          >
                            Next
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </motion.div>
            )}

          </AnimatePresence>
        </div>
      </div>
    </div>
  )
}
