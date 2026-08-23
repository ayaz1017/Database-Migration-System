import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Cpu, Server, Activity, ArrowRight } from 'lucide-react'

// Mock details for nodes
const NODE_DETAILS = {
  '1': {
    techStack: ['Java', 'JDBC', 'Debezium'],
    inputs: ['Database Credentials', 'Schema Filters'],
    outputs: ['Raw DDL Streams', 'CDC Event Stream'],
    metrics: { cpu: '4%', ram: '128MB' }
  },
  '2': {
    techStack: ['Rust', 'ANTLR4'],
    inputs: ['Raw DDL Streams'],
    outputs: ['Abstract Syntax Tree (JSON)'],
    metrics: { cpu: '45%', ram: '512MB' }
  },
  '3': {
    techStack: ['Go', 'pg_dump', 'Goroutines'],
    inputs: ['Table Metadata'],
    outputs: ['CSV / Parquet Chunks'],
    metrics: { cpu: '80%', ram: '4GB' }
  },
  '4': {
    techStack: ['Python', 'Jinja2', 'FastAPI'],
    inputs: ['Abstract Syntax Tree (JSON)'],
    outputs: ['Target Dialect DDL (SQL)'],
    metrics: { cpu: '15%', ram: '256MB' }
  },
  '5': {
    techStack: ['Go', 'Apache Arrow'],
    inputs: ['CSV / Parquet Chunks', 'Mapping Rules'],
    outputs: ['Transformed Payloads'],
    metrics: { cpu: '60%', ram: '8GB' }
  },
  '6': {
    techStack: ['Go', 'Native Drivers'],
    inputs: ['Target DDL', 'Transformed Payloads'],
    outputs: ['Committed DB Transactions'],
    metrics: { cpu: '10%', ram: '512MB' }
  },
}

export default function NodeInspectorPanel({ node, onClose }) {
  const details = node ? NODE_DETAILS[node.id] : null

  return (
    <AnimatePresence>
      {node && details && (
        <motion.div
          initial={{ x: '100%', opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: '100%', opacity: 0 }}
          transition={{ type: 'spring', damping: 25, stiffness: 250 }}
          className="absolute top-0 right-0 h-full w-[350px] bg-bg-panel/95 backdrop-blur-3xl border-l border-white/10 p-6 shadow-[-20px_0_40px_rgba(0,0,0,0.5)] z-20 flex flex-col overflow-y-auto custom-scrollbar"
        >
          <div className="flex items-start justify-between mb-8 shrink-0">
            <div>
              <h3 className="font-sans text-h4 font-semibold text-stark-white tracking-tight">{node.data.label}</h3>
              <span className="inline-block mt-2 px-2 py-1 bg-accent/10 border border-accent/20 text-accent font-mono text-caption rounded uppercase tracking-wider">
                {node.data.type}
              </span>
            </div>
            <button 
              onClick={onClose}
              className="p-2 hover:bg-white/10 rounded-full transition-colors text-gray-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="space-y-6 flex-1">
            {/* Description */}
            <div>
              <h4 className="font-sans text-caption text-gray-500 uppercase tracking-wider mb-2">Description</h4>
              <p className="font-sans text-body-sm text-gray-300 leading-relaxed">{node.data.description}</p>
            </div>

            {/* Inputs / Outputs */}
            <div className="bg-black/40 border border-white/5 rounded-xl p-4">
              <div className="mb-4">
                <h4 className="font-sans text-caption text-gray-500 uppercase tracking-wider mb-2 flex items-center">
                  Inputs <ArrowRight className="w-3 h-3 ml-2 text-gray-600" />
                </h4>
                <ul className="space-y-1">
                  {details.inputs.map(i => (
                    <li key={i} className="text-xs font-mono text-gray-300 flex items-center">
                      <span className="w-1 h-1 bg-blue-500 rounded-full mr-2" /> {i}
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h4 className="font-sans text-caption text-gray-500 uppercase tracking-wider mb-2 flex items-center">
                  <ArrowRight className="w-3 h-3 mr-2 text-gray-600" /> Outputs
                </h4>
                <ul className="space-y-1">
                  {details.outputs.map(i => (
                    <li key={i} className="text-xs font-mono text-gray-300 flex items-center">
                      <span className="w-1 h-1 bg-emerald-500 rounded-full mr-2" /> {i}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Tech Stack */}
            <div>
              <h4 className="font-sans text-caption text-gray-500 uppercase tracking-wider mb-2">Core Technology</h4>
              <div className="flex flex-wrap gap-2">
                {details.techStack.map(tech => (
                  <span key={tech} className="px-2.5 py-1 bg-white/5 border border-white/10 rounded-lg text-xs font-mono text-gray-300">
                    {tech}
                  </span>
                ))}
              </div>
            </div>

            {/* Live Metrics */}
            <div>
              <h4 className="font-sans text-caption text-gray-500 uppercase tracking-wider mb-2">Average Utilization</h4>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-white/5 rounded-lg p-3 flex items-center space-x-3 border border-white/5">
                  <Cpu className="w-4 h-4 text-accent" />
                  <div>
                    <div className="text-xs font-mono font-bold text-white">{details.metrics.cpu}</div>
                    <div className="text-caption text-gray-500 uppercase">CPU</div>
                  </div>
                </div>
                <div className="bg-white/5 rounded-lg p-3 flex items-center space-x-3 border border-white/5">
                  <Server className="w-4 h-4 text-blue-400" />
                  <div>
                    <div className="text-xs font-mono font-bold text-white">{details.metrics.ram}</div>
                    <div className="text-caption text-gray-500 uppercase">Memory</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
