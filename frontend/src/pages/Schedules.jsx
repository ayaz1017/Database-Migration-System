import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Calendar, Clock, Plus, Play, Pause, Trash2, Edit3, CheckCircle2, AlertCircle, RefreshCw, Database, Layers, ArrowRight, Shield, Sparkles } from 'lucide-react'
import apiClient from '../apiClient'
import { API_BASE_URL } from '../config'
import toast from 'react-hot-toast'

const FREQUENCY_PRESETS = [
  { id: '15m', label: 'Every 15 Minutes', type: 'interval', seconds: 900 },
  { id: '1h', label: 'Hourly', type: 'interval', seconds: 3600 },
  { id: 'daily', label: 'Daily at Midnight', type: 'cron', cron: '0 0 * * *' },
  { id: 'weekly', label: 'Weekly on Sunday', type: 'cron', cron: '0 0 * * 0' },
  { id: 'custom_cron', label: 'Custom Cron Expression', type: 'cron', cron: '0 */4 * * *' },
]

export default function Schedules() {
  const [schedules, setSchedules] = useState([])
  const [loading, setLoading] = useState(true)
  const [wizardOpen, setWizardOpen] = useState(false)
  const [editingSchedule, setEditingSchedule] = useState(null)
  const [runningId, setRunningId] = useState(null)

  // Wizard Step State (1: General, 2: Source, 3: Target, 4: Objects/Options, 5: Schedule Frequency)
  const [step, setStep] = useState(1)
  const [name, setName] = useState('')
  const [sourceDbType, setSourceDbType] = useState('mysql')
  const [sourceConn, setSourceConn] = useState('root:password@localhost:3306/source_db')
  const [targetDbType, setTargetDbType] = useState('postgres')
  const [targetConn, setTargetConn] = useState('postgres:password@localhost:5432/target_db')
  const [selectedTables, setSelectedTables] = useState(['users', 'orders', 'products'])
  const [applyMasking, setApplyMasking] = useState(false)
  const [frequencyPreset, setFrequencyPreset] = useState('1h')
  const [customCron, setCustomCron] = useState('0 0 * * *')
  const [customIntervalSec, setCustomIntervalSec] = useState(3600)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    fetchSchedules()
  }, [])

  const fetchSchedules = async () => {
    setLoading(true)
    try {
      const res = await apiClient.fetchWithAuth(`${API_BASE_URL}/api/schedules`)
      if (res.ok) {
        const data = await res.json()
        setSchedules(data)
      } else {
        toast.error('Failed to load migration schedules')
      }
    } catch (e) {
      console.error(e)
      toast.error('Error fetching schedules')
    } finally {
      setLoading(false)
    }
  }

  const handleOpenWizard = () => {
    setEditingSchedule(null)
    setStep(1)
    setName('')
    setSourceDbType('mysql')
    setSourceConn('root:password@localhost:3306/source_db')
    setTargetDbType('postgres')
    setTargetConn('postgres:password@localhost:5432/target_db')
    setSelectedTables(['users', 'orders', 'products'])
    setApplyMasking(false)
    setFrequencyPreset('1h')
    setCustomCron('0 0 * * *')
    setCustomIntervalSec(3600)
    setWizardOpen(true)
  }

  const handleOpenEditWizard = (sch) => {
    setEditingSchedule(sch)
    setStep(1)
    setName(sch.name)
    setSourceDbType(sch.source_db_type)
    setSourceConn(sch.source_connection)
    setTargetDbType(sch.target_db_type)
    setTargetConn(sch.target_connection)
    setSelectedTables(sch.selected_tables || [])
    setApplyMasking(sch.apply_masking || false)
    if (sch.schedule_type === 'cron') {
      setFrequencyPreset('custom_cron')
      setCustomCron(sch.cron_expression || '0 0 * * *')
    } else {
      setFrequencyPreset('1h')
      setCustomIntervalSec(sch.interval_seconds || 3600)
    }
    setWizardOpen(true)
  }

  const handleSaveSchedule = async (e) => {
    e.preventDefault()
    if (!name.trim()) {
      toast.error('Schedule name is required')
      return
    }

    setSaving(true)

    let schedType = 'interval'
    let cronExpr = null
    let intervalSec = 3600

    const selectedPresetObj = FREQUENCY_PRESETS.find(p => p.id === frequencyPreset)
    if (selectedPresetObj) {
      schedType = selectedPresetObj.type
      if (schedType === 'cron') {
        cronExpr = frequencyPreset === 'custom_cron' ? customCron : selectedPresetObj.cron
      } else {
        intervalSec = selectedPresetObj.seconds
      }
    }

    const payload = {
      name: name.trim(),
      schedule_type: schedType,
      cron_expression: cronExpr,
      interval_seconds: intervalSec,
      source_db_type: sourceDbType,
      source_connection: sourceConn,
      target_db_type: targetDbType,
      target_connection: targetConn,
      selected_tables: selectedTables,
      apply_masking: applyMasking,
      enabled: true
    }

    try {
      if (editingSchedule) {
        const res = await apiClient.fetchWithAuth(`${API_BASE_URL}/api/schedules/${editingSchedule.id}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        })
        if (res.ok) {
          toast.success('Schedule updated successfully')
          setWizardOpen(false)
          fetchSchedules()
        } else {
          toast.error('Failed to update schedule')
        }
      } else {
        const res = await apiClient.fetchWithAuth(`${API_BASE_URL}/api/schedules`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        })
        if (res.ok) {
          toast.success('Migration schedule created successfully')
          setWizardOpen(false)
          fetchSchedules()
        } else {
          toast.error('Failed to create schedule')
        }
      }
    } catch (err) {
      toast.error('Network error saving schedule')
    } finally {
      setSaving(false)
    }
  }

  const handleToggleEnable = async (sch) => {
    try {
      const res = await apiClient.fetchWithAuth(`${API_BASE_URL}/api/schedules/${sch.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: !sch.enabled })
      })
      if (res.ok) {
        toast.success(`Schedule ${!sch.enabled ? 'resumed' : 'paused'}`)
        fetchSchedules()
      }
    } catch (e) {
      toast.error('Error toggling schedule state')
    }
  }

  const handleDeleteSchedule = async (id) => {
    if (!confirm('Are you sure you want to delete this schedule?')) return
    try {
      const res = await apiClient.fetchWithAuth(`${API_BASE_URL}/api/schedules/${id}`, {
        method: 'DELETE'
      })
      if (res.ok) {
        toast.success('Schedule deleted')
        fetchSchedules()
      }
    } catch (e) {
      toast.error('Error deleting schedule')
    }
  }

  const handleRunNow = async (id) => {
    setRunningId(id)
    try {
      const res = await apiClient.fetchWithAuth(`${API_BASE_URL}/api/schedules/${id}/run-now`, {
        method: 'POST'
      })
      if (res.ok) {
        toast.success('Scheduled migration triggered immediately!')
        fetchSchedules()
      } else {
        toast.error('Failed to trigger execution')
      }
    } catch (e) {
      toast.error('Error executing scheduled migration')
    } finally {
      setRunningId(null)
    }
  }

  const activeCount = schedules.filter(s => s.enabled).length
  const totalRuns = schedules.reduce((s, sch) => s + (sch.run_count || 0), 0)

  return (
    <div className="p-8 max-w-[1600px] mx-auto w-full flex flex-col space-y-6 min-h-full">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 shrink-0">
        <div>
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
              <Calendar className="w-5 h-5" />
            </div>
            <h1 className="font-sans text-h1 font-bold text-text-primary tracking-tight">
              Automated Migration Schedules
            </h1>
          </div>
          <p className="text-muted-slate text-sm mt-1.5 font-mono">
            Orchestrate recurring interval and cron migration jobs powered by APScheduler with background error handling.
          </p>
        </div>
        <button
          onClick={handleOpenWizard}
          className="bg-purple-600 hover:bg-purple-500 text-white px-5 py-2.5 rounded-xl font-mono text-xs font-bold transition-all flex items-center shadow-[0_0_20px_rgba(168,85,247,0.3)] cursor-pointer"
        >
          <Plus className="w-4 h-4 mr-2" />
          Create New Schedule
        </button>
      </div>

      {/* Metric Cards Banner */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 shrink-0">
        <div className="glass-panel rounded-2xl p-4">
          <span className="text-xs text-gray-400 font-mono uppercase tracking-wider block">Total Schedules</span>
          <span className="text-2xl font-bold text-text-primary font-mono mt-1 block">{schedules.length}</span>
        </div>
        <div className="glass-panel rounded-2xl p-4">
          <span className="text-xs text-gray-400 font-mono uppercase tracking-wider block">Active Jobs</span>
          <span className="text-2xl font-bold text-emerald-400 font-mono mt-1 block">{activeCount}</span>
        </div>
        <div className="glass-panel rounded-2xl p-4">
          <span className="text-xs text-gray-400 font-mono uppercase tracking-wider block">Total Executions</span>
          <span className="text-2xl font-bold text-purple-400 font-mono mt-1 block">{totalRuns}</span>
        </div>
        <div className="glass-panel rounded-2xl p-4">
          <span className="text-xs text-gray-400 font-mono uppercase tracking-wider block">Scheduler Backend</span>
          <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-2.5 py-1 rounded-md inline-block mt-2 flex items-center w-max">
            <Sparkles className="w-3.5 h-3.5 mr-1" /> APScheduler 3.11
          </span>
        </div>
      </div>

      {/* Main Content: Schedule Cards Grid */}
      <div className="flex-1 min-h-0 flex flex-col space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-text-primary font-mono flex items-center">
            <Clock className="w-4 h-4 mr-2 text-purple-400" />
            Configured Migration Schedules ({schedules.length})
          </h2>
          <button 
            onClick={fetchSchedules}
            className="text-xs font-mono text-gray-400 hover:text-white flex items-center cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        {loading ? (
          <div className="p-12 text-center text-gray-400 font-mono bg-white/[0.02] border border-white/5 rounded-2xl">
            Loading scheduled migration jobs...
          </div>
        ) : schedules.length === 0 ? (
          <div className="p-12 text-center border border-dashed border-white/10 rounded-2xl bg-white/[0.02]">
            <Calendar className="w-12 h-12 text-gray-500 mx-auto mb-3" />
            <h3 className="text-base font-bold text-white font-mono">No Active Migration Schedules</h3>
            <p className="text-xs text-gray-400 font-mono mt-1 max-w-md mx-auto">
              Automate sync routines by setting up interval or cron-based schedules for continuous target database updates.
            </p>
            <button
              onClick={handleOpenWizard}
              className="mt-4 bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/40 px-4 py-2 rounded-xl text-xs font-mono font-bold cursor-pointer"
            >
              Configure Schedule
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 overflow-y-auto pr-1">
            {schedules.map(sch => (
              <div key={sch.id} className="bg-[#0c0c14]/90 border border-white/10 rounded-2xl p-5 backdrop-blur-xl glass-panel flex flex-col justify-between relative">
                <div>
                  <div className="flex items-center justify-between mb-3 border-b border-white/10 pb-3">
                    <span className="font-mono text-sm font-bold text-white truncate max-w-[200px]" title={sch.name}>
                      {sch.name}
                    </span>
                    <button
                      onClick={() => handleToggleEnable(sch)}
                      className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold border transition-colors cursor-pointer ${
                        sch.enabled 
                          ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' 
                          : 'bg-amber-500/10 border-amber-500/30 text-amber-400'
                      }`}
                    >
                      {sch.enabled ? 'ACTIVE' : 'PAUSED'}
                    </button>
                  </div>

                  <div className="space-y-2.5 font-mono text-xs mb-4">
                    <div className="flex items-center text-gray-300">
                      <Clock className="w-3.5 h-3.5 mr-2 text-purple-400 shrink-0" />
                      <span>
                        {sch.schedule_type === 'cron' ? `Cron: ${sch.cron_expression}` : `Interval: Every ${sch.interval_seconds}s`}
                      </span>
                    </div>

                    <div className="flex items-center space-x-2 text-gray-300 bg-white/[0.03] p-2 rounded-xl border border-white/5">
                      <Database className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                      <span className="uppercase font-bold text-[11px] text-blue-300">{sch.source_db_type}</span>
                      <ArrowRight className="w-3 h-3 text-gray-500" />
                      <span className="uppercase font-bold text-[11px] text-purple-300">{sch.target_db_type}</span>
                    </div>

                    {sch.apply_masking && (
                      <div className="flex items-center text-[11px] text-purple-300">
                        <Shield className="w-3.5 h-3.5 mr-1.5 text-purple-400" />
                        Data Masking Active
                      </div>
                    )}
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between text-[11px] font-mono text-gray-400 pt-3 border-t border-white/10 mb-3">
                    <span>Runs: {sch.run_count || 0}</span>
                    <span>Failures: {sch.failure_count || 0}</span>
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleRunNow(sch.id)}
                      disabled={runningId === sch.id}
                      className="flex-1 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-mono text-xs font-bold py-1.5 rounded-xl transition-colors cursor-pointer flex items-center justify-center"
                    >
                      <Play className={`w-3.5 h-3.5 mr-1 fill-current ${runningId === sch.id ? 'animate-spin' : ''}`} />
                      {runningId === sch.id ? 'Triggering...' : 'Run Now'}
                    </button>
                    <button
                      onClick={() => handleOpenEditWizard(sch)}
                      className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-gray-300 transition-colors cursor-pointer"
                      title="Edit Schedule"
                    >
                      <Edit3 className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => handleDeleteSchedule(sch.id)}
                      className="p-2 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-red-400 transition-colors cursor-pointer"
                      title="Delete Schedule"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 5-Step Schedule Creation Wizard Modal */}
      <AnimatePresence>
        {wizardOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-[#0e0e18] border border-white/15 rounded-2xl p-6 max-w-lg w-full shadow-2xl relative"
            >
              <div className="flex items-center justify-between mb-4 border-b border-white/10 pb-3">
                <h3 className="text-base font-bold text-white font-mono flex items-center">
                  <Calendar className="w-4 h-4 mr-2 text-purple-400" />
                  {editingSchedule ? 'Edit Migration Schedule' : `New Schedule Wizard (Step ${step}/5)`}
                </h3>
                <span className="text-xs font-mono text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded">
                  STEP {step} OF 5
                </span>
              </div>

              <form onSubmit={handleSaveSchedule} className="space-y-4 font-mono text-xs">
                {/* Step 1: Name & Description */}
                {step === 1 && (
                  <div className="space-y-3">
                    <label className="text-gray-300 font-bold block">1. Schedule Name</label>
                    <input
                      type="text"
                      placeholder="e.g. Hourly Customers Sync, Daily Audit Dump"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="w-full bg-[#050508] border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-purple-500"
                      required
                    />
                  </div>
                )}

                {/* Step 2: Source Connection */}
                {step === 2 && (
                  <div className="space-y-3">
                    <label className="text-gray-300 font-bold block">2. Source Database Connection</label>
                    <select
                      value={sourceDbType}
                      onChange={(e) => setSourceDbType(e.target.value)}
                      className="w-full bg-[#050508] border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-purple-500 mb-2"
                    >
                      <option value="mysql">MySQL</option>
                      <option value="postgres">PostgreSQL</option>
                      <option value="mssql">SQL Server (MSSQL)</option>
                      <option value="oracle">Oracle</option>
                    </select>
                    <input
                      type="text"
                      placeholder="user:password@host:port/database"
                      value={sourceConn}
                      onChange={(e) => setSourceConn(e.target.value)}
                      className="w-full bg-[#050508] border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-purple-500"
                    />
                  </div>
                )}

                {/* Step 3: Target Connection */}
                {step === 3 && (
                  <div className="space-y-3">
                    <label className="text-gray-300 font-bold block">3. Target Database Connection</label>
                    <select
                      value={targetDbType}
                      onChange={(e) => setTargetDbType(e.target.value)}
                      className="w-full bg-[#050508] border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-purple-500 mb-2"
                    >
                      <option value="postgres">PostgreSQL</option>
                      <option value="mysql">MySQL</option>
                      <option value="mssql">SQL Server (MSSQL)</option>
                    </select>
                    <input
                      type="text"
                      placeholder="user:password@host:port/database"
                      value={targetConn}
                      onChange={(e) => setTargetConn(e.target.value)}
                      className="w-full bg-[#050508] border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-purple-500"
                    />
                  </div>
                )}

                {/* Step 4: Tables & Masking Options */}
                {step === 4 && (
                  <div className="space-y-3">
                    <label className="text-gray-300 font-bold block">4. Tables & Transformation Options</label>
                    <p className="text-gray-400">Select tables to include in recurring pipeline:</p>
                    <div className="p-3 bg-[#050508] border border-white/10 rounded-xl space-y-1">
                      {['users', 'orders', 'products', 'audit_logs'].map(tb => (
                        <label key={tb} className="flex items-center space-x-2 text-gray-300 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={selectedTables.includes(tb)}
                            onChange={(e) => {
                              if (e.target.checked) setSelectedTables([...selectedTables, tb])
                              else setSelectedTables(selectedTables.filter(t => t !== tb))
                            }}
                            className="accent-purple-500 rounded"
                          />
                          <span>{tb}</span>
                        </label>
                      ))}
                    </div>

                    <label className="flex items-center space-x-2 pt-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={applyMasking}
                        onChange={(e) => setApplyMasking(e.target.checked)}
                        className="accent-purple-500 rounded"
                      />
                      <span className="text-purple-300 font-bold">Apply Configured Data Masking Rules</span>
                    </label>
                  </div>
                )}

                {/* Step 5: Cron / Interval Frequency */}
                {step === 5 && (
                  <div className="space-y-3">
                    <label className="text-gray-300 font-bold block">5. Execution Schedule Frequency</label>
                    <div className="space-y-2">
                      {FREQUENCY_PRESETS.map(fp => (
                        <label 
                          key={fp.id}
                          className={`flex items-center justify-between p-3 rounded-xl border cursor-pointer transition-colors ${
                            frequencyPreset === fp.id ? 'bg-purple-500/10 border-purple-500/40 text-white' : 'bg-[#050508] border-white/5 text-gray-400'
                          }`}
                        >
                          <div className="flex items-center space-x-2">
                            <input
                              type="radio"
                              name="freq"
                              checked={frequencyPreset === fp.id}
                              onChange={() => setFrequencyPreset(fp.id)}
                              className="accent-purple-500"
                            />
                            <span className="font-bold">{fp.label}</span>
                          </div>
                          <span className="text-[11px] font-mono text-gray-400">{fp.type === 'cron' ? fp.cron : `${fp.seconds}s`}</span>
                        </label>
                      ))}
                    </div>

                    {frequencyPreset === 'custom_cron' && (
                      <div className="pt-2">
                        <label className="text-gray-300 font-bold block mb-1">Custom Cron Expression</label>
                        <input
                          type="text"
                          placeholder="e.g. 0 */4 * * *"
                          value={customCron}
                          onChange={(e) => setCustomCron(e.target.value)}
                          className="w-full bg-[#050508] border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-purple-500"
                        />
                      </div>
                    )}
                  </div>
                )}

                {/* Navigation Controls */}
                <div className="flex items-center justify-between pt-4 border-t border-white/10">
                  {step > 1 ? (
                    <button
                      type="button"
                      onClick={() => setStep(step - 1)}
                      className="px-4 py-2 rounded-xl text-gray-300 hover:text-white font-bold cursor-pointer"
                    >
                      Back
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={() => setWizardOpen(false)}
                      className="px-4 py-2 rounded-xl text-gray-400 hover:text-white font-bold cursor-pointer"
                    >
                      Cancel
                    </button>
                  )}

                  {step < 5 ? (
                    <button
                      type="button"
                      onClick={() => setStep(step + 1)}
                      className="bg-purple-600 hover:bg-purple-500 text-white px-5 py-2 rounded-xl font-bold cursor-pointer shadow-[0_0_15px_rgba(168,85,247,0.3)]"
                    >
                      Next Step &rarr;
                    </button>
                  ) : (
                    <button
                      type="submit"
                      disabled={saving}
                      className="bg-emerald-500 hover:bg-emerald-400 text-black px-5 py-2 rounded-xl font-bold cursor-pointer shadow-[0_0_15px_rgba(16,185,129,0.3)]"
                    >
                      {saving ? 'Saving...' : 'Save & Enable Schedule'}
                    </button>
                  )}
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  )
}
