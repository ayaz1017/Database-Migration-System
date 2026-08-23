import React, { useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import { FileCode2, Copy, Check, Filter } from 'lucide-react'

const KNOWN_COERCIONS = [
  {
    sourcePattern: /SERIAL/i,
    targetPattern: /BIGINT\s+AUTO_INCREMENT/i,
    label: 'PostgreSQL SERIAL maps to MySQL BIGINT AUTO_INCREMENT',
    severity: 'lossless', // 🟢
  },
  {
    sourcePattern: /TIMESTAMP\s+WITH\s+TIME\s+ZONE/i,
    targetPattern: /TIMESTAMP/i,
    label: 'Timezone info removed — MySQL TIMESTAMP is UTC-normalized',
    severity: 'check', // 🟡
  },
  {
    sourcePattern: /JSONB/i,
    targetPattern: /JSON(?!B)/i,
    label: 'JSONB binary storage → MySQL JSON text type',
    severity: 'lossless', // 🟢
  },
]

export default function SqlDiffViewer({ 
  sourceSql = '', 
  targetSql = '', 
  sourceDialect = 'PostgreSQL 15', 
  targetDialect = 'MySQL 8.0' 
}) {
  const [copiedSource, setCopiedSource] = useState(false)
  const [copiedTarget, setCopiedTarget] = useState(false)
  const [filter, setFilter] = useState('All') // All, Coercions Only, Issues Only

  const handleCopy = (text, setCopied) => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const { diffLines, summary } = useMemo(() => {
    const sLines = sourceSql.split('\n')
    const tLines = targetSql.split('\n')
    
    const lines = []
    let losslessCount = 0
    let checkCount = 0
    let issuesCount = 0

    const maxLen = Math.max(sLines.length, tLines.length)
    
    for (let i = 0; i < maxLen; i++) {
      const sLine = sLines[i]
      const tLine = tLines[i]
      
      const sLineStr = sLine !== undefined ? sLine : ''
      const tLineStr = tLine !== undefined ? tLine : ''
      
      if (sLineStr === tLineStr) {
        if (sLine !== undefined) {
          lines.push({ type: 'unchanged', sLine: sLineStr, tLine: tLineStr, sLineNum: i + 1, tLineNum: i + 1 })
        }
      } else {
        let matchedCoercion = null
        for (const coercion of KNOWN_COERCIONS) {
          if (
            sLineStr && tLineStr &&
            coercion.sourcePattern.test(sLineStr) && 
            coercion.targetPattern.test(tLineStr)
          ) {
            matchedCoercion = coercion
            break
          }
        }

        if (matchedCoercion) {
          if (matchedCoercion.severity === 'lossless') losslessCount++
          else if (matchedCoercion.severity === 'check') checkCount++
          
          lines.push({ 
            type: 'coercion', 
            sLine: sLineStr, 
            tLine: tLineStr, 
            sLineNum: i + 1, 
            tLineNum: i + 1,
            coercion: matchedCoercion
          })
        } else {
          issuesCount++
          if (sLine !== undefined) {
            lines.push({ type: 'removed', sLine: sLineStr, tLine: null, sLineNum: i + 1, tLineNum: null })
          }
          if (tLine !== undefined) {
            lines.push({ type: 'added', sLine: null, tLine: tLineStr, sLineNum: null, tLineNum: i + 1 })
          }
        }
      }
    }

    return { diffLines: lines, summary: { losslessCount, checkCount, issuesCount } }
  }, [sourceSql, targetSql])

  const filteredLines = useMemo(() => {
    if (filter === 'All') return diffLines
    if (filter === 'Coercions Only') return diffLines.filter(l => l.type === 'coercion')
    if (filter === 'Issues Only') return diffLines.filter(l => l.type === 'added' || l.type === 'removed')
    return diffLines
  }, [diffLines, filter])

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col bg-[#0c0c14]/90 backdrop-blur-xl border border-white/10 rounded-2xl h-[460px] xl:h-[480px] overflow-hidden"
    >
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center p-4 border-b border-white/10 shrink-0 gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-purple-500/20 rounded-lg">
            <FileCode2 className="w-5 h-5 text-purple-400" />
          </div>
          <h2 className="text-sm font-semibold text-white/90">DDL Schema Equivalence Diff</h2>
        </div>

        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 bg-white/5 rounded-full px-3 py-1 border border-white/10">
            <span className="text-xs font-medium text-blue-400">{sourceDialect}</span>
            <button
              onClick={() => handleCopy(sourceSql, setCopiedSource)}
              className="p-1 hover:bg-white/10 rounded-md transition-colors"
            >
              {copiedSource ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3 text-white/40" />}
            </button>
          </div>
          <div className="text-white/20">→</div>
          <div className="flex items-center space-x-2 bg-white/5 rounded-full px-3 py-1 border border-white/10">
            <span className="text-xs font-medium text-emerald-400">{targetDialect}</span>
            <button
              onClick={() => handleCopy(targetSql, setCopiedTarget)}
              className="p-1 hover:bg-white/10 rounded-md transition-colors"
            >
              {copiedTarget ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3 text-white/40" />}
            </button>
          </div>
        </div>
      </div>

      <div className="px-4 py-3 border-b border-white/10 shrink-0 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 bg-black/20">
        <div className="flex items-center text-xs font-medium">
          <span className="text-white/50 mr-3">Summary:</span>
          {summary.losslessCount > 0 && <span className="text-emerald-400 mr-3">{summary.losslessCount} lossless</span>}
          {summary.checkCount > 0 && <span className="text-amber-400 mr-3">{summary.checkCount} to review</span>}
          {summary.issuesCount > 0 && <span className="text-red-400 mr-3">{summary.issuesCount} issues</span>}
          {summary.losslessCount === 0 && summary.checkCount === 0 && summary.issuesCount === 0 && (
             <span className="text-white/50">No differences</span>
          )}
        </div>

        <div className="flex items-center space-x-2 bg-white/5 p-1 rounded-lg border border-white/10">
          <Filter className="w-3 h-3 text-white/40 ml-2" />
          <button 
            onClick={() => setFilter('All')}
            className={`px-3 py-1 text-xs rounded-md transition-colors ${filter === 'All' ? 'bg-white/10 text-white' : 'text-white/50 hover:text-white/80'}`}
          >
            All
          </button>
          <button 
            onClick={() => setFilter('Coercions Only')}
            className={`px-3 py-1 text-xs rounded-md transition-colors ${filter === 'Coercions Only' ? 'bg-amber-500/20 text-amber-300' : 'text-white/50 hover:text-white/80'}`}
          >
            Coercions Only
          </button>
          <button 
            onClick={() => setFilter('Issues Only')}
            className={`px-3 py-1 text-xs rounded-md transition-colors ${filter === 'Issues Only' ? 'bg-red-500/20 text-red-300' : 'text-white/50 hover:text-white/80'}`}
          >
            Issues Only
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto bg-[#0a0a0f] font-mono text-sm py-2">
        {filteredLines.map((line, idx) => {
          if (line.type === 'unchanged') {
            return (
              <div key={idx} className="flex hover:bg-white/5 px-2">
                <div className="w-12 text-right pr-4 text-white/20 select-none">{line.sLineNum}</div>
                <div className="flex-1 text-white/70 whitespace-pre">{line.sLine}</div>
              </div>
            )
          }

          if (line.type === 'coercion') {
            const icon = line.coercion.severity === 'lossless' ? '🟢' : '🟡'
            const severityLabel = line.coercion.severity === 'lossless' ? 'LOSSLESS' : 'CHECK'
            return (
              <div key={idx} className="flex flex-col bg-amber-500/10 border-l-2 border-amber-500 my-1 py-1">
                <div className="flex px-2">
                  <div className="w-12 text-right pr-4 text-amber-500/40 select-none">{line.sLineNum}</div>
                  <div className="flex-1 text-red-300 whitespace-pre line-through opacity-80">{line.sLine}</div>
                </div>
                <div className="flex px-2">
                  <div className="w-12 text-right pr-4 text-amber-500/40 select-none">{line.tLineNum}</div>
                  <div className="flex-1 text-emerald-300 whitespace-pre">{line.tLine}</div>
                </div>
                <div className="flex px-2 mt-1 pb-1">
                  <div className="w-12 text-right pr-4 text-amber-500/40 select-none"></div>
                  <div className="flex-1 text-xs font-mono text-amber-400">
                    [COERCION] {icon} {severityLabel} — {line.coercion.label}
                  </div>
                </div>
              </div>
            )
          }

          if (line.type === 'removed') {
            return (
              <div key={idx} className="flex bg-red-500/10 border-l-2 border-red-500 px-2 my-px">
                <div className="w-12 text-right pr-4 text-red-500/40 select-none">{line.sLineNum}</div>
                <div className="flex-1 text-red-300 whitespace-pre">{line.sLine}</div>
              </div>
            )
          }

          if (line.type === 'added') {
            return (
              <div key={idx} className="flex bg-emerald-500/10 border-l-2 border-emerald-500 px-2 my-px">
                <div className="w-12 text-right pr-4 text-emerald-500/40 select-none">{line.tLineNum}</div>
                <div className="flex-1 text-emerald-300 whitespace-pre">{line.tLine}</div>
              </div>
            )
          }

          return null
        })}
        {filteredLines.length === 0 && (
          <div className="text-center text-white/40 py-10 text-sm">
            No lines matching the current filter.
          </div>
        )}
      </div>
    </motion.div>
  )
}
