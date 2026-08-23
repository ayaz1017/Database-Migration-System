import React, { useMemo, useCallback } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  BackgroundVariant,
  Handle,
  Position,
  useNodesState,
  useEdgesState,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { motion } from 'framer-motion'
import { Database, Cpu, FileCode2, Code2, Rocket } from 'lucide-react'

// Custom Node Component
const ArchitectureNode = ({ data, selected }) => {
  const Icon = data.icon || Database

  return (
    <div className={`
      relative p-4 rounded-xl backdrop-blur-md border transition-all min-w-[200px]
      ${selected ? 'bg-accent/20 border-accent shadow-[0_0_20px_rgba(124,58,237,0.3)]' : 'bg-black/60 border-white/10 hover:border-white/20'}
    `}>
      <Handle type="target" position={Position.Left} className="!w-2 !h-2 !bg-accent !border-black" />
      
      <div className="flex items-center space-x-3 mb-2">
        <div className={`p-2 rounded-lg ${selected ? 'bg-accent/20 text-accent' : 'bg-white/5 text-gray-400'}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div>
          <h3 className="font-sans font-semibold text-body-sm text-stark-white">{data.label}</h3>
          <p className="font-mono text-caption text-gray-500 uppercase tracking-widest">{data.type}</p>
        </div>
      </div>

      <div className="font-sans text-caption text-gray-400 mt-3 line-clamp-2">
        {data.description}
      </div>

      <Handle type="source" position={Position.Right} className="!w-2 !h-2 !bg-accent !border-black" />
    </div>
  )
}

const initialNodes = [
  { id: '1', type: 'archNode', position: { x: 50, y: 150 }, data: { label: 'Source Connector', type: 'Ingestion', description: 'JDBC/CDC connection to legacy DB', icon: Database } },
  { id: '2', type: 'archNode', position: { x: 350, y: 50 }, data: { label: 'AST Parser', type: 'Compilation', description: 'Parses DDL into Abstract Syntax Tree', icon: FileCode2 } },
  { id: '3', type: 'archNode', position: { x: 350, y: 250 }, data: { label: 'Data Extractor', type: 'ETL Worker', description: 'Parallel row streaming via pg_dump/cursors', icon: Cpu } },
  { id: '4', type: 'archNode', position: { x: 650, y: 50 }, data: { label: 'SQL Compiler', type: 'Compilation', description: 'Generates target dialect DDL', icon: Code2 } },
  { id: '5', type: 'archNode', position: { x: 650, y: 250 }, data: { label: 'Transform Engine', type: 'ETL Worker', description: 'Applies data type mappings & rules', icon: Cpu } },
  { id: '6', type: 'archNode', position: { x: 950, y: 150 }, data: { label: 'Target Connector', type: 'Deployment', description: 'Pushes schema and payloads to Target DB', icon: Rocket } },
]

const initialEdges = [
  { id: 'e1-2', source: '1', target: '2', animated: true, style: { stroke: '#7c3aed', strokeWidth: 2 } },
  { id: 'e1-3', source: '1', target: '3', animated: true, style: { stroke: '#3b82f6', strokeWidth: 2 } },
  { id: 'e2-4', source: '2', target: '4', animated: true, style: { stroke: '#7c3aed', strokeWidth: 2 } },
  { id: 'e3-5', source: '3', target: '5', animated: true, style: { stroke: '#3b82f6', strokeWidth: 2 } },
  { id: 'e4-6', source: '4', target: '6', animated: true, style: { stroke: '#7c3aed', strokeWidth: 2 } },
  { id: 'e5-6', source: '5', target: '6', animated: true, style: { stroke: '#3b82f6', strokeWidth: 2 } },
]

export default function PipelineMap({ onNodeClick }) {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)

  const nodeTypes = useMemo(() => ({ archNode: ArchitectureNode }), [])

  const handleNodeClick = useCallback((event, node) => {
    onNodeClick(node)
  }, [onNodeClick])

  const handlePaneClick = useCallback(() => {
    onNodeClick(null)
  }, [onNodeClick])

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="w-full h-full bg-black/40 backdrop-blur-xl border border-white/10 rounded-3xl overflow-hidden relative"
    >
      <div className="absolute top-6 left-6 z-10 pointer-events-none">
        <h2 className="text-xl font-bold text-stark-white tracking-tight">System Architecture Map</h2>
        <p className="text-sm text-gray-400 font-mono mt-1">Interactive DAG of the migration engine</p>
      </div>

      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        onPaneClick={handlePaneClick}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        proOptions={{ hideAttribution: true }}
      >
        <Background variant={BackgroundVariant.Dots} color="#ffffff" gap={24} size={1} opacity={0.1} />
        <Controls className="!bg-black/60 !border-white/10 !text-white [&>button]:!border-b-white/10 hover:[&>button]:!bg-white/10" />
      </ReactFlow>
    </motion.div>
  )
}
