import { create } from 'zustand'

const DEFAULT_STAGES = [
  { id: 'connect', label: 'Connect Source', status: 'pending' },
  { id: 'discovery', label: 'Extract Schema', status: 'pending' },
  { id: 'schema', label: 'Transform DDL', status: 'pending' },
  { id: 'data', label: 'Migrate Data', status: 'pending' },
  { id: 'validation', label: 'Data Verification', status: 'pending' },
  { id: 'objects', label: 'Migrate Objects', status: 'pending' },
]

export const useMigrationStore = create((set) => ({
  tables: {},
  migrationStatus: 'connecting', // connecting | running | completed | failed
  pipelineStages: DEFAULT_STAGES,
  logs: [],
  totalRows: 0,
  completedRows: 0,
  overallProgress: 0,
  rowsPerSec: 0,

  // Actions
  setTables: (updater) => set((state) => {
    const nextTables = typeof updater === 'function' ? updater(state.tables) : updater
    const tableList = Object.values(nextTables)
    const totalRows = tableList.reduce((sum, t) => sum + (t.rows_total || 0), 0)
    const completedRows = tableList.reduce((sum, t) => sum + (t.rows_done || 0), 0)
    let overallProgress = totalRows > 0 ? (completedRows / totalRows) * 100 : 0
    if (overallProgress >= 100 && state.migrationStatus !== 'completed') {
      overallProgress = 99
    }
    overallProgress = Math.round(overallProgress * 10) / 10

    return {
      tables: nextTables,
      totalRows,
      completedRows,
      overallProgress,
    }
  }),

  setMigrationStatus: (status) => set((state) => {
    const nextStatus = typeof status === 'function' ? status(state.migrationStatus) : status
    let overallProgress = state.overallProgress
    if (nextStatus === 'completed' && state.totalRows > 0 && state.completedRows >= state.totalRows) {
      overallProgress = 100
    }
    return { migrationStatus: nextStatus, overallProgress }
  }),

  setPipelineStages: (updater) => set((state) => ({
    pipelineStages: typeof updater === 'function' ? updater(state.pipelineStages) : updater
  })),

  addLogsBatch: (newLogEntries) => set((state) => {
    if (!newLogEntries || newLogEntries.length === 0) return state

    let currentLogs = state.logs
    for (const entry of newLogEntries) {
      if (currentLogs.length > 0 && 
          currentLogs[currentLogs.length - 1].msg === entry.msg && 
          currentLogs[currentLogs.length - 1].level === entry.level) {
        continue
      }
      currentLogs = [...currentLogs, entry]
    }

    // Keep last 500 entries in state for terminal buffer
    const cappedLogs = currentLogs.length > 500 ? currentLogs.slice(-500) : currentLogs
    return { logs: cappedLogs }
  }),

  setRowsPerSec: (val) => set({ rowsPerSec: val }),

  resetStore: () => set({
    tables: {},
    migrationStatus: 'connecting',
    pipelineStages: DEFAULT_STAGES,
    logs: [],
    totalRows: 0,
    completedRows: 0,
    overallProgress: 0,
    rowsPerSec: 0,
  })
}))
