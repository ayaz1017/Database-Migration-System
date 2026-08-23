import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ShieldCheck, Plus, Trash2, Edit3, Eye, Play, CheckCircle2, Lock, Table, Sparkles, AlertCircle, RefreshCw, Layers } from 'lucide-react'
import apiClient from '../apiClient'
import { API_BASE_URL } from '../config'
import toast from 'react-hot-toast'

const MASKING_TYPES = [
  { value: 'email', label: 'Email Address', desc: 'john@example.com -> user_a83f@faker.net' },
  { value: 'name', label: 'Full Name', desc: 'John Doe -> Jane Smith' },
  { value: 'first_name', label: 'First Name', desc: 'Alexander -> Robert' },
  { value: 'last_name', label: 'Last Name', desc: 'Hamilton -> Johnson' },
  { value: 'phone', label: 'Phone Number', desc: '+1-555-0199 -> +1-800-555-0142' },
  { value: 'ssn', label: 'Social Security Number', desc: 'XXX-XX-XXXX -> 987-65-4321' },
  { value: 'address', label: 'Street Address', desc: '123 Main St -> 742 Evergreen Terrace' },
  { value: 'ip', label: 'IP Address', desc: '192.168.1.1 -> 172.16.254.1' },
  { value: 'credit_card', label: 'Credit Card Number', desc: '4532-XXXX-XXXX-8921 -> 4012-8839...' },
  { value: 'date', label: 'Date of Birth / Date', desc: '1990-05-15 -> 1985-11-20' },
  { value: 'random_string', label: 'Random String', desc: 'Secret123 -> K9xL2pQ8m' },
  { value: 'null', label: 'Set to NULL', desc: 'Value -> null' },
  { value: 'fixed_value', label: 'Fixed Replacement', desc: '[REDACTED] or Custom String' },
  { value: 'hash', label: 'SHA-256 Hash Prefix', desc: 'john@example.com -> e3b0c44298fc1c14' },
]

export default function DataMasking() {
  const [rules, setRules] = useState([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingRule, setEditingRule] = useState(null)
  
  // Form State
  const [tableName, setTableName] = useState('')
  const [columnName, setColumnName] = useState('')
  const [maskingType, setMaskingType] = useState('email')
  const [fixedValue, setFixedValue] = useState('')
  const [saving, setSaving] = useState(false)

  // Live Sandbox Preview State
  const [sampleData, setSampleData] = useState(
    JSON.stringify({ email: 'alex.smith@company.com', full_name: 'Alex Smith', ssn: '900-12-3456', credit_card: '4532-1100-8842-1200' }, null, 2)
  )
  const [previewResult, setPreviewResult] = useState(null)
  const [previewing, setPreviewing] = useState(false)

  useEffect(() => {
    fetchRules()
  }, [])

  const fetchRules = async () => {
    setLoading(true)
    try {
      const res = await apiClient.fetchWithAuth(`${API_BASE_URL}/api/masking-rules`)
      if (res.ok) {
        const data = await res.json()
        setRules(data)
      } else {
        toast.error('Failed to load masking rules')
      }
    } catch (e) {
      console.error(e)
      toast.error('Error fetching masking rules')
    } finally {
      setLoading(false)
    }
  }

  const handleOpenCreateModal = () => {
    setEditingRule(null)
    setTableName('')
    setColumnName('')
    setMaskingType('email')
    setFixedValue('')
    setModalOpen(true)
  }

  const handleOpenEditModal = (rule) => {
    setEditingRule(rule)
    setTableName(rule.table_name)
    setColumnName(rule.column_name)
    setMaskingType(rule.masking_type)
    setFixedValue(rule.fixed_value || '')
    setModalOpen(true)
  }

  const handleSaveRule = async (e) => {
    e.preventDefault()
    if (!tableName.trim() || !columnName.trim()) {
      toast.error('Table name and column name are required')
      return
    }

    setSaving(true)
    try {
      if (editingRule) {
        const res = await apiClient.fetchWithAuth(`${API_BASE_URL}/api/masking-rules/${editingRule.id}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            table_name: tableName.trim(),
            column_name: columnName.trim(),
            masking_type: maskingType,
            fixed_value: maskingType === 'fixed_value' ? fixedValue : null
          })
        })
        if (res.ok) {
          toast.success('Masking rule updated successfully')
          setModalOpen(false)
          fetchRules()
        } else {
          toast.error('Failed to update masking rule')
        }
      } else {
        const res = await apiClient.fetchWithAuth(`${API_BASE_URL}/api/masking-rules`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            table_name: tableName.trim(),
            column_name: columnName.trim(),
            masking_type: maskingType,
            fixed_value: maskingType === 'fixed_value' ? fixedValue : null
          })
        })
        if (res.ok) {
          toast.success('Masking rule created successfully')
          setModalOpen(false)
          fetchRules()
        } else {
          toast.error('Failed to create masking rule')
        }
      }
    } catch (err) {
      toast.error('Network error while saving rule')
    } finally {
      setSaving(false)
    }
  }

  const handleDeleteRule = async (id) => {
    if (!confirm('Are you sure you want to delete this masking rule?')) return
    try {
      const res = await apiClient.fetchWithAuth(`${API_BASE_URL}/api/masking-rules/${id}`, {
        method: 'DELETE'
      })
      if (res.ok) {
        toast.success('Masking rule deleted')
        fetchRules()
      } else {
        toast.error('Failed to delete masking rule')
      }
    } catch (e) {
      toast.error('Error deleting rule')
    }
  }

  const handleTestPreview = async () => {
    setPreviewing(true)
    try {
      let parsedRow = {}
      try {
        parsedRow = JSON.parse(sampleData)
      } catch (err) {
        toast.error('Invalid JSON sample data input')
        setPreviewing(false)
        return
      }

      // Convert current active rules into preview payload format
      const activeRules = rules.map(r => ({
        column_name: r.column_name,
        masking_type: r.masking_type,
        fixed_value: r.fixed_value
      }))

      const res = await apiClient.fetchWithAuth(`${API_BASE_URL}/api/masking-rules/preview`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sample_row: parsedRow,
          rules: activeRules
        })
      })

      if (res.ok) {
        const data = await res.json()
        setPreviewResult(data.masked)
        toast.success('Transformation preview generated')
      } else {
        toast.error('Failed to generate preview')
      }
    } catch (e) {
      toast.error('Error executing preview')
    } finally {
      setPreviewing(false)
    }
  }

  // Group rules by table
  const rulesByTable = rules.reduce((acc, r) => {
    if (!acc[r.table_name]) acc[r.table_name] = []
    acc[r.table_name].push(r)
    return acc
  }, {})

  const tableNames = Object.keys(rulesByTable)

  return (
    <div className="p-8 max-w-[1600px] mx-auto w-full flex flex-col space-y-6 min-h-full">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 shrink-0">
        <div>
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h1 className="font-sans text-h1 font-bold text-text-primary tracking-tight">
              Data Masking & PII Anonymization
            </h1>
          </div>
          <p className="text-muted-slate text-sm mt-1.5 font-mono">
            Define opt-in rule-based transformations to redact sensitive PII (emails, SSNs, credit cards) during migration pipelines.
          </p>
        </div>
        <button
          onClick={handleOpenCreateModal}
          className="bg-purple-600 hover:bg-purple-500 text-white px-5 py-2.5 rounded-xl font-mono text-xs font-bold transition-all flex items-center shadow-[0_0_20px_rgba(168,85,247,0.3)] cursor-pointer"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Masking Rule
        </button>
      </div>

      {/* Metrics Banner */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 shrink-0">
        <div className="glass-panel rounded-2xl p-4">
          <span className="text-xs text-gray-400 font-mono uppercase tracking-wider block">Total Active Rules</span>
          <span className="text-2xl font-bold text-text-primary font-mono mt-1 block">{rules.length}</span>
        </div>
        <div className="glass-panel rounded-2xl p-4">
          <span className="text-xs text-gray-400 font-mono uppercase tracking-wider block">Protected Tables</span>
          <span className="text-2xl font-bold text-purple-400 font-mono mt-1 block">{tableNames.length}</span>
        </div>
        <div className="glass-panel rounded-2xl p-4">
          <span className="text-xs text-gray-400 font-mono uppercase tracking-wider block">Anonymization Engine</span>
          <span className="text-2xl font-bold text-emerald-400 font-mono mt-1 block flex items-center">
            <Sparkles className="w-5 h-5 mr-1.5" /> Faker v33.3
          </span>
        </div>
        <div className="glass-panel rounded-2xl p-4">
          <span className="text-xs text-gray-400 font-mono uppercase tracking-wider block">Pipeline Mode</span>
          <span className="text-xs font-mono font-bold text-amber-400 bg-amber-500/10 border border-amber-500/30 px-2.5 py-1 rounded-md inline-block mt-2">
            OPT-IN (Per Job Toggle)
          </span>
        </div>
      </div>

      {/* Main Content Layout: Left = Rules List, Right = Live Sandbox */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 min-h-0">
        
        {/* Left Column: Rules Grouped by Table */}
        <div className="lg:col-span-2 flex flex-col space-y-4 overflow-y-auto pr-1">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-text-primary font-mono flex items-center">
              <Layers className="w-4 h-4 mr-2 text-purple-400" />
              Configured Table Rules ({rules.length})
            </h2>
            <button 
              onClick={fetchRules}
              className="text-xs font-mono text-gray-400 hover:text-white flex items-center cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 mr-1 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>

          {loading ? (
            <div className="p-12 text-center text-gray-400 font-mono bg-white/[0.02] border border-white/5 rounded-2xl">
              Loading rules...
            </div>
          ) : rules.length === 0 ? (
            <div className="p-12 text-center border border-dashed border-white/10 rounded-2xl bg-white/[0.02]">
              <Lock className="w-12 h-12 text-gray-500 mx-auto mb-3" />
              <h3 className="text-base font-bold text-white font-mono">No Masking Rules Configured</h3>
              <p className="text-xs text-gray-400 font-mono mt-1 max-w-md mx-auto">
                Add column rules for your tables (e.g. `users.email` &rarr; `email`) to automatically anonymize sensitive values during migrations.
              </p>
              <button
                onClick={handleOpenCreateModal}
                className="mt-4 bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/40 px-4 py-2 rounded-xl text-xs font-mono font-bold cursor-pointer"
              >
                Create First Rule
              </button>
            </div>
          ) : (
            tableNames.map(tName => (
              <div key={tName} className="bg-[#0c0c14]/90 border border-white/10 rounded-2xl p-5 backdrop-blur-xl glass-panel">
                <div className="flex items-center justify-between border-b border-white/10 pb-3 mb-4">
                  <div className="flex items-center space-x-2">
                    <Table className="w-4 h-4 text-purple-400" />
                    <span className="font-mono text-base font-bold text-white">{tName}</span>
                    <span className="px-2 py-0.5 rounded-full bg-purple-500/10 border border-purple-500/30 text-purple-300 font-mono text-[10px]">
                      {rulesByTable[tName].length} rules
                    </span>
                  </div>
                </div>

                <div className="space-y-3">
                  {rulesByTable[tName].map(rule => (
                    <div 
                      key={rule.id}
                      className="flex items-center justify-between p-3 rounded-xl bg-white/[0.03] border border-white/5 hover:border-purple-500/30 transition-all"
                    >
                      <div className="flex items-center space-x-4">
                        <span className="font-mono text-sm font-semibold text-text-primary">
                          .{rule.column_name}
                        </span>
                        <span className="px-2.5 py-1 rounded-lg bg-white/5 border border-white/10 text-emerald-400 font-mono text-xs font-bold uppercase">
                          {rule.masking_type}
                        </span>
                        {rule.fixed_value && (
                          <span className="text-xs font-mono text-gray-400">
                            value: <code className="text-purple-300">"{rule.fixed_value}"</code>
                          </span>
                        )}
                      </div>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handleOpenEditModal(rule)}
                          className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-gray-300 transition-colors cursor-pointer"
                          title="Edit Rule"
                        >
                          <Edit3 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleDeleteRule(rule.id)}
                          className="p-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 transition-colors cursor-pointer"
                          title="Delete Rule"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Right Column: Interactive Sandbox Preview */}
        <div className="lg:col-span-1 bg-[#0c0c14]/90 border border-white/10 rounded-2xl p-5 backdrop-blur-xl glass-panel flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-bold text-text-primary font-mono flex items-center">
                <Sparkles className="w-4 h-4 mr-2 text-emerald-400" />
                Live Rule Sandbox
              </h2>
              <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/30">
                TEST ENGINE
              </span>
            </div>
            <p className="text-xs text-gray-400 font-mono mb-3">
              Paste a sample row JSON object and click Test to preview how configured rules transform your live data.
            </p>

            <label className="text-xs font-mono text-gray-300 font-bold block mb-1.5">Input Sample Row (JSON)</label>
            <textarea
              value={sampleData}
              onChange={(e) => setSampleData(e.target.value)}
              rows={6}
              className="w-full bg-[#050508] border border-white/10 rounded-xl p-3 font-mono text-xs text-text-primary focus:outline-none focus:border-purple-500 transition-colors resize-none"
            />

            <button
              onClick={handleTestPreview}
              disabled={previewing}
              className="mt-3 w-full bg-emerald-500 hover:bg-emerald-400 text-black font-mono text-xs font-bold py-2.5 rounded-xl transition-all flex items-center justify-center cursor-pointer shadow-[0_0_15px_rgba(16,185,129,0.2)]"
            >
              <Play className="w-4 h-4 mr-2 fill-current" />
              {previewing ? 'Testing Engine...' : 'Run Transformation Preview'}
            </button>

            {previewResult && (
              <div className="mt-4 border-t border-white/10 pt-4">
                <span className="text-xs font-mono text-emerald-400 font-bold block mb-1.5 flex items-center">
                  <CheckCircle2 className="w-3.5 h-3.5 mr-1.5" /> Output Anonymized Result:
                </span>
                <pre className="bg-[#050508] border border-emerald-500/30 rounded-xl p-3 font-mono text-xs text-emerald-300 overflow-x-auto max-h-56 custom-scrollbar">
                  {JSON.stringify(previewResult, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Modal / Slide-Out for Creating / Editing Masking Rule */}
      <AnimatePresence>
        {modalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-[#0e0e18] border border-white/15 rounded-2xl p-6 max-w-md w-full shadow-2xl relative"
            >
              <h3 className="text-lg font-bold text-white font-mono mb-4 flex items-center">
                <ShieldCheck className="w-5 h-5 mr-2 text-purple-400" />
                {editingRule ? 'Edit Masking Rule' : 'Create New Masking Rule'}
              </h3>

              <form onSubmit={handleSaveRule} className="space-y-4 font-mono text-xs">
                <div>
                  <label className="text-gray-300 font-bold block mb-1">Target Table Name</label>
                  <input
                    type="text"
                    placeholder="e.g. users, customers, orders"
                    value={tableName}
                    onChange={(e) => setTableName(e.target.value)}
                    className="w-full bg-[#050508] border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-purple-500"
                    required
                  />
                </div>

                <div>
                  <label className="text-gray-300 font-bold block mb-1">Target Column Name</label>
                  <input
                    type="text"
                    placeholder="e.g. email, ssn, phone_number"
                    value={columnName}
                    onChange={(e) => setColumnName(e.target.value)}
                    className="w-full bg-[#050508] border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-purple-500"
                    required
                  />
                </div>

                <div>
                  <label className="text-gray-300 font-bold block mb-1">Transformation Strategy</label>
                  <select
                    value={maskingType}
                    onChange={(e) => setMaskingType(e.target.value)}
                    className="w-full bg-[#050508] border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-purple-500"
                  >
                    {MASKING_TYPES.map(mt => (
                      <option key={mt.value} value={mt.value}>
                        {mt.label}
                      </option>
                    ))}
                  </select>
                  <p className="text-[11px] text-gray-400 mt-1">
                    {MASKING_TYPES.find(m => m.value === maskingType)?.desc}
                  </p>
                </div>

                {maskingType === 'fixed_value' && (
                  <div>
                    <label className="text-gray-300 font-bold block mb-1">Fixed Replacement Value</label>
                    <input
                      type="text"
                      placeholder="e.g. [REDACTED] or confidential"
                      value={fixedValue}
                      onChange={(e) => setFixedValue(e.target.value)}
                      className="w-full bg-[#050508] border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-purple-500"
                    />
                  </div>
                )}

                <div className="flex items-center justify-end space-x-3 pt-4 border-t border-white/10">
                  <button
                    type="button"
                    onClick={() => setModalOpen(false)}
                    className="px-4 py-2 rounded-xl text-gray-400 hover:text-white font-bold cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={saving}
                    className="bg-purple-600 hover:bg-purple-500 text-white px-5 py-2 rounded-xl font-bold cursor-pointer shadow-[0_0_15px_rgba(168,85,247,0.3)]"
                  >
                    {saving ? 'Saving...' : editingRule ? 'Update Rule' : 'Save Rule'}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  )
}
