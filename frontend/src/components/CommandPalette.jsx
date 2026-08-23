import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Search, Database, LayoutDashboard, Plus, Activity, Network, 
  History, DollarSign, BookOpen, Cpu, Shield, Sun, Moon, 
  Terminal, ArrowRight, X, Sparkles
} from 'lucide-react'

export default function CommandPalette({ isOpen, onClose, currentTheme, onToggleTheme }) {
  const [query, setQuery] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)
  const navigate = useNavigate()

  const COMMANDS = [
    {
      id: 'dash',
      title: 'Go to Dashboard',
      subtitle: 'View real-time database migration telemetry & active pipelines',
      category: 'Navigation',
      icon: LayoutDashboard,
      action: () => navigate('/app')
    },
    {
      id: 'new-mig',
      title: 'New Migration Wizard',
      subtitle: 'Configure source/target databases and schema discovery',
      category: 'Actions',
      icon: Plus,
      action: () => navigate('/app/new')
    },
    {
      id: 'schema',
      title: 'Schema Visualizer',
      subtitle: 'Explore entity-relationship node graph & column constraints',
      category: 'Tools',
      icon: Network,
      action: () => navigate('/app/schema')
    },
    {
      id: 'analytics',
      title: 'Analytics & Monitoring',
      subtitle: 'Historical throughput benchmarks, CPU/Memory telemetry',
      category: 'Analytics',
      icon: Activity,
      action: () => navigate('/app/analytics')
    },
    {
      id: 'history',
      title: 'Migration History',
      subtitle: 'Review previous migration logs, parity scores, and audit reports',
      category: 'History',
      icon: History,
      action: () => navigate('/app/history')
    },
    {
      id: 'sandbox',
      title: 'Live SQL DDL Sandbox',
      subtitle: 'Instant multi-dialect SQL conversion and DDL risk audit',
      category: 'Tools',
      icon: Cpu,
      action: () => navigate('/sandbox')
    },
    {
      id: 'pricing',
      title: 'View Pricing & ROI Calculator',
      subtitle: 'Explore plans, feature matrix, and estimated cloud savings',
      category: 'Public',
      icon: DollarSign,
      action: () => navigate('/pricing')
    },
    {
      id: 'docs',
      title: 'Documentation Portal',
      subtitle: 'API references, CLI cheatsheet, and deployment guides',
      category: 'Public',
      icon: BookOpen,
      action: () => navigate('/docs')
    },
    {
      id: 'theme',
      title: `Switch Theme to ${currentTheme === 'dark' ? 'Light' : 'Dark'} Mode`,
      subtitle: 'Toggle theme preferences across the application',
      category: 'Preferences',
      icon: currentTheme === 'dark' ? Sun : Moon,
      action: () => {
        if (onToggleTheme) onToggleTheme()
      }
    }
  ]

  const filteredCommands = COMMANDS.filter(cmd => 
    cmd.title.toLowerCase().includes(query.toLowerCase()) ||
    cmd.subtitle.toLowerCase().includes(query.toLowerCase()) ||
    cmd.category.toLowerCase().includes(query.toLowerCase())
  )

  useEffect(() => {
    setSelectedIndex(0)
  }, [query])

  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        if (isOpen) onClose()
        else {
          setQuery('')
          // Parent handles opening
        }
      }
      if (!isOpen) return

      if (e.key === 'Escape') {
        onClose()
      } else if (e.key === 'ArrowDown') {
        e.preventDefault()
        setSelectedIndex(prev => (prev + 1) % (filteredCommands.length || 1))
      } else if (e.key === 'ArrowUp') {
        e.preventDefault()
        setSelectedIndex(prev => (prev - 1 + filteredCommands.length) % (filteredCommands.length || 1))
      } else if (e.key === 'Enter') {
        e.preventDefault()
        if (filteredCommands[selectedIndex]) {
          filteredCommands[selectedIndex].action()
          onClose()
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, selectedIndex, filteredCommands, onClose])

  if (!isOpen) return null

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 px-4 sm:px-6">
        {/* Backdrop */}
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="fixed inset-0 bg-black/70 backdrop-blur-md"
        />

        {/* Modal Window */}
        <motion.div
          initial={{ opacity: 0, scale: 0.96, y: -10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.96, y: -10 }}
          transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
          className="relative w-full max-w-2xl bg-[#09090e] border border-white/15 rounded-2xl shadow-[0_25px_70px_rgba(0,0,0,0.8)] overflow-hidden z-10"
        >
          {/* Header Bar */}
          <div className="flex items-center px-4 border-b border-white/10 bg-white/[0.02]">
            <Search className="w-5 h-5 text-gray-400 mr-3 shrink-0" />
            <input
              type="text"
              autoFocus
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search commands, pages, actions... (e.g. New Migration, Schema, Docs)"
              className="w-full bg-transparent py-4 font-sans text-body text-white placeholder-gray-500 focus:outline-none"
            />
            {query && (
              <button 
                onClick={() => setQuery('')}
                className="p-1 text-gray-400 hover:text-white rounded-md mr-2"
              >
                <X className="w-4 h-4" />
              </button>
            )}
            <kbd className="hidden sm:inline-block px-2 py-0.5 text-xs font-semibold text-gray-400 bg-white/10 rounded border border-white/10">
              ESC
            </kbd>
          </div>

          {/* List */}
          <div className="max-h-[380px] overflow-y-auto p-2 space-y-1 custom-scrollbar">
            {filteredCommands.length === 0 ? (
              <div className="py-12 text-center text-gray-400">
                <Sparkles className="w-8 h-8 text-accent/50 mx-auto mb-2 animate-pulse" />
                <p className="text-sm font-medium">No matching commands found</p>
                <p className="text-xs text-gray-500 mt-1">Try searching for "Dashboard", "Migration", "Docs", or "Theme"</p>
              </div>
            ) : (
              filteredCommands.map((cmd, idx) => {
                const Icon = cmd.icon
                const isSelected = idx === selectedIndex

                return (
                  <button
                    key={cmd.id}
                    onClick={() => {
                      cmd.action()
                      onClose()
                    }}
                    onMouseEnter={() => setSelectedIndex(idx)}
                    className={`
                      w-full flex items-center justify-between p-3 rounded-xl transition-all text-left group
                      ${isSelected 
                        ? 'bg-gradient-to-r from-accent/20 to-blue-500/10 border border-accent/30 text-white shadow-lg' 
                        : 'text-gray-300 hover:bg-white/5 border border-transparent'}
                    `}
                  >
                    <div className="flex items-center space-x-3.5 min-w-0">
                      <div className={`
                        w-9 h-9 rounded-lg flex items-center justify-center shrink-0 transition-colors
                        ${isSelected ? 'bg-accent text-white shadow-[0_0_15px_rgba(139,92,246,0.5)]' : 'bg-white/5 text-gray-400 group-hover:text-white'}
                      `}>
                        <Icon className="w-4 h-4" />
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center space-x-2">
                          <span className="font-sans text-body-sm font-semibold truncate">{cmd.title}</span>
                          <span className="px-2 py-0.5 font-mono text-caption uppercase font-bold text-gray-400 bg-white/5 rounded border border-white/5">
                            {cmd.category}
                          </span>
                        </div>
                        <p className="font-sans text-caption text-gray-400 truncate mt-0.5">{cmd.subtitle}</p>
                      </div>
                    </div>

                    <ArrowRight className={`w-4 h-4 shrink-0 transition-transform ${isSelected ? 'text-accent translate-x-1' : 'text-gray-600 opacity-0 group-hover:opacity-100'}`} />
                  </button>
                )
              })
            )}
          </div>

          {/* Footer Shortcuts */}
          <div className="px-4 py-2.5 bg-white/[0.03] border-t border-white/10 flex items-center justify-between font-sans text-caption text-gray-400">
            <div className="flex items-center space-x-3">
              <span className="flex items-center space-x-1">
                <kbd className="px-1.5 py-0.5 bg-white/10 rounded text-[10px] text-gray-300">↑</kbd>
                <kbd className="px-1.5 py-0.5 bg-white/10 rounded text-[10px] text-gray-300">↓</kbd>
                <span className="ml-1">Navigate</span>
              </span>
              <span className="flex items-center space-x-1">
                <kbd className="px-1.5 py-0.5 bg-white/10 rounded text-[10px] text-gray-300">↵</kbd>
                <span className="ml-1">Select</span>
              </span>
            </div>
            <div className="flex items-center space-x-1.5 text-accent font-medium">
              <Database className="w-3.5 h-3.5" />
              <span>FluxLine AI Command Bar</span>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}
