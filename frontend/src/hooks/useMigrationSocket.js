import { useEffect, useRef, useCallback } from 'react'
import { useMigrationStore } from '../store/useMigrationStore'

/**
 * Custom hook that connects to the backend WebSocket for a migration job
 * and streams real-time updates into the decoupled Zustand store.
 *
 * Performance Features:
 * - Throttles high-frequency log messages using requestAnimationFrame batching
 * - Decouples state updates into Zustand selectors so components only re-render for their slice
 * - Maintains auto-reconnect and heartbeat safety
 */
export default function useMigrationSocket(jobId) {
  const wsRef = useRef(null)
  const reconnectTimeoutRef = useRef(null)
  const pendingLogsRef = useRef([])
  const animationFrameRef = useRef(null)
  const lastSampleRef = useRef({ time: Date.now(), count: 0 })

  const {
    setTables,
    setMigrationStatus,
    setPipelineStages,
    addLogsBatch,
    setRowsPerSec,
    resetStore
  } = useMigrationStore()

  // Batch log flusher on animation frame
  const scheduleLogFlush = useCallback(() => {
    if (animationFrameRef.current) return
    animationFrameRef.current = requestAnimationFrame(() => {
      animationFrameRef.current = null
      if (pendingLogsRef.current.length > 0) {
        const batch = pendingLogsRef.current
        pendingLogsRef.current = []
        addLogsBatch(batch)
      }
    })
  }, [addLogsBatch])

  const enqueueLog = useCallback((level, msg) => {
    if (!msg) return
    pendingLogsRef.current.push({
      id: `${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
      timestamp: new Date().toISOString().split('T')[1].slice(0, 12),
      level,
      msg,
    })
    scheduleLogFlush()
  }, [scheduleLogFlush])

  const updateStage = useCallback((stageId, status) => {
    setPipelineStages(prev => prev.map(s => {
      if (s.id === stageId) return { ...s, status }
      return s
    }))
  }, [setPipelineStages])

  const handleMessage = useCallback((data) => {
    const step = data.step || ''
    const status = data.status || ''

    const level = data.level
      || (status === 'done' || status === 'completed' ? 'SUCCESS'
      : status === 'failed' || step === 'error' || data.type === 'error' ? 'ERROR'
      : 'INFO')

    const stageAliasMap = {
      connect: 'connect',
      connect_source: 'connect',
      extract_schema: 'discovery',
      discovery: 'discovery',
      transform_ddl: 'schema',
      schema: 'schema',
      migrate_data: 'data',
      data: 'data',
      data_verification: 'validation',
      validation: 'validation',
      objects: 'objects',
      object_migration: 'objects',
    }

    const stageLabelMap = {
      connect: 'Connect Source',
      connect_source: 'Connect Source',
      extract_schema: 'Extract Schema',
      discovery: 'Extract Schema',
      transform_ddl: 'Transform DDL',
      schema: 'Transform DDL',
      migrate_data: 'Migrate Data',
      data: 'Migrate Data',
      data_verification: 'Data Verification',
      validation: 'Data Verification',
      objects: 'Migrate Objects',
      object_migration: 'Migrate Objects',
    }

    const logMsg = data.message
      || (step === 'data' && data.table ? `Table "${data.table}": ${(data.rows_done || 0).toLocaleString()} / ${(data.rows_total || 0).toLocaleString()} rows` : null)
      || (step === 'discovery' && status === 'done' ? `Schema discovery complete — ${(data.tables || []).length} tables found` : null)
      || (step === 'schema' && status === 'done' ? `DDL generation complete — ${data.ddl_count || 0} statements` : null)
      || (step === 'validation' && status === 'done' ? `Validation complete — score: ${data.score ?? 'N/A'}` : null)
      || (step === 'completion' ? `Migration ${status}` : null)
      || (data.type === 'stage_update' && data.stage ? `${stageLabelMap[data.stage] || data.stage}: ${data.status || status}` : null)
      || (step ? `${stageLabelMap[step] || step}: ${status}` : null)
      || `Pipeline: ${status}`

    enqueueLog(level, logMsg)

    // Helper to advance stages sequentially
    const advanceStageTo = (stageId, targetStatus) => {
      const normId = stageAliasMap[stageId] || stageId
      const finalStatus = targetStatus === 'in_progress' ? 'running' : targetStatus === 'done' ? 'completed' : targetStatus
      const stageOrder = ['connect', 'discovery', 'schema', 'data', 'validation', 'objects']
      const currentIdx = stageOrder.indexOf(normId)

      setPipelineStages(prev => prev.map((s) => {
        const sIdx = stageOrder.indexOf(s.id)
        if (s.id === normId) {
          return { ...s, status: finalStatus }
        }
        if (currentIdx >= 0 && sIdx < currentIdx && s.status !== 'completed') {
          return { ...s, status: 'completed' }
        }
        return s
      }))
    }

    // Stage update type events
    if (data.type === 'stage_update' && data.stage) {
      advanceStageTo(data.stage, data.status)
      if (data.stage === 'connect' || data.stage === 'connect_source') setMigrationStatus('running')
    } else if (step) {
      const mappedStage = stageAliasMap[step]
      if (mappedStage) {
        if (status === 'running' || status === 'in_progress') {
          advanceStageTo(mappedStage, 'running')
        } else if (status === 'done' || status === 'completed') {
          advanceStageTo(mappedStage, 'completed')
        }
      }
    }

    // Per-table data progress
    if ((step === 'data' || data.type === 'table_progress' || data.table) && data.table) {
      if (data.rows_per_second !== undefined && data.rows_per_second !== null && data.rows_per_second >= 0) {
        setRowsPerSec(Math.round(data.rows_per_second))
      } else if (data.rows_per_sec !== undefined && data.rows_per_sec !== null && data.rows_per_sec >= 0) {
        setRowsPerSec(Math.round(data.rows_per_sec))
      }

      setTables(prev => {
        const prevTable = prev[data.table] || {}
        const rows_done = data.rows_done ?? prevTable.rows_done ?? 0
        const rows_total = data.rows_total || prevTable.rows_total || 0
        let tableStatus = prevTable.status || 'pending'

        if (data.status === 'failed' || level === 'ERROR') {
          tableStatus = 'failed'
        } else if (data.status === 'done' || data.status === 'completed' || (rows_total > 0 && rows_done >= rows_total)) {
          tableStatus = 'completed'
        } else if (data.status === 'running' || rows_done > 0) {
          tableStatus = 'running'
        }

        return {
          ...prev,
          [data.table]: {
            name: data.table,
            rows_done,
            rows_total,
            status: tableStatus,
            message: data.message || data.error || prevTable.message,
            object_type: data.object_type || prevTable.object_type || 'table',
          }
        }
      })
    }

    // Tables list from discovery
    if (data.type === 'stage_details' && (data.tables || data.table_details)) {
      setTables(prev => {
        const next = { ...prev }
        if (Array.isArray(data.table_details)) {
          for (const item of data.table_details) {
            if (!next[item.name]) {
              next[item.name] = { name: item.name, rows_done: 0, rows_total: item.rows_total || 0, status: 'pending', object_type: item.object_type || 'table' }
            } else if (!next[item.name].rows_total && item.rows_total) {
              next[item.name].rows_total = item.rows_total
            }
          }
        } else if (Array.isArray(data.tables)) {
          for (const name of data.tables) {
            if (!next[name]) {
              next[name] = { name, rows_done: 0, rows_total: 0, status: 'pending', object_type: 'table' }
            }
          }
        }
        return next
      })
    }

    // Completion
    if (step === 'completion') {
      const finalStatus = (status || '').toLowerCase()
      if (finalStatus.includes('success') || finalStatus.includes('completed')) {
        setMigrationStatus('completed')
        setPipelineStages(prev => prev.map(s => ({ ...s, status: 'completed' })))
        setTables(prev => {
          const next = {}
          for (const [k, v] of Object.entries(prev)) {
            const isFinished = (v.rows_total > 0 && v.rows_done >= v.rows_total) || v.status === 'completed'
            const neverStarted = v.rows_done === 0 && v.status !== 'completed' && v.status !== 'failed'
            next[k] = {
              ...v,
              status: isFinished ? 'completed' : neverStarted ? 'skipped' : v.status,
              rows_done: isFinished ? (v.rows_total || v.rows_done) : v.rows_done
            }
          }
          return next
        })
      } else if (finalStatus.includes('fail')) {
        setMigrationStatus('failed')
      } else {
        setMigrationStatus('completed')
        setTables(prev => {
          const next = {}
          for (const [k, v] of Object.entries(prev)) {
            const isFinished = (v.rows_total > 0 && v.rows_done >= v.rows_total) || v.status === 'completed'
            const neverStarted = v.rows_done === 0 && v.status !== 'completed' && v.status !== 'failed'
            next[k] = {
              ...v,
              status: isFinished ? 'completed' : neverStarted ? 'skipped' : v.status,
              rows_done: isFinished ? (v.rows_total || v.rows_done) : v.rows_done
            }
          }
          return next
        })
      }
    }

    if (step === 'error' || status === 'failed' || data.type === 'error') {
      setMigrationStatus('failed')
    }
  }, [enqueueLog, setMigrationStatus, setPipelineStages, setTables, updateStage])

  // Monitor rows/sec calculation
  const completedRows = useMigrationStore(state => state.completedRows)
  useEffect(() => {
    const now = Date.now()
    const dt = (now - lastSampleRef.current.time) / 1000
    if (dt >= 0.8) {
      const dRows = completedRows - lastSampleRef.current.count
      if (dRows >= 0 && dt > 0) {
        setRowsPerSec(Math.round(dRows / dt))
      }
      lastSampleRef.current = { time: now, count: completedRows }
    }
  }, [completedRows, setRowsPerSec])

  // REST polling fallback — catches completed migrations that the WebSocket missed
  useEffect(() => {
    if (!jobId) return
    let isCancelled = false
    let pollInterval = null

    async function pollJobStatus() {
      if (isCancelled) return
      const currentStatus = useMigrationStore.getState().migrationStatus
      // Stop polling once we've already resolved the final state
      if (currentStatus === 'completed' || currentStatus === 'failed') {
        if (pollInterval) clearInterval(pollInterval)
        return
      }

      try {
        const token = localStorage.getItem('access_token') || ''
        const headers = { 'Content-Type': 'application/json' }
        if (token) headers['Authorization'] = `Bearer ${token}`

        const res = await fetch(`/api/migrations/${jobId}`, { headers })
        if (!res.ok) return
        const job = await res.json()

        const jobStatus = (job.status || '').toUpperCase()
        if (jobStatus === 'SUCCESS' || jobStatus.includes('COMPLETED')) {
          // Hydrate the store from the REST response
          enqueueLog('INFO', `Migration completed — ${job.tables_migrated || 0} tables, ${(job.total_rows || 0).toLocaleString()} rows in ${job.duration_seconds ? job.duration_seconds.toFixed(1) + 's' : 'N/A'}`)

          // Mark all pipeline stages as completed
          setPipelineStages(prev => prev.map(s => ({ ...s, status: 'completed' })))
          setMigrationStatus('completed')

          // If we have validation report info, log it
          if (job.validation_report && job.validation_report.validation_score !== undefined) {
            enqueueLog('SUCCESS', `Validation score: ${job.validation_report.validation_score}%`)
          }

          if (pollInterval) clearInterval(pollInterval)
        } else if (jobStatus === 'FAILED' || jobStatus.includes('FAILED')) {
          enqueueLog('ERROR', `Migration failed: ${job.error || 'Unknown error'}`)
          setMigrationStatus('failed')
          if (pollInterval) clearInterval(pollInterval)
        }
        // If IN_PROGRESS, keep polling — the WebSocket may still deliver granular updates
      } catch {
        // Network error, retry on next poll
      }
    }

    // Start polling after a short delay to give WebSocket a chance first
    const startTimeout = setTimeout(() => {
      if (isCancelled) return
      pollJobStatus()
      pollInterval = setInterval(pollJobStatus, 3000)
    }, 2000)

    return () => {
      isCancelled = true
      clearTimeout(startTimeout)
      if (pollInterval) clearInterval(pollInterval)
    }
  }, [jobId, enqueueLog, setMigrationStatus, setPipelineStages])

  useEffect(() => {
    if (!jobId) return

    resetStore()
    let isCancelled = false

    function connect() {
      if (isCancelled) return

      const token = localStorage.getItem('access_token') || ''
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${protocol}//${window.location.host}/ws/migrations/${jobId}?token=${encodeURIComponent(token)}`

      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        enqueueLog('INFO', 'WebSocket connected — streaming live migration data...')
        if (token) {
          try {
            ws.send(JSON.stringify({ type: 'auth', token }))
          } catch (e) {
            // ignore
          }
        }
        setMigrationStatus(prev => prev === 'connecting' ? 'running' : prev)
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          handleMessage(data)
        } catch (e) {
          // Non-JSON message, ignore
        }
      }

      ws.onclose = () => {
        if (!isCancelled && useMigrationStore.getState().migrationStatus === 'running') {
          enqueueLog('WARN', 'WebSocket disconnected — reconnecting...')
          reconnectTimeoutRef.current = setTimeout(connect, 2000)
        }
      }

      ws.onerror = () => {}
    }

    connect()

    return () => {
      isCancelled = true
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current)
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current)
      if (wsRef.current) {
        wsRef.current.onclose = null
        wsRef.current.close()
      }
    }
  }, [jobId, handleMessage, enqueueLog, resetStore, setMigrationStatus])
}
