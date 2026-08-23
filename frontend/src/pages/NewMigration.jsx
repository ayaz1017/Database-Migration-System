import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Server, Settings, ArrowRight, ArrowLeft, CheckCircle, AlertTriangle, RefreshCw, Layers, Check, Lock, X } from 'lucide-react'
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion'
import ObjectPicker from '../components/ObjectPicker'
import { DialectIcon } from '../components/DialectBadge'
import apiClient from '../apiClient'
import { API_BASE_URL } from '../config'
import OracleSetupGuide from '../components/OracleSetupGuide'

const GhostCatalog = () => (
  <div className="space-y-4 opacity-10 pointer-events-none select-none w-full h-full flex flex-col">
    <div className="flex items-center justify-between gap-4 shrink-0">
      <div className="h-6 bg-border-card rounded-md w-1/3"></div>
      <div className="h-6 bg-border-card rounded-md w-1/4"></div>
    </div>
    <div className="h-9 bg-border-card rounded-lg w-full shrink-0"></div>
    <div className="flex-1 space-y-3 pt-2 overflow-hidden">
      {[1, 2, 3, 4, 5, 6].map(i => (
        <div key={i} className="flex items-center justify-between border-b border-border-card/30 pb-2.5">
          <div className="flex items-center space-x-2.5">
            <div className="w-3.5 h-3.5 bg-border-card rounded"></div>
            <div className="h-3.5 bg-border-card rounded w-28"></div>
          </div>
          <div className="h-3.5 bg-border-card rounded w-16"></div>
        </div>
      ))}
    </div>
  </div>
)

const GhostSettings = () => (
  <div className="space-y-6 opacity-10 pointer-events-none select-none w-full h-full flex flex-col justify-between">
    <div className="space-y-6">
      <div className="space-y-2">
        <div className="h-3.5 bg-border-card rounded w-1/4 mb-1"></div>
        <div className="grid grid-cols-3 gap-2.5">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-16 bg-border-card rounded-xl"></div>
          ))}
        </div>
      </div>
      <div className="space-y-3 pt-4 border-t border-border-card/30">
        <div className="h-3.5 bg-border-card rounded w-1/5 mb-1"></div>
        {[1, 2, 3].map(i => (
          <div key={i} className="flex items-center space-x-3.5">
            <div className="w-4 h-4 bg-border-card rounded"></div>
            <div className="h-3.5 bg-border-card rounded w-1/2"></div>
          </div>
        ))}
      </div>
    </div>
    <div className="h-10 bg-border-card rounded-xl w-full mt-6"></div>
  </div>
)

export default function NewMigration() {
  const navigate = useNavigate()
  const shouldReduceMotion = useReducedMotion()

  const [source, setSource] = useState({ db_type: 'mssql', host: 'localhost', port: 1433, username: '', password: '', database: '' })
  const [target, setTarget] = useState({ db_type: 'postgres', host: 'localhost', port: 5432, username: '', password: '', database: '' })
  const [mode, setMode] = useState('full_load')
  const [options, setOptions] = useState({
    migrate_all_tables: true,
    selected_tables: [],
    fk_dependency_mode: 'auto_include',
    migrate_views: false,
    migrate_procedures: false,
    migrate_triggers: false,
    selected_views: [],
    selected_procedures: [],
    selected_triggers: [],
    migrate_data: true,
    apply_masking: false,
    validate_after: true,
    auto_fix: true,
    chunk_size: 5000
  })
  
  const [sourceTest, setSourceTest] = useState({ status: 'idle', msg: '' })
  const [targetTest, setTargetTest] = useState({ status: 'idle', msg: '' })
  const [errors, setErrors] = useState({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [migrationError, setMigrationError] = useState(null)

  const triggerError = (msg) => {
    setMigrationError(msg)
    setTimeout(() => {
      setMigrationError(null)
    }, 8000)
  }

  const validateConfig = (config) => {
    const errs = {}
    const host = (config.host || '').trim()
    const db = (config.database || '').trim()
    const user = (config.username || '').trim()
    const portVal = parseInt(config.port)

    if (!host) {
      errs.host = 'Host address is required.'
    } else if (!/^[a-zA-Z0-9.:-]+$/.test(host) && host !== 'localhost') {
      errs.host = 'Invalid host structure.'
    }

    if (!config.port) {
      errs.port = 'Port number is required.'
    } else if (isNaN(portVal) || portVal < 1 || portVal > 65535) {
      errs.port = 'Port must be between 1 and 65535.'
    }

    if (!db) {
      errs.database = 'Database name is required.'
    }

    if (!user) {
      errs.username = 'Username is required.'
    }

    return errs
  }

  const handleTestConnection = async (config, setTestState) => {
    const validationErrs = validateConfig(config)
    if (Object.keys(validationErrs).length > 0) {
      setTestState({ status: 'error', msg: 'Please fix configuration errors before testing: ' + Object.values(validationErrs).join(' ') })
      return
    }
    
    setTestState({ status: 'loading', msg: '' })
    try {
      const res = await apiClient.fetchWithAuth(`${API_BASE_URL}/api/test-db`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          db_type: config.db_type,
          host: config.host.trim(),
          port: parseInt(config.port) || 0,
          username: config.username.trim(),
          password: config.password,
          database: config.database.trim()
        })
      })
      if (res.ok) {
        setTestState({ status: 'success', msg: 'Connection established successfully.' })
      } else {
        const error = await res.json()
        setTestState({ status: 'error', msg: error.detail || `Could not connect to ${config.db_type} at ${config.host}:${config.port}. Check credentials.` })
      }
    } catch {
      setTestState({ status: 'error', msg: `Could not connect to ${config.db_type} at ${config.host}:${config.port}. Check credentials and firewall.` })
    }
  }
  
  const submitMigration = async () => {
    setIsSubmitting(true)

    // Pre-flight check target database connection before proceeding
    try {
      const testRes = await apiClient.fetchWithAuth(`${API_BASE_URL}/api/test-db`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          db_type: target.db_type,
          host: target.host.trim(),
          port: parseInt(target.port, 10) || 0,
          username: target.username.trim(),
          password: target.password,
          database: target.database.trim()
        })
      })
      if (!testRes.ok) {
        const errData = await testRes.json().catch(() => ({}))
        const errorMsg = errData.detail || 'Access denied or invalid target credentials.'
        triggerError(`Target Database Connection Failed: ${errorMsg}`)
        setIsSubmitting(false)
        return
      }
    } catch (err) {
      triggerError(`Target Database Connection Check Failed: Could not connect to ${target.db_type} at ${target.host}:${target.port}`)
      setIsSubmitting(false)
      return
    }

    const jobId = `mig_${Date.now()}`

    const selectedViews = options.selected_views || []
    const selectedProcedures = options.selected_procedures || []
    const selectedTriggers = options.selected_triggers || []
    const selectedTables = options.selected_tables || []

    const migrationOptions = {
      ...options,
      selected_tables: selectedTables,
      migrate_all_tables: options.migrate_all_tables !== undefined ? options.migrate_all_tables : selectedTables.length === 0,
      migrate_views: selectedViews.length > 0 || !!options.migrate_views,
      migrate_procedures: selectedProcedures.length > 0 || !!options.migrate_procedures,
      migrate_triggers: selectedTriggers.length > 0 || !!options.migrate_triggers,
      selected_views: selectedViews,
      selected_procedures: selectedProcedures,
      selected_triggers: selectedTriggers,
      auto_approve_objects: true,
      fk_dependency_mode: options.fk_dependency_mode || 'auto_include'
    }

    const payload = {
      source: {
        ...source,
        port: parseInt(source.port, 10)
      },
      target: {
        ...target,
        port: parseInt(target.port, 10)
      },
      mode: mode || 'auto_include',
      options: migrationOptions,
      id: jobId
    }

    console.log('Migration payload:', JSON.stringify(payload, null, 2))

    try {
      const res = await apiClient.fetchWithAuth(`${API_BASE_URL}/api/migrate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        let errorMsg = 'Failed to start migration backend job.'
        if (typeof errData.detail === 'string') {
          errorMsg = errData.detail
        } else if (errData.detail && typeof errData.detail === 'object') {
          errorMsg = errData.detail.error || errData.detail.message || JSON.stringify(errData.detail)
        } else if (typeof errData.message === 'string') {
          errorMsg = errData.message
        }
        
        if (res.status === 401 || errorMsg.toLowerCase().includes('authenticated')) {
          triggerError('Authentication required. Please log in again.')
        } else {
          triggerError(`Migration failed to start: ${errorMsg}`)
        }
        setIsSubmitting(false)
        return
      }

      const data = await res.json()
      const actualJobId = data.job_id || jobId
      navigate(`/app/progress/${actualJobId}`, { state: { source, target, mode, options, id: actualJobId } })
    } catch (err) {
      triggerError(`Network error starting migration: ${err.message}`)
      setIsSubmitting(false)
    }
  }

  const getVerifyBtnStyles = (testState, isSource) => {
    if (testState.status === 'loading') {
      return 'bg-bg-panel border-border-card text-muted-slate cursor-not-allowed opacity-75'
    }
    if (testState.status === 'success') {
      return 'bg-status-success/15 border-status-success text-status-success font-bold'
    }
    if (testState.status === 'error') {
      return 'bg-status-error/15 border-status-error text-status-error font-bold'
    }
    const hoverBorder = isSource ? 'hover:border-accent-solid' : 'hover:border-status-info'
    return `bg-bg-card border-border-card text-stark-white ${hoverBorder}`
  }

  const getVerifyBtnContent = (testState) => {
    if (testState.status === 'loading') {
      return (
        <>
          <RefreshCw className="w-3 h-3 animate-spin text-accent-solid" />
          <span>Verifying...</span>
        </>
      )
    }
    if (testState.status === 'success') {
      return (
        <>
          <Check className="w-3 h-3 text-status-success" />
          <span>Verified</span>
        </>
      )
    }
    if (testState.status === 'error') {
      return (
        <>
          <AlertTriangle className="w-3 h-3 text-status-error animate-pulse" />
          <span>Retry</span>
        </>
      )
    }
    return (
      <>
        <RefreshCw className="w-3 h-3 text-muted-slate" />
        <span>Verify Pipe</span>
      </>
    )
  }

  return (
    <div className="flex flex-col xl:flex-row xl:h-[calc(100vh-4rem)] w-full bg-bg-canvas xl:overflow-hidden overflow-y-auto p-5 gap-5 relative min-h-0">
      {/* Background ambient glows */}
      <div className="absolute top-[-10%] left-[-15%] w-[600px] h-[600px] rounded-full bg-accent-solid/5 blur-[120px] -z-10 pointer-events-none"></div>
      <div className="absolute bottom-[-10%] right-[-15%] w-[500px] h-[500px] rounded-full bg-status-info/5 blur-[120px] -z-10 pointer-events-none"></div>

      {/* Error Banner / Toast */}
      {migrationError && (
        <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-50 max-w-lg w-full bg-status-error/95 text-stark-white px-4 py-3 rounded-xl shadow-2xl border border-stark-white/20 backdrop-blur-md flex items-center justify-between gap-3 animate-fade-in">
          <div className="flex items-center gap-2.5">
            <AlertTriangle className="w-5 h-5 shrink-0 text-stark-white animate-pulse" />
            <span className="text-xs font-mono font-bold tracking-wide">{migrationError}</span>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {migrationError.includes('Authentication') && (
              <button
                onClick={() => navigate('/login')}
                className="bg-stark-white text-status-error font-mono font-bold text-[10px] uppercase px-2.5 py-1 rounded hover:bg-stark-white/90 transition-colors shadow-sm"
              >
                Log In
              </button>
            )}
            <button
              onClick={() => setMigrationError(null)}
              className="text-stark-white/80 hover:text-stark-white transition-colors p-1"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* 1. LEFT PANEL: stacked connection credentials (Source & Target) */}
      <div className="xl:flex-[1] w-full xl:min-w-[320px] xl:max-w-[380px] flex flex-col gap-4 overflow-y-auto pr-1.5 scrollbar-thin scrollbar-thumb-border-card shrink-0">
        
        {/* SOURCE DB CARD */}
        <div className="bg-bg-panel/60 border border-border-card/90 border-l-4 border-l-accent-solid rounded-2xl p-4.5 shadow-lg space-y-3 backdrop-blur-md shrink-0">
          <div className="flex items-center space-x-3 mb-0.5">
            <div className="w-7 h-7 rounded-lg bg-accent-solid/10 border border-accent-solid/20 flex items-center justify-center">
              <Server className="w-3.5 h-3.5 text-accent-solid" />
            </div>
            <div>
              <h2 className="text-[11px] font-semibold tracking-[0.08em] uppercase text-text-tertiary font-sans">Source Endpoint</h2>
              <p className="text-[8px] font-mono text-muted-slate uppercase mt-0.5">Extract schema & data</p>
            </div>
          </div>

          <div className="space-y-3">
            <div>
              <label className="block text-[11px] font-semibold tracking-[0.08em] uppercase text-text-tertiary font-sans mb-1.5">Engine Dialect</label>
              <div className="grid grid-cols-4 gap-1.5">
                {[
                  { value: 'mssql', label: 'MSSQL' },
                  { value: 'mysql', label: 'MySQL' },
                  { value: 'postgres', label: 'Postgres' },
                  { value: 'oracle', label: 'Oracle' }
                ].map(db => {
                  const isSelected = source.db_type === db.value
                  return (
                    <button
                      type="button"
                      key={db.value}
                      onClick={() => setSource({ ...source, db_type: db.value })}
                      className={`flex flex-col items-center justify-center py-1.5 rounded-lg border text-center transition-all cursor-pointer ${
                        isSelected 
                          ? 'bg-accent-muted/45 border-accent-solid text-stark-white shadow-sm' 
                          : 'bg-bg-panel/40 border-border-card text-muted-slate hover:text-stark-white hover:border-border-focus'
                      }`}
                    >
                      <DialectIcon dialect={db.value} className="w-3 h-3 mb-1" active={isSelected} />
                      <span className="text-[11px] font-semibold uppercase tracking-[0.05em] font-sans">{db.label}</span>
                    </button>
                  )
                })}
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-semibold tracking-[0.08em] uppercase text-text-tertiary font-sans mb-1">Host Endpoint</label>
              <input 
                type="text" 
                placeholder="e.g. source-db.local"
                value={source.host} 
                onChange={e => {
                  setSource({...source, host: e.target.value})
                  if (errors.host) setErrors(prev => ({ ...prev, host: null }))
                }} 
                className={`w-full rounded-lg border bg-bg-canvas text-[14px] text-text-primary font-sans px-3 py-1.5 focus:border-accent-solid focus:ring-1 focus:ring-accent-solid/35 focus:outline-none transition-all shadow-inner ${
                  errors.host ? 'border-status-error/70' : source.host.trim() ? 'border-status-success-border/30 hover:border-status-success-border/60' : 'border-border-card hover:border-border-subtle'
                }`}
              />
            </div>

            <div className="grid grid-cols-2 gap-3.5">
              <div>
                <label className="block text-[12px] font-medium text-text-secondary font-sans mb-1">Port</label>
                <input 
                  type="number" 
                  placeholder={source.db_type === 'mssql' ? '1433' : source.db_type === 'mysql' ? '3306' : source.db_type === 'postgres' ? '5432' : '1521'}
                  value={source.port} 
                  onChange={e => {
                    setSource({...source, port: e.target.value})
                    if (errors.port) setErrors(prev => ({ ...prev, port: null }))
                  }} 
                  className={`w-full rounded-lg border bg-bg-canvas text-[14px] text-text-primary font-sans px-3 py-1.5 focus:border-accent-solid focus:ring-1 focus:ring-accent-solid/35 focus:outline-none transition-all shadow-inner ${
                    errors.port ? 'border-status-error/70' : source.port ? 'border-status-success-border/30 hover:border-status-success-border/60' : 'border-border-card hover:border-border-subtle'
                  }`}
                />
              </div>
              <div>
                <label className="block text-[12px] font-medium text-text-secondary font-sans mb-1">Database</label>
                <input 
                  type="text" 
                  placeholder="e.g. production_db"
                  value={source.database} 
                  onChange={e => {
                    setSource({...source, database: e.target.value})
                    if (errors.database) setErrors(prev => ({ ...prev, database: null }))
                  }} 
                  className={`w-full rounded-lg border bg-bg-canvas text-[14px] text-text-primary font-sans px-3 py-1.5 focus:border-accent-solid focus:ring-1 focus:ring-accent-solid/35 focus:outline-none transition-all shadow-inner ${
                    errors.database ? 'border-status-error/70' : source.database.trim() ? 'border-status-success-border/30 hover:border-status-success-border/60' : 'border-border-card hover:border-border-subtle'
                  }`}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3.5">
              <div>
                <label className="block text-[12px] font-medium text-text-secondary font-sans mb-1">Username</label>
                <input 
                  type="text" 
                  autoComplete="off"
                  placeholder={source.db_type === 'mssql' ? 'e.g. sa' : 'e.g. root'}
                  value={source.username} 
                  onChange={e => {
                    setSource({...source, username: e.target.value})
                    if (errors.username) setErrors(prev => ({ ...prev, username: null }))
                  }} 
                  className={`w-full rounded-lg border bg-bg-canvas text-[14px] text-text-primary font-sans px-3 py-1.5 focus:border-accent-solid focus:ring-1 focus:ring-accent-solid/35 focus:outline-none transition-all shadow-inner ${
                    errors.username ? 'border-status-error/70' : source.username.trim() ? 'border-status-success-border/30 hover:border-status-success-border/60' : 'border-border-card hover:border-border-subtle'
                  }`}
                />
              </div>
              <div>
                <label className="block text-[12px] font-medium text-text-secondary font-sans mb-1">Password</label>
                <input 
                  type="password" 
                  autoComplete="new-password"
                  placeholder="••••••••"
                  value={source.password} 
                  onChange={e => setSource({...source, password: e.target.value})} 
                  className={`w-full rounded-lg border bg-bg-canvas text-[14px] text-text-primary font-sans px-3 py-1.5 focus:border-accent-solid focus:ring-1 focus:ring-accent-solid/35 focus:outline-none transition-all shadow-inner ${
                    source.password ? 'border-status-success-border/30 hover:border-status-success-border/60' : 'border-border-card hover:border-border-subtle'
                  }`}
                />
              </div>
            </div>

            <div className="pt-1.5 border-t border-border-card/50 flex items-center justify-between">
              <motion.button 
                whileTap={shouldReduceMotion ? {} : { scale: 0.97 }}
                disabled={sourceTest.status === 'loading'}
                onClick={() => handleTestConnection(source, setSourceTest)} 
                className={`px-3 py-1.5 text-[13px] font-semibold font-sans rounded-lg border transition-all flex items-center space-x-1.5 cursor-pointer shadow-sm disabled:opacity-50 ${getVerifyBtnStyles(sourceTest, true)}`}
              >
                {getVerifyBtnContent(sourceTest)}
              </motion.button>
              
              {sourceTest.status === 'success' && (
                <div className="flex items-center space-x-1 text-[11px] font-mono text-status-success bg-status-success/15 px-2 py-0.5 rounded-md border border-status-success-border/30">
                  <CheckCircle className="w-3 h-3" />
                  <span>ONLINE</span>
                </div>
              )}
            </div>
            
            {sourceTest.status === 'error' && (
              <div className="p-2.5 bg-status-error/10 border border-status-error/30 rounded-lg text-[9px] font-mono text-status-error leading-relaxed shadow-sm">
                {sourceTest.msg}
              </div>
            )}
          </div>
        </div>

        {/* TARGET DB CARD */}
        <div className="bg-bg-panel/60 border border-border-card/90 border-l-4 border-l-status-info rounded-2xl p-4.5 shadow-lg space-y-3 backdrop-blur-md">
          <div className="flex items-center space-x-3 mb-0.5">
            <div className="w-7 h-7 rounded-lg bg-status-info/10 border border-status-info/20 flex items-center justify-center">
              <Server className="w-3.5 h-3.5 text-status-info" />
            </div>
            <div>
              <h2 className="text-[11px] font-semibold tracking-[0.08em] uppercase text-text-tertiary font-sans">Target Endpoint</h2>
              <p className="text-[8px] font-mono text-muted-slate uppercase mt-0.5">Load translated schema & data</p>
            </div>
          </div>

          <div className="space-y-3">
            <div>
              <label className="block text-[11px] font-semibold tracking-[0.08em] uppercase text-text-tertiary font-sans mb-1.5">Engine Dialect</label>
              <div className="grid grid-cols-4 gap-1.5">
                {[
                  { value: 'postgres', label: 'Postgres' },
                  { value: 'mysql', label: 'MySQL' },
                  { value: 'mssql', label: 'MSSQL' },
                  { value: 'oracle', label: 'Oracle' }
                ].map(db => {
                  const isSelected = target.db_type === db.value
                  return (
                    <button
                      type="button"
                      key={db.value}
                      onClick={() => setTarget({ ...target, db_type: db.value })}
                      className={`flex flex-col items-center justify-center py-1.5 rounded-lg border text-center transition-all cursor-pointer ${
                        isSelected 
                          ? 'bg-status-info-muted border-status-info text-stark-white shadow-sm' 
                          : 'bg-bg-panel/40 border-border-card text-muted-slate hover:text-stark-white hover:border-border-focus'
                      }`}
                    >
                      <DialectIcon dialect={db.value} className="w-3 h-3 mb-1" active={isSelected} />
                      <span className="text-[11px] font-semibold uppercase tracking-[0.05em] font-sans">{db.label}</span>
                    </button>
                  )
                })}
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-semibold tracking-[0.08em] uppercase text-text-tertiary font-sans mb-1">Host Endpoint</label>
              <input 
                type="text" 
                placeholder="e.g. target-db.local"
                value={target.host} 
                onChange={e => {
                  setTarget({...target, host: e.target.value})
                  if (errors.host) setErrors(prev => ({ ...prev, host: null }))
                }} 
                className={`w-full rounded-lg border bg-bg-canvas text-[14px] text-text-primary font-sans px-3 py-1.5 focus:border-status-info focus:ring-1 focus:ring-status-info/35 focus:outline-none transition-all shadow-inner ${
                  errors.host ? 'border-status-error/70' : target.host.trim() ? 'border-status-success-border/30 hover:border-status-success-border/60' : 'border-border-card hover:border-border-subtle'
                }`}
              />
            </div>

            <div className="grid grid-cols-2 gap-3.5">
              <div>
                <label className="block text-[12px] font-medium text-text-secondary font-sans mb-1">Port</label>
                <input 
                  type="number" 
                  placeholder={target.db_type === 'postgres' ? '5432' : target.db_type === 'mysql' ? '3306' : target.db_type === 'mssql' ? '1433' : '1521'}
                  value={target.port} 
                  onChange={e => {
                    setTarget({...target, port: e.target.value})
                    if (errors.port) setErrors(prev => ({ ...prev, port: null }))
                  }} 
                  className={`w-full rounded-lg border bg-bg-canvas text-[14px] text-text-primary font-sans px-3 py-1.5 focus:border-status-info focus:ring-1 focus:ring-status-info/35 focus:outline-none transition-all shadow-inner ${
                    errors.port ? 'border-status-error/70' : target.port ? 'border-status-success-border/30 hover:border-status-success-border/60' : 'border-border-card hover:border-border-subtle'
                  }`}
                />
              </div>
              <div>
                <label className="block text-[12px] font-medium text-text-secondary font-sans mb-1">Database</label>
                <input 
                  type="text" 
                  placeholder="e.g. migration_target"
                  value={target.database} 
                  onChange={e => {
                    setTarget({...target, database: e.target.value})
                    if (errors.database) setErrors(prev => ({ ...prev, database: null }))
                  }} 
                  className={`w-full rounded-lg border bg-bg-canvas text-[14px] text-text-primary font-sans px-3 py-1.5 focus:border-status-info focus:ring-1 focus:ring-status-info/35 focus:outline-none transition-all shadow-inner ${
                    errors.database ? 'border-status-error/70' : target.database.trim() ? 'border-status-success-border/30 hover:border-status-success-border/60' : 'border-border-card hover:border-border-subtle'
                  }`}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3.5">
              <div>
                <label className="block text-[12px] font-medium text-text-secondary font-sans mb-1">Username</label>
                <input 
                  type="text" 
                  autoComplete="off"
                  placeholder={target.db_type === 'postgres' ? 'e.g. postgres' : 'e.g. root'}
                  value={target.username} 
                  onChange={e => {
                    setTarget({...target, username: e.target.value})
                    if (errors.username) setErrors(prev => ({ ...prev, username: null }))
                  }} 
                  className={`w-full rounded-lg border bg-bg-canvas text-[14px] text-text-primary font-sans px-3 py-1.5 focus:border-status-info focus:ring-1 focus:ring-status-info/35 focus:outline-none transition-all shadow-inner ${
                    errors.username ? 'border-status-error/70' : target.username.trim() ? 'border-status-success-border/30 hover:border-status-success-border/60' : 'border-border-card hover:border-border-subtle'
                  }`}
                />
              </div>
              <div>
                <label className="block text-[12px] font-medium text-text-secondary font-sans mb-1">Password</label>
                <input 
                  type="password" 
                  autoComplete="new-password"
                  placeholder="••••••••"
                  value={target.password} 
                  onChange={e => setTarget({...target, password: e.target.value})} 
                  className={`w-full rounded-lg border bg-bg-canvas text-[14px] text-text-primary font-sans px-3 py-1.5 focus:border-status-info focus:ring-1 focus:ring-status-info/35 focus:outline-none transition-all shadow-inner ${
                    target.password ? 'border-status-success-border/30 hover:border-status-success-border/60' : 'border-border-card hover:border-border-subtle'
                  }`}
                />
              </div>
            </div>

            <div className="pt-1.5 border-t border-border-card/50 flex items-center justify-between">
              <motion.button 
                whileTap={shouldReduceMotion ? {} : { scale: 0.97 }}
                disabled={targetTest.status === 'loading'}
                onClick={() => handleTestConnection(target, setTargetTest)} 
                className={`px-3 py-1.5 text-[13px] font-semibold font-sans rounded-lg border transition-all flex items-center space-x-1.5 cursor-pointer shadow-sm disabled:opacity-50 ${getVerifyBtnStyles(targetTest, false)}`}
              >
                {getVerifyBtnContent(targetTest)}
              </motion.button>
              
              {targetTest.status === 'success' && (
                <div className="flex items-center space-x-1 text-[11px] font-mono text-status-info bg-status-info-muted px-2 py-0.5 rounded-md border border-status-info-border/30">
                  <CheckCircle className="w-3 h-3" />
                  <span>ONLINE</span>
                </div>
              )}
            </div>
            
            {targetTest.status === 'error' && (
              <div className="p-2.5 bg-status-error/10 border border-status-error/30 rounded-lg text-[9px] font-mono text-status-error leading-relaxed shadow-sm">
                {targetTest.msg}
              </div>
            )}
            
            {target.db_type === 'oracle' && targetTest.status === 'success' && (
              <OracleSetupGuide username={target.username} />
            )}
          </div>
        </div>

      </div>

      {/* 2. CENTER PANEL: Object catalog / selection */}
      <div className="xl:flex-[2] w-full min-h-[600px] xl:min-h-0 xl:min-w-[500px] flex flex-col bg-bg-panel/40 border border-border-card/85 rounded-2xl p-5 shadow-xl relative overflow-hidden shrink-0">
        <GhostCatalog />
        
        <AnimatePresence mode="wait">
          {sourceTest.status !== 'success' ? (
            <motion.div 
              key="locked-catalog"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="absolute inset-0 z-20 backdrop-blur-md bg-bg-canvas/40 flex flex-col items-center justify-center p-6 text-center"
            >
              <div className="max-w-xs bg-bg-card border border-border-card p-6 rounded-2xl shadow-2xl flex flex-col items-center space-y-4">
                <div className="w-10 h-10 rounded-xl bg-bg-panel border border-border-card flex items-center justify-center text-muted-slate shadow-lg shrink-0">
                  <Lock className="w-4.5 h-4.5 text-muted-slate" />
                </div>
                <div className="space-y-1.5">
                  <h3 className="text-[11px] font-mono font-black uppercase text-stark-white tracking-widest">Asset Catalog Locked</h3>
                  <p className="text-[9px] font-mono text-muted-slate uppercase leading-relaxed">
                    Test and verify source connection credentials to load discovered catalog.
                  </p>
                </div>
                
                {/* Visual arrow pointing back to source verification */}
                <div className="flex items-center justify-center space-x-1.5 text-[9px] font-mono text-accent-solid mt-1">
                  <motion.div 
                    animate={{ x: [0, -4, 0] }}
                    transition={{ repeat: Infinity, duration: 1.5, ease: "easeInOut" }}
                  >
                    <ArrowLeft className="w-3.5 h-3.5" />
                  </motion.div>
                  <span className="font-black uppercase tracking-wider">Verify Source Endpoint</span>
                </div>
              </div>
            </motion.div>
          ) : (
            <motion.div 
              key="unlocked-catalog"
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.25, ease: 'easeOut' }}
              className="absolute inset-0 z-10 bg-bg-panel/10 p-5 flex flex-col min-h-0 w-full"
            >
              <div className="flex items-center space-x-3 mb-4 shrink-0">
                <div className="w-8 h-8 rounded-lg bg-status-warning/10 border border-status-warning/30 flex items-center justify-center shrink-0">
                  <Layers className="w-4 h-4 text-status-warning" />
                </div>
                <div>
                  <h2 className="text-xs font-mono font-black text-stark-white uppercase tracking-wider">Database Objects Catalog</h2>
                  <p className="text-[9px] font-mono text-muted-slate uppercase mt-0.5">Select assets to map & translate</p>
                </div>
              </div>
              
              <div className="flex-1 min-h-0 w-full overflow-hidden">
                <ObjectPicker 
                  sourceConfig={source} 
                  options={options} 
                  onOptionsChange={setOptions} 
                />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

      </div>

      {/* 3. RIGHT PANEL: Options & Submit */}
      <div className="xl:flex-[1] w-full min-h-[500px] xl:min-w-[320px] xl:max-w-[380px] xl:min-h-0 flex flex-col bg-bg-panel/40 border border-border-card/85 rounded-2xl p-5 shadow-xl justify-between relative overflow-hidden shrink-0">
        <GhostSettings />
        
        <AnimatePresence mode="wait">
          {targetTest.status !== 'success' ? (
            <motion.div 
              key="locked-settings"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="absolute inset-0 z-20 backdrop-blur-md bg-bg-canvas/40 flex flex-col items-center justify-center p-6 text-center"
            >
              <div className="max-w-xs bg-bg-card border border-border-card p-6 rounded-2xl shadow-2xl flex flex-col items-center space-y-4">
                <div className="w-10 h-10 rounded-xl bg-bg-panel border border-border-card flex items-center justify-center text-muted-slate shadow-lg shrink-0">
                  <Lock className="w-4.5 h-4.5 text-muted-slate" />
                </div>
                <div className="space-y-1.5">
                  <h3 className="text-[11px] font-mono font-black uppercase text-stark-white tracking-widest">Settings Locked</h3>
                  <p className="text-[9px] font-mono text-muted-slate uppercase leading-relaxed">
                    Verify target endpoint connection credentials to unlock pipeline parameters.
                  </p>
                </div>
                
                {/* Visual arrow pointing back to target verification */}
                <div className="flex items-center justify-center space-x-1.5 text-[9px] font-mono text-status-info mt-1">
                  <motion.div 
                    animate={{ x: [0, -4, 0] }}
                    transition={{ repeat: Infinity, duration: 1.5, ease: "easeInOut" }}
                  >
                    <ArrowLeft className="w-3.5 h-3.5" />
                  </motion.div>
                  <span className="font-black uppercase tracking-wider">Verify Target Endpoint</span>
                </div>
              </div>
            </motion.div>
          ) : (
            <motion.div 
              key="unlocked-settings"
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.25, ease: 'easeOut' }}
              className="absolute inset-0 z-10 bg-bg-panel/10 p-5 flex flex-col justify-between min-h-0 w-full"
            >
              <div className="flex-1 flex flex-col justify-between min-h-0 w-full space-y-6">
                <div className="space-y-6 overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-border-card min-h-0">
                  <div className="flex items-center space-x-3 mb-2 shrink-0">
                    <div className="w-8 h-8 rounded-lg bg-status-success/10 border border-status-success/30 flex items-center justify-center shrink-0">
                      <Settings className="w-4 h-4 text-status-success" />
                    </div>
                    <div>
                      <h2 className="text-xs font-mono font-black text-stark-white uppercase tracking-wider">Engine Settings</h2>
                      <p className="text-[9px] font-mono text-muted-slate uppercase mt-0.5">Sync strategies & policies</p>
                    </div>
                  </div>

                  {/* Sync Strategy selection */}
                  <div>
                    <label className="block text-[9px] font-mono text-stark-white/80 font-bold uppercase tracking-widest mb-3">Sync Strategy</label>
                    <div className="flex flex-col gap-3">
                       {['full_load', 'cdc', 'full_then_cdc'].map((m) => {
                         const isSelected = mode === m;
                         const labels = {
                           full_load: { title: 'Bulk Snapshot', desc: 'One-time massive load via optimized backend workers.' },
                           cdc: { title: 'CDC Sync', desc: 'Real-time incremental capture via Airbyte engine.' },
                           full_then_cdc: { title: 'Hybrid Sync', desc: 'Snapshot followed by continuous incremental capture.' }
                         }
                         return (
                           <div 
                             key={m}
                             onClick={() => setMode(m)}
                             className={`cursor-pointer rounded-xl p-3.5 border-2 transition-all flex flex-col space-y-1 ${
                               isSelected 
                                 ? 'border-status-success bg-status-success/5 shadow-sm' 
                                 : 'border-border-card bg-bg-card hover:border-border-focus'
                             }`}
                           >
                             <div className="flex items-center justify-between">
                               <span className={`text-[11px] font-mono font-bold uppercase tracking-wider ${isSelected ? 'text-stark-white' : 'text-muted-slate'}`}>
                                 {labels[m].title}
                               </span>
                               <div className={`w-3.5 h-3.5 rounded-full border flex items-center justify-center ${isSelected ? 'border-status-success' : 'border-border-card'}`}>
                                  {isSelected && <div className="w-1.5 h-1.5 rounded-full bg-status-success"></div>}
                               </div>
                             </div>
                             <p className="text-[9px] text-muted-slate font-mono leading-relaxed">{labels[m].desc}</p>
                           </div>
                         )
                       })}
                    </div>
                  </div>

                  {/* Advanced rules checklist */}
                  <div className="space-y-2.5 pt-4 border-t border-border-card/60">
                    <label className="block text-[9px] font-mono text-stark-white/80 font-bold uppercase tracking-widest mb-2">Execution Rules</label>
                    
                    {[
                      { key: 'auto_fix', label: 'Auto-fix minor DDL validation mismatches' },
                      { key: 'validate_after', label: 'Validate row count sweeps after stream' },
                      { key: 'migrate_data', label: 'Migrate raw table datasets (exclude skeleton)' },
                      { key: 'apply_masking', label: 'Apply Data Masking Rules (PII Anonymization)' },
                    ].map((rule) => (
                      <label key={rule.key} className="flex items-start space-x-3 cursor-pointer group p-2 rounded-lg hover:bg-bg-card border border-transparent hover:border-border-card transition-all">
                        <div className="pt-0.5">
                          <input 
                            type="checkbox" 
                            className="h-4.5 w-4.5 bg-bg-canvas border-border-card rounded text-status-success focus:ring-0 focus:ring-offset-0 transition-colors cursor-pointer" 
                            checked={options[rule.key]}
                            onChange={e => setOptions({ ...options, [rule.key]: e.target.checked })}
                          />
                        </div>
                        <span className="text-[11px] font-mono font-medium text-muted-slate group-hover:text-stark-white transition-colors">{rule.label}</span>
                      </label>
                    ))}

                    {/* AST Warning notice if custom code translations are selected */}
                    {(options.migrate_views || options.migrate_procedures || options.migrate_triggers) && (
                      <div className="mt-4 p-3.5 rounded-lg border border-indigo-500/30 bg-indigo-500/10 text-zinc-200 font-mono text-[11px] leading-relaxed shadow-sm flex items-start space-x-2.5">
                        <Layers className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
                        <div>
                          <div className="font-semibold text-indigo-300 uppercase tracking-wider mb-0.5">AST Transcompiler Enabled</div>
                          <span className="text-zinc-400">Stored procedures & views will compile to target dialect with human verification checks.</span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Pipeline Start Button */}
                <div className="pt-4 border-t border-border-card/60 shrink-0">
                  <motion.button 
                    whileTap={shouldReduceMotion ? {} : { scale: 0.98 }}
                    disabled={isSubmitting || (!options.migrate_all_tables && (!options.selected_tables || options.selected_tables.length === 0) && (!options.selected_views || options.selected_views.length === 0) && (!options.selected_procedures || options.selected_procedures.length === 0) && (!options.selected_triggers || options.selected_triggers.length === 0))}
                    className="w-full py-3 rounded-lg text-xs font-sans font-semibold tracking-wide bg-emerald-600 hover:bg-emerald-500 text-white flex items-center justify-center space-x-2 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed shadow-sm transition-colors"
                    onClick={submitMigration}
                  >
                    <span>{isSubmitting ? 'Initializing Pipeline...' : 'Start Migration Pipeline'}</span>
                    <ArrowRight className="w-4 h-4 text-white" />
                  </motion.button>
                </div>
                
              </div>
            </motion.div>
          )}
        </AnimatePresence>

      </div>
    </div>
  )
}
