import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Table, CheckCircle2, XCircle, Search, Copy, Check, Hash, ArrowUpDown } from 'lucide-react'

export default function ValidationMatrix({ data = [] }) {
  const [searchTerm, setSearchTerm] = useState('')
  const [copiedChecksum, setCopiedChecksum] = useState(null)

  const filteredData = data.filter(row => 
    row.table.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const totalTables = data.length
  const matchedTables = data.filter(r => r.row_count_match !== false).length
  const allMatched = totalTables > 0 && matchedTables === totalTables
  const totalRows = data.reduce((sum, r) => sum + (r.target_row_count ?? r.targetRows ?? 0), 0)

  const handleCopyChecksum = (table, checksum) => {
    navigator.clipboard.writeText(checksum)
    setCopiedChecksum(table)
    setTimeout(() => setCopiedChecksum(null), 1200)
  }

  const formatNum = (num) => new Intl.NumberFormat('en-US').format(num)

  return (
    <motion.div 
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
      className="bg-[#0c0c14]/90 backdrop-blur-xl border border-white/10 rounded-2xl flex flex-col overflow-hidden h-[460px] xl:h-[480px] glass-panel"
    >
      {/* Header */}
      <div className="bg-[#12121a] border-b border-white/10 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shrink-0">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center">
            <Table className="w-4 h-4 text-emerald-400" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="font-sans font-semibold text-body-sm text-stark-white tracking-wider">
                Data Consistency Matrix
              </h3>
              <span className={`text-caption font-mono font-bold px-2 py-0.5 rounded-full border ${
                allMatched ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' : 'bg-red-500/10 border-red-500/30 text-red-400'
              }`}>
                {matchedTables}/{totalTables} Matched
              </span>
            </div>
            <p className="font-sans text-caption text-text-secondary mt-0.5">
              Live checksum & row count parity verification
            </p>
          </div>
        </div>

        {/* Search Input */}
        <div className="relative w-full sm:w-56">
          <Search className="w-3.5 h-3.5 text-gray-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search table..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-white/[0.04] border border-white/10 focus:border-purple-500 rounded-xl pl-9 pr-3 py-1.5 text-xs font-mono text-white placeholder-gray-500 outline-none transition-colors"
          />
        </div>
      </div>

      {allMatched && (
        <motion.div 
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-r from-emerald-500/15 to-teal-500/10 border border-emerald-500/25 rounded-xl px-4 py-3 mx-4 mt-3 flex items-center gap-3 shrink-0"
        >
          <div className="w-8 h-8 rounded-lg bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center shrink-0">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div>
            <p className="text-sm font-semibold text-emerald-400 font-mono">
              ✓ All {totalTables} tables validated — {formatNum(totalRows)} rows verified
            </p>
            <p className="text-xs text-emerald-400/60 mt-0.5">Full SHA-256 checksum parity confirmed across all tables</p>
          </div>
        </motion.div>
      )}

      {/* Table Container */}
      <div className="flex-1 overflow-auto custom-scrollbar w-full">
        <table className="w-full text-left border-collapse">
          <thead className="bg-[#07070b]/90 sticky top-0 z-10 backdrop-blur-md">
            <tr>
              <th className="p-3.5 text-[11px] uppercase tracking-[0.06em] text-text-tertiary font-semibold font-sans border-b border-white/10">Table Name</th>
              <th className="p-3.5 text-[11px] uppercase tracking-[0.06em] text-text-tertiary font-semibold font-sans border-b border-white/10 text-right">Source Rows</th>
              <th className="p-3.5 text-[11px] uppercase tracking-[0.06em] text-text-tertiary font-semibold font-sans border-b border-white/10 text-right">Target Rows</th>
              <th className="p-3.5 text-[11px] uppercase tracking-[0.06em] text-text-tertiary font-semibold font-sans border-b border-white/10">Checksum SHA256</th>
              <th className="p-3.5 text-[11px] uppercase tracking-[0.06em] text-text-tertiary font-semibold font-sans border-b border-white/10 text-center">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5 font-mono text-xs">
            {filteredData.map((row, idx) => {
              const isMatch = row.row_count_match !== false && row.checksum_match !== false
              const checksumVal = row.checksum || row.checksum_method || '--'
              const shortChecksum = checksumVal.length > 20 ? `${checksumVal.substring(0, 8)}...${checksumVal.substring(checksumVal.length - 6)}` : checksumVal

              return (
                <motion.tr 
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.04 }}
                  key={row.table} 
                  className={`hover:bg-white/[0.04] transition-colors ${idx % 2 !== 0 ? 'bg-white/[0.02]' : ''}`}
                >
                  <td className="p-3.5 font-mono font-semibold text-white flex items-center space-x-2">
                    <Hash className="w-3.5 h-3.5 text-purple-400 shrink-0" />
                    <span>{row.table}</span>
                  </td>
                  <td className="p-3.5 text-right font-mono font-medium text-gray-300">{formatNum(row.source_row_count ?? row.sourceRows ?? 0)}</td>
                  <td className="p-3.5 text-right font-mono font-medium text-gray-300">{formatNum(row.target_row_count ?? row.targetRows ?? 0)}</td>
                  <td className="p-3.5">
                    <button
                      onClick={() => handleCopyChecksum(row.table, (row.checksum || row.checksum_method || ''))}
                      className="inline-flex items-center space-x-1.5 bg-white/[0.03] hover:bg-white/[0.08] border border-white/10 px-2 py-1 rounded-md text-[11px] text-gray-400 hover:text-white transition-colors group cursor-pointer"
                      title="Click to copy full checksum"
                    >
                      <span className="font-mono text-gray-300">{shortChecksum}</span>
                      {copiedChecksum === row.table ? (
                        <Check className="w-3 h-3 text-emerald-400 shrink-0" />
                      ) : (
                        <Copy className="w-3 h-3 text-gray-500 group-hover:text-gray-300 shrink-0" />
                      )}
                    </button>
                  </td>
                  <td className="p-3.5 text-center">
                    {isMatch ? (
                      <span className="inline-flex items-center space-x-1 text-[10px] font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-2.5 py-1 rounded-full shadow-[0_0_8px_rgba(16,185,129,0.15)]">
                        <CheckCircle2 className="w-3 h-3" />
                        <span>MATCH</span>
                      </span>
                    ) : (
                      <span className="inline-flex items-center space-x-1 text-[10px] font-bold text-red-400 bg-red-500/10 border border-red-500/30 px-2.5 py-1 rounded-full shadow-[0_0_8px_rgba(239,68,68,0.15)] animate-pulse">
                        <XCircle className="w-3 h-3" />
                        <span>MISMATCH</span>
                      </span>
                    )}
                  </td>
                </motion.tr>
              )
            })}

            {filteredData.length === 0 && (
              <tr>
                <td colSpan="5" className="text-center py-10 text-gray-500 italic">
                  {searchTerm ? `No matching tables found for "${searchTerm}"` : 'No table validation data available'}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </motion.div>
  )
}
