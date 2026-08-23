import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Webhook, Plus, Trash2, Send, CheckCircle2, AlertCircle, Copy, Check, Eye, EyeOff, Code, RefreshCw, Activity, Terminal } from 'lucide-react'
import apiClient from '../apiClient'
import { API_BASE_URL } from '../config'
import toast from 'react-hot-toast'

const EVENT_TYPES = [
  { id: 'migration.completed', label: 'Migration Completed', desc: 'Triggered when a migration pipeline finishes successfully.' },
  { id: 'migration.failed', label: 'Migration Failed', desc: 'Triggered when a migration job encounters an error or aborts.' },
  { id: 'migration.started', label: 'Migration Started', desc: 'Triggered immediately when a new migration pipeline initializes.' },
]

const PYTHON_VERIFY_SNIPPET = `import hmac
import hashlib
from fastapi import Request, HTTPException

WEBHOOK_SECRET = "your_webhook_secret_here"

def verify_fluxline_signature(raw_body: bytes, signature_header: str) -> bool:
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected_sig = signature_header.split("sha256=")[1]
    computed_sig = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'),
        raw_body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(computed_sig, expected_sig)
`

export default function Webhooks() {
  const [webhooks, setWebhooks] = useState([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [copiedSecretId, setCopiedSecretId] = useState(null)
  const [visibleSecrets, setVisibleSecrets] = useState({})
  
  // Form State
  const [url, setUrl] = useState('')
  const [selectedEvents, setSelectedEvents] = useState(['migration.completed', 'migration.failed'])
  const [secret, setSecret] = useState('')
  const [saving, setSaving] = useState(false)
  const [testingId, setTestingId] = useState(null)

  useEffect(() => {
    fetchWebhooks()
  }, [])

  const fetchWebhooks = async () => {
    setLoading(true)
    try {
      const res = await apiClient.fetchWithAuth(`${API_BASE_URL}/api/webhooks`)
      if (res.ok) {
        const data = await res.json()
        setWebhooks(data)
      } else {
        toast.error('Failed to load webhooks')
      }
    } catch (e) {
      console.error(e)
      toast.error('Error fetching webhooks')
    } finally {
      setLoading(false)
    }
  }

  const handleToggleEvent = (eventId) => {
    if (selectedEvents.includes(eventId)) {
      setSelectedEvents(selectedEvents.filter(e => e !== eventId))
    } else {
      setSelectedEvents([...selectedEvents, eventId])
    }
  }

  const handleCreateWebhook = async (e) => {
    e.preventDefault()
    if (!url.trim()) {
      toast.error('Webhook URL is required')
      return
    }
    if (selectedEvents.length === 0) {
      toast.error('Select at least one event subscription')
      return
    }

    setSaving(true)
    try {
      const res = await apiClient.fetchWithAuth(`${API_BASE_URL}/api/webhooks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: url.trim(),
          events: selectedEvents,
          secret: secret.trim() || undefined,
          enabled: true
        })
      })
      if (res.ok) {
        toast.success('Webhook registered successfully')
        setModalOpen(false)
        setUrl('')
        setSecret('')
        fetchWebhooks()
      } else {
        toast.error('Failed to register webhook')
      }
    } catch (err) {
      toast.error('Network error creating webhook')
    } finally {
      setSaving(false)
    }
  }

  const handleToggleEnabled = async (wh) => {
    try {
      const res = await apiClient.fetchWithAuth(`${API_BASE_URL}/api/webhooks/${wh.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: !wh.enabled })
      })
      if (res.ok) {
        toast.success(`Webhook ${!wh.enabled ? 'enabled' : 'disabled'}`)
        fetchWebhooks()
      }
    } catch (e) {
      toast.error('Failed to update status')
    }
  }

  const handleDeleteWebhook = async (id) => {
    if (!confirm('Are you sure you want to delete this webhook endpoint?')) return
    try {
      const res = await apiClient.fetchWithAuth(`${API_BASE_URL}/api/webhooks/${id}`, {
        method: 'DELETE'
      })
      if (res.ok) {
        toast.success('Webhook deleted')
        fetchWebhooks()
      }
    } catch (e) {
      toast.error('Error deleting webhook')
    }
  }

  const handleTestWebhook = async (id) => {
    setTestingId(id)
    try {
      const res = await apiClient.fetchWithAuth(`${API_BASE_URL}/api/webhooks/${id}/test`, {
        method: 'POST'
      })
      if (res.ok) {
        const data = await res.json()
        toast.success(`Test ping dispatched! Status: ${data.delivery_result.status}`)
        fetchWebhooks()
      } else {
        toast.error('Test payload failed to deliver')
      }
    } catch (e) {
      toast.error('Error executing test ping')
    } finally {
      setTestingId(null)
    }
  }

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text)
    setCopiedSecretId(id)
    setTimeout(() => setCopiedSecretId(null), 1500)
  }

  const toggleSecretVisibility = (id) => {
    setVisibleSecrets(prev => ({ ...prev, [id]: !prev[id] }))
  }

  return (
    <div className="p-8 max-w-[1600px] mx-auto w-full flex flex-col space-y-6 min-h-full">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 shrink-0">
        <div>
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
              <Webhook className="w-5 h-5" />
            </div>
            <h1 className="font-sans text-h1 font-bold text-text-primary tracking-tight">
              Async Webhook Notifications
            </h1>
          </div>
          <p className="text-muted-slate text-sm mt-1.5 font-mono">
            Register HTTP endpoints to receive HMAC-SHA256 signed event payloads upon migration completion or failure.
          </p>
        </div>
        <button
          onClick={() => setModalOpen(true)}
          className="bg-purple-600 hover:bg-purple-500 text-white px-5 py-2.5 rounded-xl font-mono text-xs font-bold transition-all flex items-center shadow-[0_0_20px_rgba(168,85,247,0.3)] cursor-pointer"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Webhook Endpoint
        </button>
      </div>

      {/* Main Content Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 min-h-0">
        
        {/* Left Column: Registered Webhook Cards */}
        <div className="lg:col-span-2 flex flex-col space-y-4 overflow-y-auto pr-1">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-text-primary font-mono flex items-center">
              <Activity className="w-4 h-4 mr-2 text-purple-400" />
              Configured Endpoints ({webhooks.length})
            </h2>
            <button 
              onClick={fetchWebhooks}
              className="text-xs font-mono text-gray-400 hover:text-white flex items-center cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 mr-1 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>

          {loading ? (
            <div className="p-12 text-center text-gray-400 font-mono bg-white/[0.02] border border-white/5 rounded-2xl">
              Loading endpoints...
            </div>
          ) : webhooks.length === 0 ? (
            <div className="p-12 text-center border border-dashed border-white/10 rounded-2xl bg-white/[0.02]">
              <Webhook className="w-12 h-12 text-gray-500 mx-auto mb-3" />
              <h3 className="text-base font-bold text-white font-mono">No Webhooks Registered</h3>
              <p className="text-xs text-gray-400 font-mono mt-1 max-w-md mx-auto">
                Connect external notification channels (Slack, PagerDuty, custom APIs) to receive instant updates when migrations finish.
              </p>
              <button
                onClick={() => setModalOpen(true)}
                className="mt-4 bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/40 px-4 py-2 rounded-xl text-xs font-mono font-bold cursor-pointer"
              >
                Add First Endpoint
              </button>
            </div>
          ) : (
            webhooks.map(wh => (
              <div key={wh.id} className="glass-panel rounded-2xl p-5 relative">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
                  <div className="flex items-center space-x-3 overflow-hidden">
                    <span className={`w-3 h-3 rounded-full shrink-0 ${wh.enabled ? 'bg-emerald-400 shadow-[0_0_10px_rgba(16,185,129,0.5)]' : 'bg-gray-500'}`} />
                    <span className="font-mono text-sm font-bold text-white truncate max-w-md" title={wh.url}>
                      {wh.url}
                    </span>
                  </div>

                  <div className="flex items-center space-x-2 shrink-0">
                    <button
                      onClick={() => handleToggleEnabled(wh)}
                      className={`px-3 py-1 rounded-lg text-xs font-mono font-bold border transition-colors cursor-pointer ${
                        wh.enabled 
                          ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' 
                          : 'bg-gray-500/10 border-gray-500/30 text-gray-400'
                      }`}
                    >
                      {wh.enabled ? 'ENABLED' : 'PAUSED'}
                    </button>
                    <button
                      onClick={() => handleTestWebhook(wh.id)}
                      disabled={testingId === wh.id}
                      className="bg-purple-500/10 hover:bg-purple-500/20 text-purple-300 border border-purple-500/30 px-3 py-1 rounded-lg text-xs font-mono font-bold transition-colors cursor-pointer flex items-center"
                    >
                      <Send className={`w-3.5 h-3.5 mr-1.5 ${testingId === wh.id ? 'animate-pulse' : ''}`} />
                      {testingId === wh.id ? 'Testing...' : 'Test Ping'}
                    </button>
                    <button
                      onClick={() => handleDeleteWebhook(wh.id)}
                      className="p-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 transition-colors cursor-pointer"
                      title="Delete Endpoint"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {/* Secret & Subscriptions Info */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-3 border-t border-white/10 text-xs font-mono">
                  <div>
                    <span className="text-gray-400 block mb-1">Subscribed Events:</span>
                    <div className="flex flex-wrap gap-1.5">
                      {(wh.events || '').split(',').map(evt => (
                        <span key={evt} className="px-2 py-0.5 rounded bg-white/5 border border-white/10 text-purple-300 text-[11px]">
                          {evt}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div>
                    <span className="text-gray-400 block mb-1">HMAC Secret:</span>
                    <div className="flex items-center space-x-2 bg-[#050508] border border-white/10 rounded-lg px-2.5 py-1">
                      <span className="text-gray-300 truncate">
                        {visibleSecrets[wh.id] ? wh.secret : '••••••••••••••••••••'}
                      </span>
                      <button 
                        onClick={() => toggleSecretVisibility(wh.id)}
                        className="text-gray-400 hover:text-white cursor-pointer ml-auto"
                      >
                        {visibleSecrets[wh.id] ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                      </button>
                      <button 
                        onClick={() => copyToClipboard(wh.secret, wh.id)}
                        className="text-gray-400 hover:text-white cursor-pointer"
                      >
                        {copiedSecretId === wh.id ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Delivery Status Badge */}
                {wh.last_delivery && (
                  <div className="mt-3 flex items-center justify-between text-[11px] font-mono text-gray-400 bg-white/[0.02] px-3 py-1.5 rounded-lg border border-white/5">
                    <span>Last delivery attempt: {new Date(wh.last_delivery).toLocaleString()}</span>
                    <span className={`font-bold ${wh.last_status?.includes('200') ? 'text-emerald-400' : 'text-amber-400'}`}>
                      {wh.last_status}
                    </span>
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        {/* Right Column: Code Snippet Block for Verification */}
        <div className="lg:col-span-1 glass-panel rounded-2xl p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-base font-bold text-text-primary font-mono flex items-center">
                <Code className="w-4 h-4 mr-2 text-purple-400" />
                Signature Verification
              </h2>
              <span className="text-[10px] font-mono text-purple-300 bg-purple-500/10 px-2 py-0.5 rounded border border-purple-500/30">
                HMAC-SHA256
              </span>
            </div>
            <p className="text-xs text-gray-400 font-mono mb-3">
              Every request contains header <code>X-Fluxline-Signature: sha256=...</code>. Verify payloads with python:
            </p>

            <pre className="bg-[#050508] border border-white/10 rounded-xl p-3 font-mono text-[11px] text-purple-200 overflow-x-auto custom-scrollbar leading-relaxed">
              {PYTHON_VERIFY_SNIPPET}
            </pre>
          </div>
        </div>
      </div>

      {/* Modal for Adding Webhook */}
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
                <Webhook className="w-5 h-5 mr-2 text-purple-400" />
                Register Webhook Endpoint
              </h3>

              <form onSubmit={handleCreateWebhook} className="space-y-4 font-mono text-xs">
                <div>
                  <label className="text-gray-300 font-bold block mb-1">Target Endpoint URL</label>
                  <input
                    type="url"
                    placeholder="https://api.yourdomain.com/webhooks/fluxline"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    className="w-full bg-[#050508] border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-purple-500"
                    required
                  />
                </div>

                <div>
                  <label className="text-gray-300 font-bold block mb-1">Event Subscriptions</label>
                  <div className="space-y-2 mt-1">
                    {EVENT_TYPES.map(evt => (
                      <label 
                        key={evt.id} 
                        className={`flex items-start space-x-2.5 p-2.5 rounded-xl border cursor-pointer transition-colors ${
                          selectedEvents.includes(evt.id)
                            ? 'bg-purple-500/10 border-purple-500/40 text-white'
                            : 'bg-[#050508] border-white/5 text-gray-400'
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={selectedEvents.includes(evt.id)}
                          onChange={() => handleToggleEvent(evt.id)}
                          className="mt-0.5 rounded border-white/10 accent-purple-500"
                        />
                        <div>
                          <span className="font-bold text-xs text-white block">{evt.label}</span>
                          <span className="text-[11px] text-gray-400 block mt-0.5">{evt.desc}</span>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="text-gray-300 font-bold block mb-1">Custom Secret (Optional)</label>
                  <input
                    type="text"
                    placeholder="Leave empty for auto-generated secret"
                    value={secret}
                    onChange={(e) => setSecret(e.target.value)}
                    className="w-full bg-[#050508] border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-purple-500"
                  />
                </div>

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
                    {saving ? 'Registering...' : 'Register Webhook'}
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
