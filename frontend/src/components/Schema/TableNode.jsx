import React, { memo } from 'react'
import { Handle, Position } from '@xyflow/react'
import { Database, Key, Link as LinkIcon } from 'lucide-react'

function getDialectColor(dialect) {
  const d = (dialect || '').toUpperCase()
  if (d.includes('POSTGRES')) return '#3b82f6' // Blue
  if (d.includes('MSSQL') || d.includes('SQL SERVER')) return '#f97316' // Orange
  if (d.includes('MYSQL')) return '#14b8a6' // Teal
  if (d.includes('ORACLE')) return '#f59e0b' // Amber
  return '#7c3aed' // Purple
}

const TableNode = memo(({ data, selected }) => {
  const { tableName, dialect, columns = [] } = data
  const topBorderColor = getDialectColor(dialect)

  return (
    <div 
      className={`bg-black/40 backdrop-blur-md border rounded-xl overflow-hidden shadow-2xl transition-all duration-200 min-w-[260px] group ${
        selected 
          ? 'border-accent shadow-[0_0_25px_rgba(124,58,237,0.4)] ring-1 ring-accent/50' 
          : 'border-white/10 hover:border-white/25 hover:-translate-y-1 hover:shadow-[0_0_20px_rgba(124,58,237,0.25)]'
      }`}
      style={{ borderTop: `3px solid ${topBorderColor}` }}
    >
      {/* Target handle on left edge */}
      <Handle 
        type="target" 
        position={Position.Left} 
        className="!w-2 !h-2 !bg-accent !border-none opacity-0" 
      />

      {/* Header */}
      <div className="px-4 py-3 bg-white/[0.03] border-b border-white/10 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Database className="w-4 h-4 text-accent shrink-0" />
          <span className="font-mono text-body-sm font-semibold text-stark-white tracking-wide truncate max-w-[140px]">
            {tableName}
          </span>
        </div>
        <span 
          className="font-mono text-caption px-2 py-0.5 rounded border uppercase text-white/80 bg-white/5 border-white/10 shrink-0"
          style={{ color: topBorderColor, borderColor: `${topBorderColor}40` }}
        >
          {dialect || 'SQL'}
        </span>
      </div>

      {/* Column List */}
      <div className="p-3 space-y-1.5 bg-black/20">
        {columns.map((col, i) => (
          <div 
            key={i} 
            className="flex items-center justify-between gap-4 py-1 px-2 rounded hover:bg-white/5 transition-colors"
          >
            <div className="flex items-center gap-2 min-w-0">
              {col.isPrimary ? (
                <Key className="w-3.5 h-3.5 text-amber-400 shrink-0" title="Primary Key" />
              ) : col.isForeign ? (
                <LinkIcon className="w-3.5 h-3.5 text-accent-solid shrink-0" title="Foreign Key" />
              ) : (
                <span className="w-3.5 h-3.5 inline-block shrink-0" />
              )}
              <span className={`font-mono text-caption truncate ${col.isPrimary ? 'font-semibold text-stark-white' : 'text-white/90'}`}>
                {col.name}
              </span>
            </div>
            <span className="font-mono text-caption text-gray-400 shrink-0">
              {col.type}
            </span>
          </div>
        ))}
      </div>

      {/* Source handle on right edge */}
      <Handle 
        type="source" 
        position={Position.Right} 
        className="!w-2 !h-2 !bg-accent !border-none opacity-0" 
      />
    </div>
  )
})

TableNode.displayName = 'TableNode'
export default TableNode
