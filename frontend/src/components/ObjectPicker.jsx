import { useState, useEffect, memo } from 'react'
import apiClient from '../apiClient'
import { Search, Database, FileCode, CheckSquare, Square, RefreshCw, AlertCircle, Code, Eye, Zap, Info, Layers, Link as LinkIcon, Network } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { API_BASE_URL } from '../config'

const ObjectPicker = ({ sourceConfig, options = {}, onOptionsChange }) => {
  const [activeTab, setActiveTab] = useState('tables')
  const [searchTerm, setSearchTerm] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  const [tables, setTables] = useState([])
  const [objects, setObjects] = useState({
    views: [],
    procedures: [],
    triggers: []
  })

  const [dependencyResolution, setDependencyResolution] = useState(null)
  const [isResolving, setIsResolving] = useState(false)

  // Initialization: fetch tables and objects
  useEffect(() => {
    const discoverAll = async () => {
      setLoading(true)
      try {
        const configParams = new URLSearchParams({
          host: sourceConfig.host,
          port: sourceConfig.port || 0,
          username: sourceConfig.username,
          password: sourceConfig.password,
          db_type: sourceConfig.db_type,
          database: sourceConfig.database
        })

        const [tablesRes, objectsRes] = await Promise.all([
          apiClient.fetchWithAuth(`${API_BASE_URL}/api/discover/tables`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(sourceConfig)
          }),
          apiClient.fetchWithAuth(`${API_BASE_URL}/api/discover/objects`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(sourceConfig)
          })
        ])

        if (!tablesRes.ok) throw new Error(await tablesRes.text())
        
        const tablesData = await tablesRes.json()
        setTables(tablesData.tables || [])
        
        if (objectsRes.ok) {
          const objectsData = await objectsRes.json()
          setObjects(objectsData || { views: [], procedures: [], triggers: [] })
        }
        
        // Default to migrate all tables
        onOptionsChange({
          ...options,
          migrate_all_tables: options.migrate_all_tables !== undefined ? options.migrate_all_tables : true,
          raw_selected_tables: options.raw_selected_tables || [],
          selected_tables: options.selected_tables || [],
          migrate_views: options.migrate_views || false,
          migrate_procedures: options.migrate_procedures || false,
          migrate_triggers: options.migrate_triggers || false,
          selected_views: options.selected_views || [],
          selected_procedures: options.selected_procedures || [],
          selected_triggers: options.selected_triggers || []
        })

      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    if (sourceConfig && sourceConfig.host) discoverAll()
  }, [sourceConfig.db_type, sourceConfig.host, sourceConfig.port, sourceConfig.username, sourceConfig.database])

  // Resolve Dependencies whenever raw selection or mode changes
  useEffect(() => {
    // If migrating all tables, no need to resolve dependencies for subsets
    if (options.migrate_all_tables || !tables.length) {
      setDependencyResolution(null)
      if (options.migrate_all_tables && tables.length > 0) {
        const allTableNames = tables.map(t => t.name)
        if (JSON.stringify(options.selected_tables) !== JSON.stringify(allTableNames)) {
          onOptionsChange(prev => ({ ...prev, selected_tables: allTableNames, raw_selected_tables: [] }))
        }
      }
      return
    }

    const resolveDependencies = async () => {
      setIsResolving(true)
      try {
        const bodyData = {
          config: {
            db_type: sourceConfig.db_type,
            host: sourceConfig.host,
            port: parseInt(sourceConfig.port) || 0,
            username: sourceConfig.username,
            password: sourceConfig.password,
            database: sourceConfig.database
          },
          selected_tables: options.raw_selected_tables || [],
          fk_dependency_mode: options.fk_dependency_mode || 'auto_include'
        }

        const res = await apiClient.fetchWithAuth(`${API_BASE_URL}/api/discover/resolve_dependencies`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(bodyData)
        })
        
        if (res.ok) {
          const resolution = await res.json()
          setDependencyResolution(resolution)
          // Update the final selected_tables in the parent options
          if (JSON.stringify(options.selected_tables) !== JSON.stringify(resolution.final_table_set)) {
            onOptionsChange(prev => ({ ...prev, selected_tables: resolution.final_table_set }))
          }
        }
      } catch (err) {
        console.error("Failed to resolve dependencies", err)
      } finally {
        setIsResolving(false)
      }
    }
    
    if (options.raw_selected_tables) {
       resolveDependencies()
    }
  }, [JSON.stringify(options.raw_selected_tables), options.fk_dependency_mode, options.migrate_all_tables, tables.length])

  // Table selection handlers
  const isTableManuallySelected = (name) => {
    if (options.migrate_all_tables) return true
    return (options.raw_selected_tables || []).includes(name)
  }

  const isTableAutoAdded = (name) => {
    if (options.migrate_all_tables) return false
    return dependencyResolution?.auto_added?.includes(name) || false
  }
  
  const isTableBlocked = (name) => {
    return dependencyResolution?.blocked && dependencyResolution?.missing_dependencies?.includes(name)
  }

  const handleSelectAllTables = (checked) => {
    onOptionsChange({ ...options, migrate_all_tables: checked, raw_selected_tables: [] })
  }

  const handleSelectTable = (name, checked) => {
    let newRaw = [...(options.raw_selected_tables || [])]
    if (options.migrate_all_tables) {
      newRaw = tables.map(t => t.name).filter(t => t !== name)
      onOptionsChange({ ...options, migrate_all_tables: false, raw_selected_tables: newRaw })
      return
    }
    if (checked) {
      if (!newRaw.includes(name)) newRaw.push(name)
    } else {
      newRaw = newRaw.filter(t => t !== name)
    }
    
    if (newRaw.length === tables.length) {
      onOptionsChange({ ...options, migrate_all_tables: true, raw_selected_tables: [] })
    } else {
      onOptionsChange({ ...options, migrate_all_tables: false, raw_selected_tables: newRaw })
    }
  }

  // Object selection handlers
  const isObjectSelected = (type, name) => {
    if (type === 'view') return (options.selected_views || []).includes(name)
    if (type === 'procedure') return (options.selected_procedures || []).includes(name)
    if (type === 'trigger') return (options.selected_triggers || []).includes(name)
    return false
  }

  const handleSelectObject = (type, name, checked) => {
    if (type === 'view') {
      let selected = [...(options.selected_views || [])]
      selected = checked ? [...selected, name] : selected.filter(v => v !== name)
      onOptionsChange({ ...options, selected_views: selected, migrate_views: selected.length > 0 })
    } else if (type === 'procedure') {
      let selected = [...(options.selected_procedures || [])]
      selected = checked ? [...selected, name] : selected.filter(p => p !== name)
      onOptionsChange({ ...options, selected_procedures: selected, migrate_procedures: selected.length > 0 })
    } else if (type === 'trigger') {
      let selected = [...(options.selected_triggers || [])]
      selected = checked ? [...selected, name] : selected.filter(t => t !== name)
      onOptionsChange({ ...options, selected_triggers: selected, migrate_triggers: selected.length > 0 })
    }
  }

  const toggleMigrationType = (type, enabled) => {
    if (type === 'view') {
      onOptionsChange({ ...options, migrate_views: enabled, selected_views: enabled ? objects.views.map(o => o.name) : [] })
    } else if (type === 'procedure') {
      onOptionsChange({ ...options, migrate_procedures: enabled, selected_procedures: enabled ? objects.procedures.map(o => o.name) : [] })
    } else if (type === 'trigger') {
      onOptionsChange({ ...options, migrate_triggers: enabled, selected_triggers: enabled ? objects.triggers.map(o => o.name) : [] })
    }
  }

  const filteredTables = tables.filter(t => t.name.toLowerCase().includes(searchTerm.toLowerCase()))
  const filteredViews = objects.views.filter(o => o.name.toLowerCase().includes(searchTerm.toLowerCase()))
  const filteredProcedures = objects.procedures.filter(o => o.name.toLowerCase().includes(searchTerm.toLowerCase()))
  const filteredTriggers = objects.triggers.filter(o => o.name.toLowerCase().includes(searchTerm.toLowerCase()))

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-[550px] text-muted-slate space-y-4 bg-bg-panel border border-border-card rounded-2xl animate-pulse shadow-xl w-full">
        <RefreshCw className="w-6 h-6 animate-spin text-accent-solid" />
        <p className="font-mono text-xs tracking-wider uppercase text-status-info">Discovering database schemas & assets...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6 bg-status-error-muted border border-status-error-border rounded-xl text-status-error flex items-start space-x-3 shadow-md animate-in fade-in duration-300 w-full">
        <AlertCircle className="w-5 h-5 shrink-0 mt-0.5 text-status-error" />
        <div>
          <h3 className="font-bold text-sm font-display tracking-tight text-stark-white">Asset Discovery Failed</h3>
          <p className="text-xs font-mono mt-1 text-status-error">{error}</p>
        </div>
      </div>
    )
  }

  // Summary computations
  const resolvedCount = options.selected_tables?.length || 0
  const resolvedRows = tables.filter(t => options.selected_tables?.includes(t.name)).reduce((sum, t) => sum + t.row_count, 0)
  const resolvedSizeMB = tables.filter(t => options.selected_tables?.includes(t.name)).reduce((sum, t) => sum + (t.estimated_size_mb || 0), 0)

  let isAllSelected = false;
  let isPartiallySelected = false;
  let selectedCount = 0;
  let totalCount = 0;
  
  if (activeTab === 'tables') {
    isAllSelected = options.migrate_all_tables || (tables.length > 0 && options.selected_tables?.length === tables.length)
    isPartiallySelected = !isAllSelected && options.selected_tables?.length > 0
    selectedCount = resolvedCount
    totalCount = tables.length
  } else if (activeTab === 'views') {
    isAllSelected = options.migrate_views
    selectedCount = options.migrate_views ? (options.selected_views?.length || objects.views.length) : 0
    totalCount = objects.views.length
  } else if (activeTab === 'procedures') {
    isAllSelected = options.migrate_procedures
    selectedCount = options.migrate_procedures ? (options.selected_procedures?.length || objects.procedures.length) : 0
    totalCount = objects.procedures.length
  } else if (activeTab === 'triggers') {
    isAllSelected = options.migrate_triggers
    selectedCount = options.migrate_triggers ? (options.selected_triggers?.length || objects.triggers.length) : 0
    totalCount = objects.triggers.length
  }

  const handleGlobalSelectAll = () => {
    if (activeTab === 'tables') handleSelectAllTables(!isAllSelected)
    else if (activeTab === 'views') toggleMigrationType('view', !isAllSelected)
    else if (activeTab === 'procedures') toggleMigrationType('procedure', !isAllSelected)
    else if (activeTab === 'triggers') toggleMigrationType('trigger', !isAllSelected)
  }

  return (
    <div className="flex flex-col gap-4 w-full h-[550px] animate-in fade-in zoom-in-95 duration-300">
      
      {/* Summary Bar */}
      <div className="w-full bg-bg-raised border border-border-default p-4 rounded-xl shadow-sm flex items-center justify-between shrink-0">
        <div className="flex items-center space-x-6">
          <div>
             <span className="block text-xs font-mono text-text-tertiary uppercase tracking-wider mb-0.5">Tables Selected</span>
             <div className="text-xl font-display font-bold text-text-primary flex items-center space-x-2">
               <span>{resolvedCount}</span>
               <span className="text-xs font-medium text-text-tertiary">/ {tables.length}</span>
             </div>
          </div>
          <div className="h-8 w-px bg-border-default"></div>
          <div>
             <span className="block text-xs font-mono text-text-tertiary uppercase tracking-wider mb-0.5">Estimated Rows</span>
             <div className="text-xl font-display font-bold text-text-primary">
               {resolvedRows.toLocaleString()}
             </div>
          </div>
          <div className="h-8 w-px bg-border-default"></div>
          <div>
             <span className="block text-xs font-mono text-text-tertiary uppercase tracking-wider mb-0.5">Estimated Size</span>
             <div className="text-xl font-display font-bold text-text-primary">
               {resolvedSizeMB.toFixed(2)} <span className="text-xs font-medium text-text-tertiary">MB</span>
             </div>
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          <label className="text-xs font-mono font-bold text-text-secondary uppercase tracking-wider flex items-center space-x-2">
            <Layers className="w-3.5 h-3.5" />
            <span>Dependency Mode:</span>
          </label>
          <select 
            value={options.fk_dependency_mode || 'auto_include'} 
            onChange={e => onOptionsChange({...options, fk_dependency_mode: e.target.value})}
            className="rounded-md border border-border-default bg-bg-sunken text-text-primary px-3 py-1.5 text-xs font-mono focus:border-accent focus:ring-1 focus:ring-accent focus:outline-none transition-all outline-none"
          >
            <option value="auto_include">Auto-Include</option>
            <option value="strict">Strict (Fail Fast)</option>
            <option value="drop_constraint">Drop Constraint</option>
          </select>
        </div>
      </div>

      {sourceConfig.db_type === 'oracle' && (
        <div className="bg-warning/10 border border-warning/20 text-warning px-4 py-3 rounded-lg mb-6 text-xs font-mono flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-sm">
          <div className="flex items-center space-x-2">
            <span>⚠️ Showing user objects only. Oracle system objects (AQ$, LOGMNR$, MVIEW$, etc.) are automatically excluded.</span>
          </div>
          <label className="flex items-center space-x-2 cursor-pointer shrink-0 bg-warning/20 px-3 py-1.5 rounded-md hover:bg-warning/30 transition-colors border border-warning/30">
            <input 
              type="checkbox" 
              className="accent-warning bg-bg-sunken border-warning"
              checked={options.show_system_objects || false}
              onChange={e => onOptionsChange({...options, show_system_objects: e.target.checked})}
            />
            <span className="text-warning text-xs font-bold uppercase tracking-wider">Show system objects</span>
          </label>
        </div>
      )}

      <div className="flex flex-col lg:flex-row gap-6 w-full flex-1 min-h-0">
        {/* Main Content Area */}
        <div className="flex-1 flex flex-col min-w-0 bg-bg-raised border border-border-default rounded-xl shadow-md overflow-hidden relative">
          
          {/* Tabs */}
          <div className="flex items-center border-b border-border-default overflow-x-auto hide-scrollbar">
            <button
              onClick={() => setActiveTab('tables')}
              className={`flex items-center space-x-2 px-6 py-4 font-mono text-xs font-bold uppercase tracking-wider transition-colors relative whitespace-nowrap ${activeTab === 'tables' ? 'text-text-primary' : 'text-text-secondary hover:text-text-primary'}`}
            >
              <Database className="w-4 h-4" />
              <span>Tables ({tables.length})</span>
              {activeTab === 'tables' && (
                <motion.div layoutId="activeTabIndicator" className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent" />
              )}
            </button>
            <button
              onClick={() => setActiveTab('views')}
              className={`flex items-center space-x-2 px-6 py-4 font-mono text-xs font-bold uppercase tracking-wider transition-colors relative whitespace-nowrap ${activeTab === 'views' ? 'text-text-primary' : 'text-text-secondary hover:text-text-primary'}`}
            >
              <Eye className="w-4 h-4" />
              <span>Views ({objects.views.length})</span>
              {activeTab === 'views' && (
                <motion.div layoutId="activeTabIndicator" className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent" />
              )}
            </button>
            <button
              onClick={() => setActiveTab('procedures')}
              className={`flex items-center space-x-2 px-6 py-4 font-mono text-xs font-bold uppercase tracking-wider transition-colors relative whitespace-nowrap ${activeTab === 'procedures' ? 'text-text-primary' : 'text-text-secondary hover:text-text-primary'}`}
            >
              <Code className="w-4 h-4" />
              <span>Procedures ({objects.procedures.length})</span>
              {activeTab === 'procedures' && (
                <motion.div layoutId="activeTabIndicator" className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent" />
              )}
            </button>
            <button
              onClick={() => setActiveTab('triggers')}
              className={`flex items-center space-x-2 px-6 py-4 font-mono text-xs font-bold uppercase tracking-wider transition-colors relative whitespace-nowrap ${activeTab === 'triggers' ? 'text-text-primary' : 'text-text-secondary hover:text-text-primary'}`}
            >
              <Zap className="w-4 h-4" />
              <span>Triggers ({objects.triggers.length})</span>
              {activeTab === 'triggers' && (
                <motion.div layoutId="activeTabIndicator" className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent" />
              )}
            </button>
          </div>

          <div className="px-5 pt-3 pb-1 bg-bg-raised flex items-center justify-between text-xs text-text-secondary font-mono">
            <span>
              {objects.views.length} views &bull; {objects.procedures.length} procedures &bull; {objects.triggers.length} triggers
            </span>
          </div>

          {/* Grid Toolbar */}
          <div className="px-5 py-3 border-b border-border-default bg-bg-raised flex items-center justify-between z-10 shadow-sm shrink-0 flex-wrap gap-3">
            
            <motion.button 
              whileTap={{ scale: 0.98 }}
              onClick={handleGlobalSelectAll}
              className="flex items-center space-x-2.5 text-xs font-bold font-mono text-text-primary hover:text-accent transition-colors"
            >
              {isAllSelected ? (
                <CheckSquare className="w-4 h-4 text-accent" />
              ) : isPartiallySelected ? (
                <div className="w-4 h-4 bg-accent rounded flex items-center justify-center">
                  <div className="w-2.5 h-0.5 bg-text-inverse rounded-full"></div>
                </div>
              ) : (
                <Square className="w-4 h-4 text-text-secondary" />
              )}
              <span>Select All {activeTab}</span>
              <span className="ml-2 bg-bg-sunken px-1.5 py-0.5 rounded-md text-xs text-text-secondary border border-border-default">
                {selectedCount} / {totalCount}
              </span>
            </motion.button>
            
            <div className="relative w-full sm:w-64">
              <Search className="w-4 h-4 absolute left-3 top-2 text-text-secondary" />
              <input 
                type="text" 
                placeholder={`Filter ${activeTab}...`}
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 bg-bg-sunken border border-border-default rounded-md text-xs font-mono text-text-primary focus:border-accent focus:ring-1 focus:ring-accent transition-all outline-none"
              />
            </div>
          </div>

          {/* Data Table */}
          <div className="flex-1 overflow-auto bg-bg-canvas/30 scrollbar-thin scrollbar-thumb-border-card relative z-0">
            {isResolving && activeTab === 'tables' && (
               <div className="absolute top-0 left-0 right-0 h-1 bg-accent-solid/20 overflow-hidden">
                 <div className="h-full bg-accent-solid w-1/3 animate-[slide_1.5s_ease-in-out_infinite]"></div>
               </div>
            )}
            <table className="w-full text-left text-xs font-mono relative table-fixed">
               <thead className="sticky top-0 bg-bg-raised border-b border-border-default text-text-secondary z-10 shadow-sm">
                 <tr>
                   <th className="px-5 py-3 w-14 text-center"></th>
                   <th className={`px-5 py-3 font-bold uppercase tracking-wider ${activeTab === 'tables' ? 'w-[45%]' : 'w-[70%]'}`}>Asset Name</th>
                   {activeTab === 'tables' && (
                     <th className="px-5 py-3 w-[25%] font-bold uppercase tracking-wider">Dependencies</th>
                   )}
                   <th className="px-5 py-3 w-[25%] font-bold uppercase tracking-wider text-right">
                     {activeTab === 'tables' ? 'Row Volume' : 'Complexity'}
                   </th>
                 </tr>
               </thead>
               <tbody className="divide-y divide-border-subtle">
                  
                  {/* Tables Render */}
                  {activeTab === 'tables' && filteredTables.map(t => {
                    const isManual = isTableManuallySelected(t.name)
                    const isAuto = isTableAutoAdded(t.name)
                    const isBlocked = isTableBlocked(t.name)
                    const selected = isManual || isAuto
                    
                    const hasFKs = t.has_foreign_keys_to?.length > 0
                    const hasRefs = t.referenced_by?.length > 0
                    const autoReason = dependencyResolution?.auto_added_reasons?.[t.name]

                    return (
                      <tr key={t.name} className={`group transition-colors ${selected ? (isAuto ? 'bg-info-muted/20 hover:bg-info-muted/30' : 'bg-accent-muted/15 hover:bg-accent-muted/25') : 'hover:bg-bg-raised/40'}`}>
                        <td className="px-5 py-2.5 text-center">
                          <button 
                            className="cursor-pointer mt-1 relative" 
                            onClick={() => handleSelectTable(t.name, !isManual)}
                          >
                            {isAuto && !isManual ? (
                              <CheckSquare className="w-4 h-4 text-info opacity-70" />
                            ) : selected ? (
                              <CheckSquare className="w-4 h-4 text-accent" />
                            ) : (
                              <Square className="w-4 h-4 text-text-tertiary group-hover:text-text-primary transition-colors" />
                            )}
                          </button>
                        </td>
                        <td className="px-5 py-2.5">
                          <div className="flex items-center space-x-2.5">
                            <Database className={`w-3.5 h-3.5 ${selected ? (isAuto ? 'text-info' : 'text-accent') : 'text-text-tertiary'} transition-colors`} />
                            <span className={`font-semibold ${selected ? 'text-text-primary' : 'text-text-secondary'} transition-colors`}>{t.name}</span>
                            
                            {isAuto && (
                               <div className="group/tooltip relative inline-flex">
                                 <span className="px-1.5 py-0.5 rounded bg-info-muted text-info text-[9px] uppercase tracking-wider font-bold cursor-help border border-info/20">
                                   Auto-Added
                                 </span>
                                 <div className="absolute left-0 bottom-full mb-2 hidden group-hover/tooltip:block w-48 bg-bg-raised text-text-primary text-[10px] p-2 rounded shadow-xl border border-border-default z-50">
                                    {autoReason || 'Added due to dependency rules.'}
                                 </div>
                               </div>
                            )}
                            
                            {isBlocked && (
                               <div className="group/tooltip relative inline-flex">
                                 <span className="px-1.5 py-0.5 rounded bg-error-muted text-error text-[9px] uppercase tracking-wider font-bold cursor-help border border-error/20">
                                   Blocked
                                 </span>
                                 <div className="absolute left-0 bottom-full mb-2 hidden group-hover/tooltip:block w-48 bg-bg-raised text-text-primary text-[10px] p-2 rounded shadow-xl border border-border-default z-50">
                                    Strict mode failed due to missing dependency.
                                 </div>
                               </div>
                            )}
                          </div>
                        </td>
                        <td className="px-5 py-2.5">
                           {(hasFKs || hasRefs) && (
                              <div className="group/deps relative inline-flex items-center space-x-1.5 text-text-tertiary cursor-pointer hover:text-text-primary transition-colors">
                                 <Network className="w-3.5 h-3.5" />
                                 <span className="text-[10px] font-bold">{t.has_foreign_keys_to?.length + t.referenced_by?.length}</span>
                                 
                                 <div className="absolute left-0 bottom-full mb-2 hidden group-hover/deps:block w-64 bg-bg-raised text-text-primary p-3 rounded shadow-xl border border-border-default z-50">
                                    {hasFKs && (
                                       <div className="mb-2">
                                          <div className="text-[10px] uppercase text-text-tertiary mb-1">Depends on</div>
                                          <div className="text-[11px] font-mono leading-tight">{t.has_foreign_keys_to.join(', ')}</div>
                                       </div>
                                    )}
                                    {hasRefs && (
                                       <div>
                                          <div className="text-[10px] uppercase text-text-tertiary mb-1">Referenced by</div>
                                          <div className="text-[11px] font-mono leading-tight">{t.referenced_by.join(', ')}</div>
                                       </div>
                                    )}
                                 </div>
                              </div>
                           )}
                        </td>
                        <td className="px-5 py-2.5 text-right font-bold text-info">{t.row_count.toLocaleString()}</td>
                      </tr>
                    )
                  })}

                  {/* Views Render */}
                  {activeTab === 'views' && filteredViews.map(o => {
                    const selected = isObjectSelected('view', o.name)
                    return (
                      <tr key={o.name} className={`group transition-colors ${selected ? 'bg-accent-muted/15 hover:bg-accent-muted/25' : 'hover:bg-bg-raised/40'}`}>
                        <td className="px-5 py-2.5 text-center">
                          <button className="cursor-pointer mt-1" onClick={() => handleSelectObject('view', o.name, !selected)}>
                            {selected ? <CheckSquare className="w-4 h-4 text-accent" /> : <Square className="w-4 h-4 text-text-tertiary group-hover:text-text-primary transition-colors" />}
                          </button>
                        </td>
                        <td className="px-5 py-2.5">
                          <div className="flex items-center space-x-2.5">
                            <Eye className={`w-3.5 h-3.5 ${selected ? 'text-accent' : 'text-text-tertiary'} transition-colors`} />
                            <span className={`font-semibold ${selected ? 'text-text-primary' : 'text-text-secondary'} transition-colors`}>{o.name}</span>
                          </div>
                        </td>
                        <td className="px-5 py-2.5 text-right">
                          <span className="px-1.5 py-0.5 rounded bg-success-muted text-success font-semibold border border-success/20 text-xs">LOW</span>
                        </td>
                      </tr>
                    )
                  })}

                  {/* Procedures Render */}
                  {activeTab === 'procedures' && filteredProcedures.map(o => {
                    const selected = isObjectSelected('procedure', o.name)
                    const isHigh = o.complexity_estimate === 'high';
                    const isLow = o.complexity_estimate === 'low';
                    const badgeColor = isHigh ? 'bg-error-muted text-error border-error/20' : (isLow ? 'bg-success-muted text-success border-success/20' : 'bg-warning-muted text-warning border-warning/20');
                    return (
                      <tr key={o.name} className={`group transition-colors ${selected ? 'bg-accent-muted/15 hover:bg-accent-muted/25' : 'hover:bg-bg-raised/40'}`}>
                        <td className="px-5 py-2.5 text-center">
                          <button className="cursor-pointer mt-1" onClick={() => handleSelectObject('procedure', o.name, !selected)}>
                            {selected ? <CheckSquare className="w-4 h-4 text-accent" /> : <Square className="w-4 h-4 text-text-tertiary group-hover:text-text-primary transition-colors" />}
                          </button>
                        </td>
                        <td className="px-5 py-2.5">
                          <div className="flex items-center space-x-2.5">
                            <Code className={`w-3.5 h-3.5 ${selected ? 'text-accent' : 'text-text-tertiary'} transition-colors`} />
                            <span className={`font-semibold ${selected ? 'text-text-primary' : 'text-text-secondary'} transition-colors`}>{o.name}</span>
                          </div>
                        </td>
                        <td className="px-5 py-2.5 text-right">
                          <span className={`px-1.5 py-0.5 rounded font-semibold border text-xs uppercase tracking-wider ${badgeColor}`}>
                             {o.complexity_estimate || 'MEDIUM'}
                          </span>
                        </td>
                      </tr>
                    )
                  })}

                  {/* Triggers Render */}
                  {activeTab === 'triggers' && filteredTriggers.map(o => {
                    const selected = isObjectSelected('trigger', o.name)
                    const isHigh = o.complexity_estimate === 'high';
                    const isLow = o.complexity_estimate === 'low';
                    const badgeColor = isHigh ? 'bg-error-muted text-error border-error/20' : (isLow ? 'bg-success-muted text-success border-success/20' : 'bg-warning-muted text-warning border-warning/20');
                    return (
                      <tr key={o.name} className={`group transition-colors ${selected ? 'bg-accent-muted/15 hover:bg-accent-muted/25' : 'hover:bg-bg-raised/40'}`}>
                        <td className="px-5 py-2.5 text-center">
                          <button className="cursor-pointer mt-1" onClick={() => handleSelectObject('trigger', o.name, !selected)}>
                            {selected ? <CheckSquare className="w-4 h-4 text-accent" /> : <Square className="w-4 h-4 text-text-tertiary group-hover:text-text-primary transition-colors" />}
                          </button>
                        </td>
                        <td className="px-5 py-2.5">
                          <div className="flex items-center space-x-2.5">
                            <Zap className={`w-3.5 h-3.5 ${selected ? 'text-accent' : 'text-text-tertiary'} transition-colors`} />
                            <span className={`font-semibold ${selected ? 'text-text-primary' : 'text-text-secondary'} transition-colors`}>{o.name}</span>
                          </div>
                        </td>
                        <td className="px-5 py-2.5 text-right">
                          <span className={`px-1.5 py-0.5 rounded font-semibold border text-xs uppercase tracking-wider ${badgeColor}`}>
                             {o.complexity_estimate || 'MEDIUM'}
                          </span>
                        </td>
                      </tr>
                    )
                  })}

               </tbody>
            </table>
            
            {((activeTab === 'tables' && filteredTables.length === 0) ||
              (activeTab === 'views' && filteredViews.length === 0) ||
              (activeTab === 'procedures' && filteredProcedures.length === 0) ||
              (activeTab === 'triggers' && filteredTriggers.length === 0)) && (
              <div className="flex flex-col items-center justify-center py-20 text-muted-slate space-y-3">
                <Search className="w-8 h-8 opacity-20" />
                <div className="text-xs font-mono">
                  {searchTerm 
                    ? `No items found matching "${searchTerm}"` 
                    : (sourceConfig.db_type === 'oracle' 
                        ? `No user-defined ${activeTab} found. Oracle system ${activeTab} are excluded from migration.` 
                        : `No ${activeTab} found.`)}
                </div>
              </div>
            )}
          </div>

        </div>
      </div>
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes slide {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(300%); }
        }
      `}} />
    </div>
  )
}

export default memo(ObjectPicker)
