import React, { useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { CheckCircle2, Loader2, AlertCircle, Clock, AlertTriangle } from 'lucide-react'
import { useMigrationStore } from '../../store/useMigrationStore'

const formatNumber = (num) =>
  new Intl.NumberFormat('en-US', { notation: 'compact', compactDisplay: 'short' }).format(Math.floor(num || 0))

const getStatusIcon = (status) => {
  switch (status) {
    case 'completed':
      return <CheckCircle2 className="w-4 h-4 text-emerald-400" />
    case 'running':
      return <Loader2 className="w-4 h-4 text-accent animate-spin" />
    case 'failed':
      return <AlertCircle className="w-4 h-4 text-red-400" />
    case 'skipped':
      return <AlertTriangle className="w-4 h-4 text-orange-400" />
    case 'pending':
    default:
      return <Clock className="w-4 h-4 text-amber-400" />
  }
}

const getStatusBadge = (status) => {
  switch (status) {
    case 'completed':
      return <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded text-caption font-mono uppercase">Done</span>
    case 'running':
      return <span className="bg-accent/10 text-accent border border-accent/20 px-2 py-0.5 rounded text-caption font-mono uppercase animate-pulse">Migrating</span>
    case 'failed':
      return <span className="bg-red-500/10 text-red-400 border border-red-500/20 px-2 py-0.5 rounded text-caption font-mono uppercase">Failed</span>
    case 'skipped':
      return <span className="bg-orange-500/10 text-orange-400 border border-orange-500/20 px-2 py-0.5 rounded text-caption font-mono uppercase">Skipped</span>
    case 'pending':
    default:
      return <span className="bg-amber-500/10 text-amber-400 border border-amber-500/20 px-2 py-0.5 rounded text-caption font-mono uppercase">Queued</span>
  }
}

const getTypeBadge = (objectType) => {
  if (!objectType || objectType === 'table') return null
  const typeMap = {
    view: { bg: 'bg-blue-500/10', text: 'text-blue-400', border: 'border-blue-500/20', label: 'VIEW' },
    procedure: { bg: 'bg-purple-500/10', text: 'text-purple-400', border: 'border-purple-500/20', label: 'PROC' },
    trigger: { bg: 'bg-pink-500/10', text: 'text-pink-400', border: 'border-pink-500/20', label: 'TRIG' }
  }
  const conf = typeMap[objectType] || { bg: 'bg-gray-500/10', text: 'text-gray-400', border: 'border-gray-500/20', label: objectType.toUpperCase() }
  return <span className={`ml-2 px-1.5 py-0.5 rounded text-[10px] font-mono border ${conf.bg} ${conf.text} ${conf.border}`}>{conf.label}</span>
}

const getBarColor = (status) => {
  switch (status) {
    case 'completed': return 'bg-emerald-500'
    case 'running': return 'bg-accent'
    case 'failed': return 'bg-red-500'
    case 'skipped': return 'bg-orange-500/30'
    case 'pending':
    default: return 'bg-amber-500/30'
  }
}

const getBorderColor = (status) => {
  switch (status) {
    case 'completed': return 'border-emerald-500/20'
    case 'running': return 'border-accent/30'
    case 'failed': return 'border-red-500/20'
    case 'skipped': return 'border-orange-500/20'
    case 'pending':
    default: return 'border-amber-500/10'
  }
}

const TableProgressRow = React.memo(function TableProgressRow({ table }) {
  const percent = useMemo(() => {
    return table.rows_total > 0 ? (table.rows_done / table.rows_total) * 100 : 0
  }, [table.rows_done, table.rows_total])

  return (
    <div className={`bg-white/[0.02] border p-3 rounded-xl ${getBorderColor(table.status)}`}>
      <div className="flex justify-between items-center mb-2">
        <div className="flex items-center space-x-2">
          {getStatusIcon(table.status)}
          <div className="flex items-center">
            <span className="font-mono font-semibold text-white">{table.name}</span>
            {getTypeBadge(table.object_type)}
          </div>
          {getStatusBadge(table.status)}
        </div>
        <div className="font-mono text-caption text-gray-300">
          {table.rows_total > 0 ? (
            <>
              {formatNumber(table.rows_done)} / {formatNumber(table.rows_total)}
              <span className="ml-2 text-gray-500">({percent.toFixed(1)}%)</span>
            </>
          ) : (
            <span className="text-amber-400/70 text-caption font-mono uppercase">Queued</span>
          )}
        </div>
      </div>

      <div className="w-full h-1.5 bg-black/50 rounded-full overflow-hidden flex">
        <div
          style={{ width: `${percent}%`, transition: 'width 0.3s ease-out' }}
          className={`h-full ${getBarColor(table.status)}`}
        />
      </div>
    </div>
  )
})

function TableProgressGrid({ tables }) {
  const storeTablesDict = useMigrationStore((state) => state.tables)

  const tableList = useMemo(() => {
    if (tables && Array.isArray(tables)) return tables
    return Object.values(storeTablesDict)
  }, [tables, storeTablesDict])

  const sortedTables = useMemo(() => {
    const statusOrder = { running: 0, pending: 1, skipped: 2, completed: 3, failed: 4 }
    return [...tableList].sort((a, b) => (statusOrder[a.status] ?? 4) - (statusOrder[b.status] ?? 4))
  }, [tableList])

  return (
    <div className="bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl flex flex-col h-[400px]">
      <div className="p-4 border-b border-white/10 flex items-center justify-between shrink-0">
        <div>
          <h3 className="font-sans font-semibold text-body-sm text-stark-white uppercase tracking-wider">Table Worker Progress</h3>
          <p className="text-xs font-mono text-gray-500 mt-1">Live data ingestion by worker node</p>
        </div>
        <div className="flex space-x-3 text-[10px] font-mono text-gray-400">
          <span className="flex items-center"><CheckCircle2 className="w-3 h-3 text-emerald-400 mr-1" /> Completed</span>
          <span className="flex items-center"><Loader2 className="w-3 h-3 text-accent mr-1 animate-spin" /> Running</span>
          <span className="flex items-center"><Clock className="w-3 h-3 text-amber-400 mr-1" /> Queued</span>
          <span className="flex items-center"><AlertTriangle className="w-3 h-3 text-orange-400 mr-1" /> Skipped</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
        {sortedTables.length === 0 ? (
          <div className="text-gray-500 font-mono text-sm italic text-center py-8">
            Waiting for table discovery...
          </div>
        ) : (
          sortedTables.map((table) => (
            <TableProgressRow key={table.name} table={table} />
          ))
        )}
      </div>
    </div>
  )
}

export default React.memo(TableProgressGrid)
