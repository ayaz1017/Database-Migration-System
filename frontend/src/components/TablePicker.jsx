import { useState, useEffect, useCallback, useMemo, useRef } from 'react'
import apiClient from '../apiClient'
import { Search, AlertCircle, Database, CheckSquare, Square, RefreshCw, Info, Layers } from 'lucide-react'
import { motion } from 'framer-motion'
import { useVirtualizer } from '@tanstack/react-virtual'
import { API_BASE_URL } from '../config'
import TableRow from './TableRow'

// ─── Stagger animation cap ──────────────────────────────────────────────────
// Only the first 15 rows animate with delay; the rest appear instantly to avoid
// massive initial render stalls on schemas with 200+ tables.
const STAGGER_CAP = 15

export default function TablePicker({ sourceConfig, onOptionsChange, options }) {
  const [tables, setTables] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    const fetchTables = async () => {
      setLoading(true)
      setError(null)
      try {
        const res = await apiClient.fetchWithAuth(`${API_BASE_URL}/api/discover/tables`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            db_type: sourceConfig.db_type,
            host: sourceConfig.host,
            port: parseInt(sourceConfig.port) || 0,
            username: sourceConfig.username,
            password: sourceConfig.password,
            database: sourceConfig.database,
          }),
        })

        if (!res.ok) {
          const errData = await res.json()
          throw new Error(errData.detail || 'Failed to fetch tables')
        }

        const data = await res.json()
        setTables(data.tables || [])

        if (options.migrate_all_tables === undefined) {
          onOptionsChange({ ...options, migrate_all_tables: true, selected_tables: [] })
        }
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    if (sourceConfig?.host) fetchTables()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sourceConfig])

  // ── Derived / memoised values ───────────────────────────────────────────
  const filteredTables = useMemo(
    () => tables.filter(t => t.name.toLowerCase().includes(searchTerm.toLowerCase())),
    [tables, searchTerm],
  )

  const isTableSelected = useCallback(
    (name) => options.migrate_all_tables || (options.selected_tables || []).includes(name),
    [options.migrate_all_tables, options.selected_tables],
  )

  const isAllSelected = options.migrate_all_tables || (tables.length > 0 && options.selected_tables?.length === tables.length)
  const isPartiallySelected = !isAllSelected && options.selected_tables?.length > 0

  const totalDBRows = useMemo(() => tables.reduce((sum, t) => sum + t.row_count, 0), [tables])
  const selectedCount = isAllSelected ? tables.length : (options.selected_tables?.length || 0)

  const handleSelectAll = useCallback((checked) => {
    onOptionsChange({ ...options, migrate_all_tables: checked, selected_tables: [] })
  }, [options, onOptionsChange])

  const handleSelectTable = useCallback((tableName, checked) => {
    if (options.migrate_all_tables) {
      const newSelected = tables.map(t => t.name).filter(t => t !== tableName)
      onOptionsChange({ ...options, migrate_all_tables: false, selected_tables: newSelected })
      return
    }

    let newSelected = [...(options.selected_tables || [])]
    if (checked) {
      newSelected.push(tableName)
    } else {
      newSelected = newSelected.filter(t => t !== tableName)
    }

    if (newSelected.length === tables.length) {
      onOptionsChange({ ...options, migrate_all_tables: true, selected_tables: [] })
    } else {
      onOptionsChange({ ...options, migrate_all_tables: false, selected_tables: newSelected })
    }
  }, [options, tables, onOptionsChange])

  // ── Virtual list setup ──────────────────────────────────────────────────
  const parentRef = useRef(null)
  const ROW_HEIGHT = 41 // px — matches py-2.5 + text-xs line

  const rowVirtualizer = useVirtualizer({
    count: filteredTables.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => ROW_HEIGHT,
    overscan: 10,
  })

  // ── Loading / error states ──────────────────────────────────────────────
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-muted-slate space-y-4 bg-bg-panel border border-border-card rounded-2xl animate-pulse shadow-xl w-full">
        <RefreshCw className="w-6 h-6 animate-spin text-accent-solid" />
        <p className="font-mono text-xs tracking-wider uppercase text-status-info">Discovering schema & analyzing dependencies...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6 bg-status-error-muted border border-status-error-border rounded-xl text-status-error flex items-start space-x-3 shadow-md animate-in fade-in duration-300 w-full">
        <AlertCircle className="w-5 h-5 shrink-0 mt-0.5 text-status-error" />
        <div>
          <h3 className="font-bold text-sm font-display tracking-tight text-stark-white">Schema Discovery Failed</h3>
          <p className="text-xs font-mono mt-1 text-status-error">{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col lg:flex-row gap-6 w-full h-[550px] animate-in fade-in zoom-in-95 duration-300">

      {/* Left Pane: Config & Stats */}
      <div className="w-full lg:w-80 flex flex-col gap-4 shrink-0">

        {/* Dependency Resolution */}
        <div className="bg-bg-panel border border-border-card p-5 rounded-2xl shadow-lg space-y-4">
          <label className="block text-[10px] font-mono font-bold text-muted-slate uppercase tracking-wider flex items-center space-x-2">
            <Layers className="w-3.5 h-3.5" />
            <span>Dependency Mode</span>
          </label>
          <div className="space-y-4">
            <select
              value={options.fk_dependency_mode || 'auto_include'}
              onChange={e => onOptionsChange({ ...options, fk_dependency_mode: e.target.value })}
              className="w-full rounded-xl border border-border-subtle bg-[#0A0A0A] text-stark-white px-3 py-2.5 text-xs font-mono focus-ring-violet transition-all outline-none"
            >
              <option value="auto_include">Auto-Include (Safest)</option>
              <option value="strict">Strict (Fail Fast)</option>
              <option value="drop_constraint">Drop Constraint</option>
            </select>
            <div className="flex items-start space-x-2.5 text-[11px] text-muted-slate bg-[#111111] border border-border-card p-3 rounded-xl leading-relaxed">
              <Info className="w-3.5 h-3.5 text-status-info shrink-0 mt-0.5" />
              <p>
                When migrating a subset of tables, determines how missing foreign key parent relationships are handled to prevent structural failures.
              </p>
            </div>
          </div>
        </div>

        {/* Database Stats */}
        <div className="bg-bg-panel border border-border-card p-5 rounded-2xl shadow-lg flex-1 flex flex-col justify-center">
          <div className="space-y-6">
            <div>
              <span className="block text-[10px] font-mono text-muted-slate uppercase tracking-wider mb-1">Discovered Tables</span>
              <div className="text-4xl font-display font-extrabold text-stark-white tracking-tighter">{tables.length}</div>
            </div>
            <div>
              <span className="block text-[10px] font-mono text-muted-slate uppercase tracking-wider mb-1">Estimated Total Rows</span>
              <div className="text-4xl font-display font-extrabold text-status-info tracking-tighter">
                {(totalDBRows / 1_000_000).toFixed(2)}<span className="text-lg opacity-50 ml-1">M</span>
              </div>
            </div>
            {tables.length > 50 && (
              <div className="text-[10px] font-mono text-muted-slate bg-bg-card/60 border border-border-subtle rounded-lg px-3 py-2">
                ⚡ {tables.length} tables — virtual scroll enabled
              </div>
            )}
          </div>
        </div>

      </div>

      {/* Right Pane: Virtualised Data-Grid */}
      <div className="flex-1 bg-bg-panel border border-border-card rounded-2xl shadow-xl flex flex-col overflow-hidden min-h-0">

        {/* Toolbar */}
        <div className="px-5 py-4 border-b border-border-card flex flex-col sm:flex-row sm:items-center justify-between bg-[#111111] gap-4 shrink-0 z-20">
          <motion.button
            whileTap={{ scale: 0.96 }}
            className="flex items-center space-x-3 text-xs font-bold text-stark-white font-mono cursor-pointer bg-bg-card hover:bg-bg-canvas px-3 py-1.5 rounded-lg border border-border-card transition-colors"
            onClick={() => handleSelectAll(!isAllSelected)}
          >
            {isAllSelected ? (
              <CheckSquare className="w-4 h-4 text-accent-solid" />
            ) : isPartiallySelected ? (
              <div className="w-4 h-4 bg-accent-solid rounded-[3px] flex items-center justify-center">
                <div className="w-2.5 h-0.5 bg-white rounded-full" />
              </div>
            ) : (
              <Square className="w-4 h-4 text-muted-slate" />
            )}
            <span>Select All Tables</span>
            <span className="ml-2 bg-bg-panel px-1.5 py-0.5 rounded text-[10px] text-muted-slate border border-border-subtle">
              {selectedCount} / {tables.length}
            </span>
          </motion.button>

          <div className="relative w-full sm:w-64">
            <Search className="w-4 h-4 absolute left-3 top-2 text-muted-slate" />
            <input
              type="text"
              placeholder="Filter by table name..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-[#0A0A0A] border border-border-card rounded-lg text-xs font-mono text-stark-white focus-ring-violet transition-all outline-none"
            />
          </div>
        </div>

        {/* Header row */}
        <div className="flex items-center border-b border-border-card bg-[#0A0A0A] text-muted-slate z-10 shadow-sm shrink-0">
          <div className="px-5 py-3 w-14 text-center" />
          <div className="flex-1 px-2 py-3 text-xs font-bold uppercase tracking-wider font-mono">Table Name</div>
          <div className="px-5 py-3 w-32 text-right text-xs font-bold uppercase tracking-wider font-mono">Row Volume</div>
        </div>

        {/* Virtualised rows */}
        <div
          ref={parentRef}
          className="flex-1 overflow-auto bg-bg-canvas/30 scrollbar-thin scrollbar-thumb-border-card relative z-0"
        >
          {filteredTables.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-muted-slate space-y-3">
              <Search className="w-8 h-8 opacity-20" />
              <div className="text-xs font-mono">No tables found matching &quot;{searchTerm}&quot;</div>
            </div>
          ) : (
            <div style={{ height: rowVirtualizer.getTotalSize(), position: 'relative' }}>
              {rowVirtualizer.getVirtualItems().map((virtualRow) => {
                const table = filteredTables[virtualRow.index]
                const selected = isTableSelected(table.name)
                return (
                  <TableRow
                    key={table.name}
                    table={table}
                    selected={selected}
                    onToggle={handleSelectTable}
                    style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      right: 0,
                      transform: `translateY(${virtualRow.start}px)`,
                      height: `${virtualRow.size}px`,
                    }}
                  />
                )
              })}
            </div>
          )}
        </div>

      </div>
    </div>
  )
}
