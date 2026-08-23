import React, { useState, useMemo, useCallback } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  BackgroundVariant
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, Layers, RefreshCw, Network, Sparkles } from 'lucide-react'
import TableNode from './TableNode'
import SchemaSidebar from './SchemaSidebar'
import { initialNodes, initialEdges } from './mockSchemaData'

export default function SchemaCanvas({ onClose = null }) {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)
  const [activeNode, setActiveNode] = useState(null)
  const [search, setSearch] = useState('')

  const nodeTypes = useMemo(() => ({ tableNode: TableNode }), [])

  // Node Click handler
  const handleNodeClick = useCallback((event, node) => {
    setActiveNode(node)
  }, [])

  // Pane Click handler (closes sidebar)
  const handlePaneClick = useCallback(() => {
    setActiveNode(null)
  }, [])

  // Search Filtering
  const filteredNodes = useMemo(() => {
    if (!search.trim()) return nodes
    const q = search.toLowerCase()
    return nodes.map(n => ({
      ...n,
      hidden: !n.data.tableName.toLowerCase().includes(q) &&
              !n.data.columns.some(c => c.name.toLowerCase().includes(q))
    }))
  }, [nodes, search])

  const handleResetLayout = () => {
    setNodes(initialNodes)
    setEdges(initialEdges)
    setSearch('')
    setActiveNode(null)
  }

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="relative w-full h-full flex flex-col bg-transparent overflow-hidden"
    >
      {/* Top Controls Bar */}
      <div className="h-14 shrink-0 px-6 bg-black/40 backdrop-blur-md border-b border-white/10 flex items-center justify-between z-30">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-xl bg-accent/15 border border-accent/30 flex items-center justify-center">
            <Network className="w-4 h-4 text-accent" />
          </div>
          <div>
            <h2 className="font-sans font-semibold text-body-sm text-stark-white uppercase tracking-wider">Interactive ERD Canvas</h2>
            <p className="font-sans text-caption text-gray-400 uppercase">Automated Schema Topology</p>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          {/* Search Bar */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search tables & columns..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="pl-9 pr-3 py-1.5 bg-black/50 border border-white/10 rounded-lg font-sans text-caption text-stark-white placeholder:text-gray-500 w-56 focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent transition-all"
            />
          </div>

          <div className="h-4 w-px bg-white/10" />

          {/* Reset button */}
          <button
            onClick={handleResetLayout}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-black/40 hover:bg-white/10 border border-white/10 rounded-lg text-xs font-mono text-gray-300 hover:text-white transition-colors cursor-pointer"
            title="Reset Diagram Layout"
          >
            <RefreshCw className="w-3.5 h-3.5 text-accent" />
            <span className="font-sans text-caption font-semibold uppercase">Reset</span>
          </button>

          {onClose && (
            <button 
              onClick={onClose} 
              className="px-3 py-1.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 rounded-lg text-[10px] font-mono font-bold uppercase tracking-wider transition-colors cursor-pointer"
            >
              Close
            </button>
          )}
        </div>
      </div>

      {/* Canvas Area */}
      <div className="flex-1 relative w-full h-full">
        <ReactFlow
          nodes={filteredNodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={handleNodeClick}
          onPaneClick={handlePaneClick}
          nodeTypes={nodeTypes}
          fitView
          attributionPosition="bottom-left"
          className="bg-transparent"
        >
          {/* Dot Grid Background */}
          <Background 
            variant={BackgroundVariant.Dots} 
            color="#7c3aed" 
            gap={32} 
            size={1} 
            opacity={0.2} 
          />

          {/* Dark-styled Controls */}
          <Controls 
            className="!bg-black/60 !border !border-white/10 !rounded-xl !overflow-hidden !shadow-2xl !text-white"
          />

          {/* Dark-styled MiniMap */}
          <MiniMap 
            nodeColor={() => '#7c3aed'}
            maskColor="rgba(5, 5, 8, 0.8)"
            className="!bg-black/70 !border !border-white/10 !rounded-xl !overflow-hidden !shadow-2xl hidden md:block"
          />
        </ReactFlow>
      </div>

      {/* Slide-in Detail Sidebar */}
      <AnimatePresence>
        {activeNode && (
          <SchemaSidebar 
            activeNode={activeNode} 
            edges={edges} 
            onClose={() => setActiveNode(null)} 
          />
        )}
      </AnimatePresence>
    </motion.div>
  )
}
