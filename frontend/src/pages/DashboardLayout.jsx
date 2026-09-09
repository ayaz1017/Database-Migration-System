import React, { useState, useEffect, lazy, Suspense } from 'react'
import apiClient from '../apiClient'
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { Database, LayoutDashboard, Plus, ShieldAlert, RefreshCw, Activity, PlayCircle, Sun, Moon, Menu, X, Terminal, Network, LogOut, Settings, Users, Search, Calendar, Webhook, ShieldCheck, GitCompare } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion'
import { API_BASE_URL } from '../config'
import Demo from './Demo'
import CommandPalette from '../components/CommandPalette'
const AssistantChat = lazy(() => import('../components/AssistantChat'))

export default function DashboardLayout() {
  const [health, setHealth] = useState({ status: 'checking', msg: '' })
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('fluxline-theme')
    if (saved) return saved
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    return systemPrefersDark ? 'dark' : 'light'
  })
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [activeJob, setActiveJob] = useState(null)
  const [demoOpen, setDemoOpen] = useState(false)
  const [profileOpen, setProfileOpen] = useState(false)
  const [cmdPaletteOpen, setCmdPaletteOpen] = useState(false)
  
  const { user, logout } = useAuth()
  
  const location = useLocation()
  const navigate = useNavigate()
  const shouldReduceMotion = useReducedMotion()

  // Close mobile drawer on route transition
  useEffect(() => {
    setMobileMenuOpen(false)
  }, [location.pathname])

  useEffect(() => {
    const root = document.documentElement
    root.setAttribute('data-theme', theme)
    localStorage.setItem('fluxline-theme', theme)
  }, [theme])

  // System Health Check
  useEffect(() => {
    Promise.all([
      apiClient.fetchWithAuth(`${API_BASE_URL}/health`).then(r => r.json()).catch(() => null),
      apiClient.fetchWithAuth(`${API_BASE_URL}/api/health/llm`).then(r => r.json()).catch(() => null)
    ])
    .then(([healthData, llmData]) => {
      if (!healthData) {
        setHealth({ status: 'error', msg: 'Cannot connect to backend (port 8000).' })
        return
      }
      
      let msgParts = []
      let status = 'ok'
      
      if (!healthData.mssql_driver || !healthData.pgloader_available) {
        status = 'warning'
        msgParts.push('Missing MSSQL driver or pgloader.')
      }
      
      if (!llmData || !llmData.llm_available) {
        status = 'warning'
        const rawErr = llmData?.error || 'Unknown network error'
        const lowerErr = rawErr.toLowerCase()
        if (lowerErr.includes('not found')) {
          msgParts.push(`Ollama model ${llmData?.model || 'llama3.1:8b'} not installed. Run 'ollama run ${llmData?.model || 'llama3.1:8b'}'`)
        } else if (lowerErr.includes('connection refused') || lowerErr.includes('connect')) {
          msgParts.push(`Ollama service is not running on port 11434.`)
        } else {
          const shortErr = rawErr.length > 120 ? rawErr.slice(0, 120) + '…' : rawErr
          msgParts.push(`Ollama LLM unavailable: ${shortErr}`)
        }
      }
      
      if (status === 'warning') {
        setHealth({ status: 'warning', msg: 'Degraded: ' + msgParts.join(' ') })
      } else {
        setHealth({ status: 'ok', msg: '' })
      }
    })
  }, [])

  // Poll for active migration job
  useEffect(() => {
    let intervalId
    const checkActiveJob = async () => {
      try {
        const res = await apiClient.fetchWithAuth(`${API_BASE_URL}/api/migrations/history`)
        if (res.ok) {
          const data = await res.json()
          const list = Array.isArray(data) ? data : (data.items || [])
          const active = list.find(job => 
            job.status === 'IN_PROGRESS' || job.status === 'RUNNING' || job.status === 'in_progress' || job.status === 'running'
          )
          if (active) {
            setActiveJob({
              id: active.id,
              status: active.status,
              tables: active.tables_migrated || 0,
              rows: active.rows_migrated || 0,
              timestamp: active.timestamp
            })
          } else {
            setActiveJob(null)
          }
        }
      } catch (e) {
        console.error('Active job check failed:', e)
      }
    }
    
    checkActiveJob()
    intervalId = setInterval(checkActiveJob, 4000)
    return () => clearInterval(intervalId)
  }, [])

  const navItems = [
    { to: '/app', icon: LayoutDashboard, label: 'Dashboard', tooltip: 'Dashboard', end: true },
    { to: '/app/analytics', icon: Activity, label: 'Analytics', tooltip: 'Analytics' },
    { to: '/app/schema', icon: Network, label: 'Schema', tooltip: 'Schema' },
    { to: '/app/schedules', icon: Calendar, label: 'Schedules', tooltip: 'Schedules' },
    { to: '/app/webhooks', icon: Webhook, label: 'Webhooks', tooltip: 'Webhooks' },
    { to: '/app/masking', icon: ShieldCheck, label: 'Data Masking', tooltip: 'Data Masking' },
    { to: '/app/compare', icon: GitCompare, label: 'Compare Jobs', tooltip: 'Compare Jobs' },
    { to: '/app/new', icon: Plus, label: 'New Migration', tooltip: 'New Migration' },
    { onClick: () => setDemoOpen(true), icon: PlayCircle, label: 'Monitor', tooltip: 'How It Works' }
  ]

  return (
    <div className="flex h-screen w-screen bg-bg-canvas text-stark-white overflow-hidden font-sans">
      
      {/* 1. Left Navigation Dock - Desktop (Hidden on mobile) */}
      <aside className="hidden md:flex flex-col w-20 shrink-0 border-r border-border-card glass-panel items-center py-6 justify-between z-50">
        
        {/* Logo */}
        <Link to="/" className="flex flex-col items-center group mb-8 relative" aria-label="Fluxline Home">
          <motion.div 
            whileHover={shouldReduceMotion ? {} : { rotate: 10, scale: 1.05 }}
            className="flex items-center justify-center w-10 h-10 rounded-xl border border-accent-border/40 bg-accent-muted text-accent-solid shadow-[0_0_15px_rgba(139,92,246,0.15)] group-hover:border-accent-solid transition-colors"
          >
            <Database className="w-5 h-5 text-accent-solid" />
          </motion.div>
          <span className="font-sans text-h4 font-bold tracking-widest text-muted-slate group-hover:text-stark-white mt-2 transition-colors uppercase">FLUX</span>
          {/* Tooltip */}
          <div className="absolute left-full ml-3 px-2.5 py-1 bg-bg-panel border border-border-card text-stark-white text-xs font-mono rounded-md whitespace-nowrap shadow-xl opacity-0 group-hover:opacity-100 transition-opacity duration-150 pointer-events-none z-50">
            Fluxline Home
          </div>
        </Link>

        {/* Navigation Links with Tooltips (FIX 4) */}
        <nav className="flex flex-col space-y-4 flex-1 w-full px-2" role="navigation" aria-label="Main Navigation">
          {navItems.map((item) => {
            if (item.to) {
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.end}
                  className={({ isActive }) =>
                    `relative flex flex-col items-center justify-center w-full py-3.5 rounded-xl transition-all group ${
                      isActive ? 'text-stark-white' : 'text-muted-slate hover:text-stark-white'
                    }`
                  }
                >
                  {({ isActive }) => (
                    <>
                      {isActive && (
                        <motion.div
                          layoutId="dock-active-pill"
                          className="absolute inset-0 bg-accent-muted border border-accent-border/30 rounded-xl -z-10 mx-1.5"
                          transition={{ type: 'spring', stiffness: 350, damping: 28 }}
                        />
                      )}
                      <item.icon className={`w-5 h-5 transition-colors duration-150 ${isActive ? 'text-accent-solid' : 'text-muted-slate group-hover:text-stark-white'}`} />
                      {/* Sidebar hover tooltip */}
                      <div className="absolute left-full ml-3 px-2.5 py-1 bg-bg-panel border border-border-card text-stark-white text-xs font-mono rounded-md whitespace-nowrap shadow-xl opacity-0 group-hover:opacity-100 transition-opacity duration-150 pointer-events-none z-50">
                        {item.tooltip}
                      </div>
                    </>
                  )}
                </NavLink>
              )
            } else {
              return (
                <button
                  key={item.label}
                  onClick={item.onClick}
                  className="relative flex flex-col items-center justify-center w-full py-3.5 rounded-xl transition-all group text-muted-slate hover:text-stark-white cursor-pointer"
                >
                  {demoOpen && (
                    <motion.div
                      layoutId="dock-active-pill"
                      className="absolute inset-0 bg-accent-muted border border-accent-border/30 rounded-xl -z-10 mx-1.5"
                      transition={{ type: 'spring', stiffness: 350, damping: 28 }}
                    />
                  )}
                  <item.icon className={`w-5 h-5 transition-colors duration-150 ${demoOpen ? 'text-accent-solid' : 'text-muted-slate group-hover:text-stark-white'}`} />
                  {/* Sidebar hover tooltip */}
                  <div className="absolute left-full ml-3 px-2.5 py-1 bg-bg-panel border border-border-card text-stark-white text-xs font-mono rounded-md whitespace-nowrap shadow-xl opacity-0 group-hover:opacity-100 transition-opacity duration-150 pointer-events-none z-50">
                    {item.tooltip}
                  </div>
                </button>
              )
            }
          })}
          
          {/* Active Job Quick Link */}
          {activeJob && (
            <NavLink
              to={`/app/progress/${activeJob.id}`}
              className={({ isActive }) =>
                `relative flex flex-col items-center justify-center w-full py-3.5 rounded-xl transition-all group ${
                  isActive ? 'text-status-info' : 'text-muted-slate hover:text-status-info'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <motion.div
                      layoutId="dock-active-pill"
                      className="absolute inset-0 bg-status-info-muted border border-status-info-border/30 rounded-xl -z-10 mx-1.5"
                      transition={{ type: 'spring', stiffness: 350, damping: 28 }}
                    />
                  )}
                  <div className="relative">
                    <Terminal className={`w-5 h-5 transition-colors duration-150 ${isActive ? 'text-status-info' : 'text-muted-slate group-hover:text-status-info'}`} />
                    <span className="absolute -top-1.5 -right-1.5 w-2.5 h-2.5 bg-status-info border-2 border-bg-panel rounded-full animate-ping"></span>
                    <span className="absolute -top-1.5 -right-1.5 w-2.5 h-2.5 bg-status-info border-2 border-bg-panel rounded-full"></span>
                  </div>
                  {/* Tooltip */}
                  <div className="absolute left-full ml-3 px-2.5 py-1 bg-bg-panel border border-border-card text-stark-white text-xs font-mono rounded-md whitespace-nowrap shadow-xl opacity-0 group-hover:opacity-100 transition-opacity duration-150 pointer-events-none z-50">
                    Monitor
                  </div>
                </>
              )}
            </NavLink>
          )}
        </nav>

        {/* Dock Footer Settings with Tooltips (FIX 4) */}
        <div className="flex flex-col items-center space-y-4 w-full px-2">
          
          {/* Light/Dark Toggle */}
          <div className="relative group">
            <button
              onClick={() => setTheme(prev => prev === 'dark' ? 'light' : 'dark')}
              className="w-10 h-10 rounded-xl bg-bg-card hover:bg-bg-popover border border-border-card text-muted-slate hover:text-stark-white transition-all cursor-pointer flex items-center justify-center shadow-sm"
              aria-label="Toggle theme mode"
            >
              {theme === 'dark' ? <Moon className="w-4 h-4 text-accent-solid" /> : <Sun className="w-4 h-4 text-amber-400" />}
            </button>
            <div className="absolute left-full ml-3 px-2.5 py-1 bg-bg-panel border border-border-card text-stark-white text-xs font-mono rounded-md whitespace-nowrap shadow-xl opacity-0 group-hover:opacity-100 transition-opacity duration-150 pointer-events-none z-50">
              Toggle Theme
            </div>
          </div>

          {/* Health Indicator */}
          <div className="relative group">
            <div 
              className="flex items-center justify-center w-10 h-10 rounded-xl bg-bg-card border border-border-card cursor-help relative" 
              role="status"
              aria-live="polite"
            >
              {health.status === 'checking' && (
                <RefreshCw className="w-4 h-4 text-accent-solid animate-spin" />
              )}
              {health.status !== 'checking' && (
                <span className={`w-3 h-3 rounded-full ${
                  health.status === 'ok' 
                    ? 'bg-status-success shadow-[0_0_10px_rgba(16,185,129,0.5)]' 
                    : health.status === 'warning' 
                    ? 'bg-status-warning shadow-[0_0_10px_rgba(245,158,11,0.5)] animate-pulse' 
                    : 'bg-status-error shadow-[0_0_10px_rgba(244,63,94,0.5)] animate-ping'
                }`}></span>
              )}
            </div>
            <div className="absolute left-full ml-3 px-2.5 py-1 bg-bg-panel border border-border-card text-stark-white text-xs font-mono rounded-md whitespace-nowrap shadow-xl opacity-0 group-hover:opacity-100 transition-opacity duration-150 pointer-events-none z-50">
              System Status
            </div>
          </div>

          {/* Profile / Account */}
          <div className="relative group">
            <button
              onClick={() => setProfileOpen(!profileOpen)}
              className="w-10 h-10 rounded-xl bg-bg-card hover:bg-bg-popover border border-border-card transition-all flex items-center justify-center shadow-sm text-stark-white font-medium"
            >
              {user?.email?.charAt(0).toUpperCase() || 'U'}
            </button>
            <div className="absolute left-full ml-3 px-2.5 py-1 bg-bg-panel border border-border-card text-stark-white text-xs font-mono rounded-md whitespace-nowrap shadow-xl opacity-0 group-hover:opacity-100 transition-opacity duration-150 pointer-events-none z-50">
              Account ({user?.email?.slice(0, 8) || 'User'}...)
            </div>

            <AnimatePresence>
              {profileOpen && (
                <motion.div
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -10 }}
                  className="absolute left-14 bottom-0 w-48 bg-bg-panel border border-border-card rounded-xl shadow-2xl overflow-hidden z-50 py-1"
                >
                  <div className="px-3 py-2 border-b border-white/5 mb-1">
                    <p className="text-sm font-medium text-white truncate">{user?.email}</p>
                    <p className="text-xs text-gray-500">{user?.role}</p>
                  </div>
                  {user?.role === 'Admin' && (
                    <Link to="/app/settings/users" onClick={() => setProfileOpen(false)} className="flex items-center px-3 py-2 text-sm text-gray-300 hover:text-white hover:bg-white/5 transition-colors">
                      <Users className="w-4 h-4 mr-2 text-blue-400" />
                      Manage Users
                    </Link>
                  )}
                  <Link to="/app/settings/password" onClick={() => setProfileOpen(false)} className="flex items-center px-3 py-2 text-sm text-gray-300 hover:text-white hover:bg-white/5 transition-colors">
                    <Settings className="w-4 h-4 mr-2 text-gray-400" />
                    Password
                  </Link>
                  <button onClick={logout} className="w-full flex items-center px-3 py-2 text-sm text-red-400 hover:text-red-300 hover:bg-red-400/10 transition-colors">
                    <LogOut className="w-4 h-4 mr-2" />
                    Sign out
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

        </div>
      </aside>

      {/* 2. Mobile Header - (Hidden on desktop) */}
      <div className="md:hidden flex flex-col w-full h-full">
        <header className="h-14 shrink-0 border-b border-border-subtle bg-bg-panel/85 backdrop-blur-xl flex items-center justify-between px-6 z-50">
          <Link to="/" className="flex items-center space-x-3" aria-label="Fluxline Home">
            <Database className="w-5 h-5 text-accent-solid" />
            <span className="font-display font-bold text-base tracking-tight text-stark-white">Fluxline</span>
          </Link>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => setTheme(prev => prev === 'dark' ? 'light' : 'dark')}
              className="p-2 rounded-lg bg-bg-card border border-border-card text-muted-slate"
              aria-label="Toggle theme mode"
            >
              {theme === 'dark' ? <Moon className="w-4 h-4 text-accent-solid" /> : <Sun className="w-4 h-4 text-amber-400" />}
            </button>

            <button
              onClick={() => setMobileMenuOpen(prev => !prev)}
              className="p-2 rounded-lg bg-bg-card border border-border-card text-muted-slate"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
            </button>
          </div>
        </header>

        {/* Mobile Menu Drawer */}
        <AnimatePresence>
          {mobileMenuOpen && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 top-14 bg-black/60 backdrop-blur-sm z-40"
              onClick={() => setMobileMenuOpen(false)}
            >
              <motion.div
                initial={{ x: '100%' }}
                animate={{ x: 0 }}
                exit={{ x: '100%' }}
                transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                className="absolute right-0 top-0 bottom-0 w-72 bg-bg-panel border-l border-border-card p-6 flex flex-col space-y-6 shadow-2xl"
                onClick={e => e.stopPropagation()}
              >
                <span className="font-sans text-caption text-muted-slate uppercase tracking-wider">Console Menu</span>
                <nav className="flex flex-col space-y-2">
                  {navItems.map((item) => {
                    if (item.to) {
                      return (
                        <NavLink
                          key={item.to}
                          to={item.to}
                          end={item.end}
                          className={({ isActive }) =>
                            `flex items-center px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                              isActive ? 'bg-accent-muted text-stark-white border border-accent-border/30' : 'text-muted-slate hover:text-stark-white hover:bg-bg-card'
                            }`
                          }
                        >
                          <item.icon className="w-4 h-4 mr-3 text-accent-solid" />
                          <span>{item.label}</span>
                        </NavLink>
                      )
                    } else {
                      return (
                        <button
                          key={item.label}
                          onClick={() => {
                            setMobileMenuOpen(false)
                            item.onClick()
                          }}
                          className="flex items-center w-full text-left px-4 py-3 rounded-xl text-sm font-medium transition-all text-muted-slate hover:text-stark-white hover:bg-bg-card cursor-pointer"
                        >
                          <item.icon className="w-4 h-4 mr-3 text-accent-solid" />
                          <span>{item.label}</span>
                        </button>
                      )
                    }
                  })}
                  
                  {activeJob && (
                    <NavLink
                      to={`/app/progress/${activeJob.id}`}
                      className={({ isActive }) =>
                        `flex items-center px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                          isActive ? 'bg-status-info-muted text-status-info border border-status-info-border/30' : 'text-status-info hover:bg-bg-card'
                        }`
                      }
                    >
                      <Terminal className="w-4 h-4 mr-3 text-status-info animate-pulse" />
                      <span>Active Monitor</span>
                    </NavLink>
                  )}
                </nav>

                <div className="mt-auto border-t border-border-card pt-6 flex flex-col space-y-4">
                  <div className="flex items-center justify-between px-2">
                    <div className="flex items-center space-x-3">
                       <div className="w-8 h-8 rounded-full bg-blue-500/10 flex items-center justify-center border border-blue-500/20 text-blue-400 font-bold">
                         {user?.email?.charAt(0).toUpperCase()}
                       </div>
                       <div>
                         <p className="text-sm font-medium text-white truncate max-w-[150px]">{user?.email}</p>
                         <p className="text-xs text-gray-500">{user?.role}</p>
                       </div>
                    </div>
                  </div>
                  
                  <button
                    onClick={logout}
                    className="flex items-center justify-center px-4 py-2.5 rounded-xl text-sm font-medium bg-red-500/10 border border-red-500/20 text-red-400 hover:text-red-300 hover:bg-red-500/20 transition-all"
                  >
                    <LogOut className="w-4 h-4 mr-2" />
                    <span>Sign out</span>
                  </button>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* 3. Main Workspace Area (Center/Right) */}
      <div className="flex-1 flex flex-col h-full min-w-0 bg-bg-canvas relative">
        
        {/* Top Minimal Header (Breadcrumbs/Status) (FIX 1 & FIX 5) */}
        <header className="h-14 shrink-0 border-b border-border-subtle flex items-center justify-between px-8 z-20 glass-panel relative">
          <div className="flex items-center space-x-2 text-xs font-mono text-muted-slate">
            <span className="text-stark-white font-semibold">Fluxline Console</span>
            <span>/</span>
            <span className="text-accent-solid font-medium text-xs">
              {location.pathname === '/app' ? 'Workspace dashboard' : location.pathname.substring(5).replace(/\//g, ' / ')}
            </span>
          </div>
          
          {/* Search Trigger Button & Health Status */}
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setCmdPaletteOpen(true)}
              className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-bg-card hover:bg-bg-popover border border-border-card text-xs text-muted-slate hover:text-stark-white transition-all cursor-pointer shadow-sm"
            >
              <Search className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Search...</span>
              <kbd className="px-1.5 py-0.5 bg-bg-panel rounded text-[10px] text-stark-white border border-border-card">Ctrl K</kbd>
            </button>

            <div className="relative group">
              {health.status === 'ok' && (
                <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-mono font-semibold">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                  <span>Operational</span>
                </div>
              )}
              
              {(health.status === 'warning' || health.status === 'error') && (
                <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-mono font-semibold cursor-pointer transition-all hover:bg-amber-500/20">
                  <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
                  <span>⚠ Degraded</span>
                </div>
              )}

              {health.status !== 'ok' && health.msg && (
                <div className="absolute right-0 top-full mt-2 w-80 p-3.5 bg-bg-panel border border-border-card rounded-xl shadow-2xl text-xs font-mono text-stark-white opacity-0 group-hover:opacity-100 transition-opacity duration-150 pointer-events-none group-hover:pointer-events-auto z-50">
                  <div className="flex items-center space-x-2 text-amber-400 font-bold mb-1.5">
                    <ShieldAlert className="w-4 h-4 shrink-0" />
                    <span>System Health Details</span>
                  </div>
                  <p className="text-muted-slate leading-relaxed">{health.msg}</p>
                </div>
              )}
            </div>
          </div>

          {/* Thin subtle line under breadcrumb header */}
          <div className="absolute bottom-0 left-0 right-0 h-[1px] bg-white/[0.04]" />
        </header>

        {/* Dynamic Route Viewport with Faint Dot Grid Texture */}
        <main 
          className="flex-1 min-h-0 overflow-y-auto flex flex-col relative w-full custom-scrollbar" 
          id="main-content"
          style={{ 
            backgroundImage: 'radial-gradient(rgba(255,255,255,0.04) 1px, transparent 1px)', 
            backgroundSize: '24px 24px' 
          }}
        >
          <div className="flex-1 flex flex-col relative w-full min-h-full">
            <AnimatePresence mode="wait">
              <motion.div
                key={location.pathname}
                initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, y: 12, filter: 'blur(4px)' }}
                animate={shouldReduceMotion ? { opacity: 1 } : { opacity: 1, y: 0, filter: 'blur(0px)' }}
                exit={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, y: -12, filter: 'blur(4px)' }}
                transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
                className="flex-1 flex flex-col w-full min-h-full"
              >
                <Outlet />
              </motion.div>
            </AnimatePresence>
          </div>
        </main>

        {/* 4. Persistent Global Bottom Status Bar */}
        <AnimatePresence>
          {activeJob && (
            <motion.footer
              initial={{ y: '100%', opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: '100%', opacity: 0 }}
              transition={{ type: 'spring', damping: 28, stiffness: 220 }}
              className="h-12 border-t border-status-info-border bg-status-info-muted/30 backdrop-blur-xl flex items-center justify-between px-8 z-30 shrink-0"
            >
              <div className="flex items-center space-x-4">
                <span className="flex items-center text-xs font-mono font-bold text-status-info uppercase tracking-wider">
                  <Activity className="w-4 h-4 mr-2 text-status-info animate-pulse" />
                  <span>Pipeline Sync Running</span>
                </span>
                <span className="hidden sm:inline text-xs font-mono text-muted-slate">
                  Job Ref: <strong className="text-stark-white select-all font-bold">{activeJob.id.slice(-6)}…</strong>
                </span>
                <span className="hidden md:inline-flex items-center px-2 py-0.5 rounded bg-bg-card border border-border-card text-xs font-mono text-stark-white">
                  {activeJob.rows.toLocaleString()} rows synced
                </span>
              </div>

              <div className="flex items-center space-x-4">
                <button
                  onClick={() => navigate(`/app/progress/${activeJob.id}`)}
                  className="px-4 py-1.5 bg-status-info hover:bg-blue-600 text-white font-mono text-xs font-bold uppercase tracking-wider rounded-lg shadow-[0_0_12px_rgba(59,130,246,0.25)] transition-all flex items-center space-x-1.5 cursor-pointer"
                >
                  <Terminal className="w-3.5 h-3.5" />
                  <span>View Terminal</span>
                </button>
              </div>
            </motion.footer>
          )}
        </AnimatePresence>

        <Demo isOpen={demoOpen} onClose={() => setDemoOpen(false)} />

        <CommandPalette 
          isOpen={cmdPaletteOpen} 
          onClose={() => setCmdPaletteOpen(false)} 
          currentTheme={theme}
          onToggleTheme={() => setTheme(p => p === 'dark' ? 'light' : 'dark')}
        />

        <Suspense fallback={null}>
          <AssistantChat />
        </Suspense>
      </div>
    </div>
  )
}
