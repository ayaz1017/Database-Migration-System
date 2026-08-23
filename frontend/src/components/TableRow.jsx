import React, { memo, useCallback } from 'react'
import { Database, CheckSquare, Square } from 'lucide-react'

const TableRow = memo(function TableRow({ table, selected, onToggle, style }) {
  const handleClick = useCallback(() => onToggle(table.name, !selected), [table.name, selected, onToggle])

  return (
    <div
      style={style}
      onClick={handleClick}
      className={`flex items-center border-b border-border-subtle cursor-pointer transition-colors
        ${selected ? 'bg-accent-solid/5 hover:bg-accent-solid/10' : 'hover:bg-bg-card/40'}`}
    >
      {/* Checkbox */}
      <div className="px-5 py-2.5 w-14 flex items-center justify-center shrink-0">
        {selected ? (
          <CheckSquare className="w-4 h-4 text-accent-solid" />
        ) : (
          <Square className="w-4 h-4 text-muted-slate group-hover:text-stark-white transition-colors" />
        )}
      </div>

      {/* Table name */}
      <div className="flex-1 px-2 py-2.5 flex items-center space-x-2.5 min-w-0">
        <Database className={`w-3.5 h-3.5 shrink-0 ${selected ? 'text-accent-solid' : 'text-muted-slate'} transition-colors`} />
        <span className={`font-mono text-xs font-semibold truncate ${selected ? 'text-stark-white' : 'text-stark-white/70'} transition-colors`}>
          {table.name}
        </span>
      </div>

      {/* Row count */}
      <div className="px-5 py-2.5 text-right shrink-0 w-32">
        <span className={`font-mono text-xs font-bold ${selected ? 'text-status-info' : 'text-muted-slate'}`}>
          {table.row_count.toLocaleString()}
        </span>
      </div>
    </div>
  )
})

export default TableRow
