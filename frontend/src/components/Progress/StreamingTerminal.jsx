import React, { useEffect, useState, useRef, useMemo, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Terminal, Maximize2, Minimize2, Play, Square, Settings2, ArrowDown } from 'lucide-react'
import { useVirtualizer } from '@tanstack/react-virtual'
import { useMigrationStore } from '../../store/useMigrationStore'

const getTagStyle = (level) => {
  switch (level) {
    case 'SUCCESS':
      return 'bg-[#065f46] text-white'
    case 'INFO':
      return 'bg-[#1d4ed8] text-white'
    case 'WARN':
      return 'bg-[#92400e] text-white'
    case 'ERROR':
      return 'bg-[#7f1d1d] text-white'
    default:
      return 'bg-[#374151] text-gray-300'
  }
}

const LogLine = React.memo(function LogLine({ log }) {
  const parsedMsg = useMemo(() => {
    if (!log.msg) return ''
    return log.msg.split(/(['"].+?['"])/g).map((part, i) =>
      /^['"].+?['"]$/.test(part) ? <span key={i} className="text-cyan-400 font-mono">{part}</span> : part
    )
  }, [log.msg])

  return (
    <div className="flex items-baseline space-x-3 hover:bg-white/[0.03] px-2 py-1 rounded-lg transition-colors min-h-[30px]">
      <span className="text-gray-500 font-mono text-[11px] shrink-0 font-medium">{log.timestamp}</span>
      <span
        className={`rounded-md px-2 py-1 text-[10px] font-mono font-bold tracking-wider uppercase shrink-0 ${getTagStyle(
          log.level
        )}`}
      >
        {log.level}
      </span>
      <span className="text-[#f8fafc] text-[13px] break-all font-mono leading-relaxed">
        {parsedMsg}
      </span>
    </div>
  )
})

function StreamingTerminal({ throughputMBs = 467, cpuUsage = 100 }) {
  const logs = useMigrationStore((state) => state.logs)

  const [isPaused, setIsPaused] = useState(false)
  const [isExpanded, setIsExpanded] = useState(false)
  const [isReceiving, setIsReceiving] = useState(false)
  const [isUserScrolledUp, setIsUserScrolledUp] = useState(false)

  const containerRef = useRef(null)
  const receivingTimerRef = useRef(null)

  // React Virtualizer setup for rendering DOM nodes efficiently
  const rowVirtualizer = useVirtualizer({
    count: logs.length,
    getScrollElement: () => containerRef.current,
    estimateSize: () => 34,
    overscan: 8,
  })

  // Track active message receiving status for dot indicator
  useEffect(() => {
    if (logs.length > 0) {
      setIsReceiving(true)
      if (receivingTimerRef.current) clearTimeout(receivingTimerRef.current)
      receivingTimerRef.current = setTimeout(() => {
        setIsReceiving(false)
      }, 3000)
    }
    return () => {
      if (receivingTimerRef.current) clearTimeout(receivingTimerRef.current)
    }
  }, [logs.length])

  // Auto-scroll when new logs arrive if user hasn't scrolled up
  useEffect(() => {
    if (!isPaused && !isUserScrolledUp && logs.length > 0) {
      rowVirtualizer.scrollToIndex(logs.length - 1, { align: 'end' })
    }
  }, [logs.length, isPaused, isUserScrolledUp, rowVirtualizer])

  const handleScroll = useCallback(() => {
    if (!containerRef.current) return
    const { scrollTop, scrollHeight, clientHeight } = containerRef.current
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 40
    setIsUserScrolledUp(!isAtBottom)
  }, [])

  const scrollToBottom = useCallback(() => {
    if (logs.length > 0) {
      rowVirtualizer.scrollToIndex(logs.length - 1, { align: 'end' })
    }
    setIsUserScrolledUp(false)
  }, [logs.length, rowVirtualizer])

  return (
    <div
      className={`bg-[#0a0a0f] border border-white/10 rounded-2xl flex flex-col overflow-hidden transition-all duration-300 ${
        isExpanded ? 'fixed inset-4 z-50 shadow-2xl shadow-accent/20' : 'h-[420px] relative'
      }`}
    >
      {/* Terminal Header */}
      <div className="bg-[#12121a] border-b border-white/10 px-4 py-3 flex items-center justify-between shrink-0">
        <div className="flex items-center space-x-3">
          <Terminal className="w-4 h-4 text-gray-400" />
          <div className="flex items-center space-x-2">
            <span className="relative flex h-2 w-2">
              {isReceiving && (
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              )}
              <span
                className={`relative inline-flex rounded-full h-2 w-2 ${
                  isReceiving ? 'bg-emerald-400' : 'bg-gray-600'
                }`}
              ></span>
            </span>
            <h3 className="font-sans text-[13px] font-semibold tracking-[0.08em] uppercase text-text-tertiary">
              Live Output Console
            </h3>
          </div>

          <div className="hidden sm:flex items-center gap-2 text-caption font-mono text-gray-400 bg-white/[0.04] px-2.5 py-1 rounded-md border border-white/5">
            <span>{logs.length} events</span>
            <span>•</span>
            <span className="text-cyan-400 font-semibold">{throughputMBs} MB/s</span>
            <span>•</span>
            <span className="text-amber-400 font-semibold">{cpuUsage}% CPU</span>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setIsPaused((prev) => !prev)}
            className="p-1.5 hover:bg-white/10 rounded-lg transition-colors text-gray-400 hover:text-white flex items-center space-x-1 cursor-pointer"
            title={isPaused ? 'Resume Stream' : 'Pause Stream'}
          >
            {isPaused ? <Play className="w-3.5 h-3.5 text-emerald-400" /> : <Square className="w-3.5 h-3.5" />}
          </button>
          <button className="p-1.5 hover:bg-white/10 rounded-lg transition-colors text-gray-400 hover:text-white cursor-pointer">
            <Settings2 className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setIsExpanded((prev) => !prev)}
            className="p-1.5 hover:bg-white/10 rounded-lg transition-colors text-gray-400 hover:text-white cursor-pointer"
          >
            {isExpanded ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Virtualized Terminal Body */}
      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-4 font-mono text-xs bg-[#07070b] custom-scrollbar relative"
      >
        {logs.length === 0 ? (
          <div className="text-[#6b7280] italic text-sm py-6 text-center">
            Waiting for live WebSocket messages...
          </div>
        ) : (
          <div
            style={{
              height: `${rowVirtualizer.getTotalSize()}px`,
              width: '100%',
              position: 'relative',
            }}
          >
            {rowVirtualizer.getVirtualItems().map((virtualRow) => {
              const log = logs[virtualRow.index]
              if (!log) return null
              return (
                <div
                  key={virtualRow.key}
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    transform: `translateY(${virtualRow.start}px)`,
                  }}
                >
                  <LogLine log={log} />
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Scroll to bottom button */}
      <AnimatePresence>
        {isUserScrolledUp && (
          <motion.button
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            onClick={scrollToBottom}
            className="absolute bottom-4 right-6 bg-accent hover:bg-accent-hover text-white font-mono text-xs px-3.5 py-2 rounded-xl shadow-xl backdrop-blur border border-white/20 flex items-center space-x-2 z-20 cursor-pointer transition-all"
          >
            <ArrowDown className="w-4 h-4 animate-bounce" />
            <span>Scroll to bottom</span>
          </motion.button>
        )}
      </AnimatePresence>
    </div>
  )
}

export default React.memo(StreamingTerminal)
