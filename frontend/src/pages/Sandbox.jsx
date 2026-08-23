import { useState } from 'react'
import apiClient from '../apiClient'
import { Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Database, Play, AlertCircle, CheckCircle, RefreshCw, Code, Info, Terminal } from 'lucide-react'
import discoverCached from '../assets/discover_cached.json'
import { API_BASE_URL } from '../config'

export default function Sandbox() {
  const [dbType, setDbType] = useState('mssql')
  const [host, setHost] = useState('localhost')
  const [port, setPort] = useState('1433')
  const [username, setUsername] = useState('sa')
  const [password, setPassword] = useState('Ayaz@123')
  const [database, setDatabase] = useState('migrated_sql')
  
  const [status, setStatus] = useState('idle') // idle, loading, success, fallback
  const [outputJson, setOutputJson] = useState(null)
  const [errorMsg, setErrorMsg] = useState('')
  const [runType, setRunType] = useState('') // live, cached
 
  const loadDemo = (type) => {
    if (type === 'mssql') {
      setDbType('mssql')
      setHost('localhost')
      setPort('1433')
      setUsername('sa')
      setPassword('Ayaz@123')
      setDatabase('migrated_sql')
    } else if (type === 'mysql') {
      setDbType('mysql')
      setHost('localhost')
      setPort('3306')
      setUsername('root')
      setPassword('Ayaz@123')
      setDatabase('migration_target')
    } else if (type === 'postgres') {
      setDbType('postgres')
      setHost('localhost')
      setPort('5432')
      setUsername('postgres')
      setPassword('Ayaz@123')
      setDatabase('migration_target')
    }
  }
 
  const runDiscovery = async () => {
    setStatus('loading')
    setErrorMsg('')
    setOutputJson(null)
    setRunType('')
 
    try {
      const res = await apiClient.fetchWithAuth(`${API_BASE_URL}/api/discover`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          db_type: dbType,
          host: host,
          port: parseInt(port) || 0,
          username: username,
          password: password,
          database: database
        })
      })

      if (res.ok) {
        const data = await res.json()
        setOutputJson(data)
        setStatus('success')
        setRunType('live')
      } else {
        const errData = await res.json()
        throw new Error(errData.detail || 'Connection refused or database unreachable.')
      }
    } catch (e) {
      console.warn("Live database discovery failed. Falling back to cached schema.", e)
      // Graceful fallback to cached JSON
      setTimeout(() => {
        setOutputJson(discoverCached)
        setStatus('fallback')
        setRunType('cached')
        setErrorMsg(`Live database not reachable at ${host}:${port} (${e.message}). Showing cached verification payload instead.`)
      }, 800)
    }
  }

  return (
    <div className="min-h-screen bg-[#09090b] text-zinc-200 flex flex-col pt-20 pb-16">
      {/* Main Layout */}
      <div className="flex-1 max-w-7xl mx-auto w-full px-6 py-8 grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Column - Configurations (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          <div className="space-y-1.5">
            <h1 className="text-2xl font-sans font-bold text-white tracking-tight">Interactive SQL Sandbox</h1>
            <p className="text-xs text-zinc-400">Run live catalog discovery on <code className="text-zinc-200 font-mono bg-zinc-900 px-1.5 py-0.5 rounded border border-zinc-800">/discover</code> to inspect table structures, primary keys, and constraint dependencies.</p>
          </div>

          {/* Preset Buttons */}
          <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4 space-y-2.5">
            <span className="text-[11px] font-mono text-zinc-400 uppercase tracking-wider block font-semibold">Pre-Configured Test Sources</span>
            <div className="grid grid-cols-3 gap-2">
              <button 
                onClick={() => loadDemo('mssql')}
                className={`py-2 px-2.5 rounded-lg text-xs font-mono font-medium border transition-all cursor-pointer ${
                  dbType === 'mssql' ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-sm' : 'bg-zinc-800/80 border-zinc-700 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-700'
                }`}
              >
                SQL Server
              </button>
              <button 
                onClick={() => loadDemo('mysql')}
                className={`py-2 px-2.5 rounded-lg text-xs font-mono font-medium border transition-all cursor-pointer ${
                  dbType === 'mysql' ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-sm' : 'bg-zinc-800/80 border-zinc-700 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-700'
                }`}
              >
                MySQL 8.0
              </button>
              <button 
                onClick={() => loadDemo('postgres')}
                className={`py-2 px-2.5 rounded-lg text-xs font-mono font-medium border transition-all cursor-pointer ${
                  dbType === 'postgres' ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-sm' : 'bg-zinc-800/80 border-zinc-700 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-700'
                }`}
              >
                PostgreSQL
              </button>
            </div>
          </div>

          {/* Form Credentials */}
          <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5 space-y-4">
            <span className="text-[11px] font-mono text-zinc-400 uppercase tracking-wider block font-semibold">Connection Parameters</span>
            
            <div className="space-y-3">
              <div>
                <label className="block font-sans text-caption text-text-secondary uppercase tracking-wider mb-1">Dialect Type</label>
                <select 
                  value={dbType} 
                  onChange={e => setDbType(e.target.value)}
                  className="w-full rounded-lg border border-white/10 bg-bg-base text-text-primary px-3 py-2 text-xs font-mono focus:outline-none focus:border-accent"
                >
                  <option value="mssql">MSSQL (SQL Server)</option>
                  <option value="mysql">MySQL</option>
                  <option value="postgres">PostgreSQL</option>
                  <option value="oracle">Oracle</option>
                </select>
              </div>

              <div className="grid grid-cols-3 gap-2">
                <div className="col-span-2">
                  <label className="block font-sans text-caption text-text-secondary uppercase tracking-wider mb-1">Host</label>
                  <input 
                    type="text" 
                    value={host}
                    onChange={e => setHost(e.target.value)}
                    className="w-full rounded-lg border border-white/10 bg-bg-base text-text-primary px-3 py-2 text-xs font-mono focus:outline-none focus:border-accent"
                  />
                </div>
                <div>
                  <label className="block font-sans text-xs text-zinc-400 uppercase tracking-wider mb-1">Port</label>
                  <input 
                    type="text" 
                    value={port}
                    onChange={e => setPort(e.target.value)}
                    className="w-full rounded-lg border border-zinc-800 bg-zinc-950 text-zinc-100 px-3 py-2 text-xs font-mono focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block font-sans text-xs text-zinc-400 uppercase tracking-wider mb-1">Database Name</label>
                <input 
                  type="text" 
                  value={database}
                  onChange={e => setDatabase(e.target.value)}
                  className="w-full rounded-lg border border-zinc-800 bg-zinc-950 text-zinc-100 px-3 py-2 text-xs font-mono focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block font-sans text-xs text-zinc-400 uppercase tracking-wider mb-1">Username</label>
                  <input 
                    type="text" 
                    value={username}
                    onChange={e => setUsername(e.target.value)}
                    className="w-full rounded-lg border border-zinc-800 bg-zinc-950 text-zinc-100 px-3 py-2 text-xs font-mono focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block font-sans text-xs text-zinc-400 uppercase tracking-wider mb-1">Password</label>
                  <input 
                    type="password" 
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    className="w-full rounded-lg border border-zinc-800 bg-zinc-950 text-zinc-100 px-3 py-2 text-xs font-mono focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>
            </div>

            <div className="pt-2">
              <button
                onClick={runDiscovery}
                disabled={status === 'loading'}
                className={`w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white font-semibold rounded-lg text-xs flex items-center justify-center space-x-2 transition-all cursor-pointer shadow-sm ${status === 'loading' ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                {status === 'loading' ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin text-white/70" />
                ) : (
                  <Play className="w-3.5 h-3.5" />
                )}
                <span>Run Schema Discovery</span>
              </button>
            </div>
          </div>
        </div>

        {/* Right Column - Code Terminal Response (7 cols) */}
        <div className="lg:col-span-7 flex flex-col min-h-[500px]">
          <div className="flex-1 bg-zinc-900/60 border border-zinc-800 rounded-xl overflow-hidden flex flex-col font-mono text-xs shadow-xl">
            
            {/* Header tab */}
            <div className="px-4 py-3 bg-zinc-900/90 border-b border-zinc-800 flex items-center justify-between text-zinc-400">
              <span className="flex items-center space-x-2">
                <Terminal className="w-4 h-4 text-indigo-400" />
                <span className="font-semibold text-zinc-200">DISCOVER_RESPONSE.json</span>
              </span>
              
              <div className="flex items-center space-x-2">
                {runType === 'live' && (
                  <span className="flex items-center space-x-1.5 py-0.5 px-2 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded text-[10px] font-semibold">
                    <CheckCircle className="w-3 h-3" />
                    <span>LIVE BACKEND RESPONSE</span>
                  </span>
                )}
                {runType === 'cached' && (
                  <span className="flex items-center space-x-1.5 py-0.5 px-2 bg-amber-500/10 border border-amber-500/20 text-amber-400 rounded text-[10px] font-semibold">
                    <Info className="w-3 h-3" />
                    <span>CACHED TEST PAYLOAD</span>
                  </span>
                )}
              </div>
            </div>

            {/* Error banner details if fallback */}
            {status === 'fallback' && errorMsg && (
              <div className="p-4 bg-amber-500/10 border-b border-border-default text-amber-300 font-sans text-xs flex items-start space-x-2.5">
                <AlertCircle className="w-4.5 h-4.5 text-amber-400 shrink-0 mt-0.5" />
                <span>{errorMsg}</span>
              </div>
            )}

            {/* Code Output panel */}
            <div className="flex-1 p-5 overflow-auto bg-[#050506] text-text-primary max-h-[580px] scrollbar-thin scrollbar-thumb-neutral-800">
              <AnimatePresence mode="wait">
                {status === 'idle' && (
                  <motion.div 
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="h-full flex flex-col items-center justify-center text-center text-text-secondary space-y-2 py-20 font-sans"
                  >
                    <Code className="w-10 h-10 text-neutral-800 mb-2" />
                    <span className="text-xs font-bold text-text-primary">Sandbox Staging Ready</span>
                    <p className="text-xs max-w-xs leading-relaxed font-light">Select a demo preset profile on the left and run discovery to output raw catalog metadata logs.</p>
                  </motion.div>
                )}

                {status === 'loading' && (
                  <motion.div 
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="h-full flex flex-col items-center justify-center text-center text-text-secondary space-y-2 py-20 font-sans"
                  >
                    <RefreshCw className="w-8 h-8 animate-spin text-neutral-400 mb-2" />
                    <span className="text-xs font-bold text-text-primary">Requesting Catalog...</span>
                    <p className="text-xs font-light">Querying system tables information catalog schemas from host.</p>
                  </motion.div>
                )}

                {(status === 'success' || status === 'fallback') && outputJson && (
                  <motion.div
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    className="text-[#22D3EE] leading-relaxed select-all"
                  >
                    <pre className="whitespace-pre overflow-x-auto text-[11px] leading-5 font-mono text-neutral-305">
                      {JSON.stringify(outputJson, null, 2)}
                    </pre>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>

      </div>
    </div>
  )
}
