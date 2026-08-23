import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Database, ShieldCheck, Play, Code } from 'lucide-react'
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion'

export default function Docs() {
  const [activeSection, setActiveSection] = useState('getting-started')
  const shouldReduceMotion = useReducedMotion()

  const sections = [
    { id: 'getting-started', name: 'Getting Started', icon: Play },
    { id: 'api-discover', name: 'POST /discover', icon: Code },
    { id: 'api-migrate', name: 'POST /migrate', icon: Code },
    { id: 'validation-math', name: 'Validation Algebra', icon: ShieldCheck }
  ]

  const discoverRequestShape = `{
  "db_type": "mssql | mysql | postgres",
  "host": "localhost",
  "port": 1433,
  "username": "sa",
  "password": "your_secure_password",
  "database": "production_crm"
}`

  const discoverResponseShape = `{
  "tables": [
    {
      "name": "users",
      "row_count": 15000,
      "primary_keys": ["id"],
      "columns": [
        { "name": "id", "type": "INT" },
        { "name": "email", "type": "VARCHAR(255)" }
      ],
      "foreign_keys": [],
      "indexes": [],
      "check_constraints": []
    }
  ]
}`

  const migrateRequestShape = `{
  "source": {
    "db_type": "mssql",
    "host": "127.0.0.1",
    "port": 1433,
    "username": "sa",
    "password": "secure_password",
    "database": "source_crm"
  },
  "target": {
    "db_type": "postgres",
    "host": "127.0.0.1",
    "port": 5432,
    "username": "postgres",
    "password": "target_password",
    "database": "target_crm"
  },
  "mode": "full_load | cdc | full_then_cdc"
}`

  const migrateResponseShape = `{
  "status": "success",
  "duration_seconds": 1.45,
  "tables_migrated": 1,
  "total_rows": 15000,
  "validation_score": 100,
  "ddl_translation_log": [
    {
      "column": "id",
      "from": "INT IDENTITY(1,1)",
      "to": "SERIAL",
      "lossy": false
    }
  ],
  "llm_warnings": {
    "warnings": []
  },
  "validation_report": {
    "validation_score": 100,
    "tables": [
      {
        "table": "users",
        "source_row_count": 15000,
        "target_row_count": 15000,
        "issues": []
      }
    ]
  }
}`

  return (
    <div className="min-h-screen bg-[#09090b] text-zinc-200 flex flex-col pt-20 pb-16">
      
      {/* Docs Body Layout */}
      <div className="flex-1 max-w-7xl mx-auto w-full px-6 py-8 flex gap-8">
        
        {/* Left Sidebar Navigation */}
        <aside className="w-64 shrink-0 hidden md:block">
          <div className="sticky top-28 space-y-5">
            <div className="px-3">
              <span className="text-[11px] font-mono text-zinc-500 uppercase tracking-wider block mb-3 font-bold">API Specifications</span>
              <ul className="space-y-1">
                {sections.map((sec) => {
                  const Icon = sec.icon
                  return (
                    <li key={sec.id}>
                      <button
                        onClick={() => setActiveSection(sec.id)}
                        className={`w-full flex items-center px-3 py-2 rounded-lg text-xs font-mono font-medium transition-all relative text-left cursor-pointer ${
                          activeSection === sec.id ? 'text-white bg-zinc-800 border border-zinc-700' : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900'
                        }`}
                      >
                        <Icon className="w-4 h-4 mr-2.5 text-indigo-400" />
                        <span>{sec.name}</span>
                      </button>
                    </li>
                  )
                })}
              </ul>
            </div>
            
            <div className="p-4 bg-bg-raised rounded-none border border-border-default space-y-2">
              <span className="text-[9px] font-mono text-text-secondary uppercase tracking-wider block font-bold">Server endpoint</span>
              <span className="text-xs font-mono text-text-primary block bg-bg-base p-2 rounded-none border border-border-default">http://localhost:8000</span>
            </div>
          </div>
        </aside>

        {/* Right Content Area */}
        <main className="flex-1 bg-bg-raised border border-border-default rounded-none p-8 shadow-2xl overflow-hidden min-h-[500px]">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeSection}
              initial={shouldReduceMotion ? {} : { opacity: 0, y: 8 }}
              animate={shouldReduceMotion ? {} : { opacity: 1, y: 0 }}
              exit={shouldReduceMotion ? {} : { opacity: 0, y: -8 }}
              transition={{ duration: 0.15, ease: "easeInOut" }}
            >
              {activeSection === 'getting-started' && (
            <div className="space-y-6 animate-in fade-in duration-300">
              <div className="space-y-2 pb-4 border-b border-border-default">
                <h1 className="text-h1 font-sans font-bold text-text-primary">Developer Integration</h1>
                <p className="font-sans text-body text-text-secondary font-light">
                  The migration core exposes raw HTTP socket endpoints for database schema discovery and replication pipelines. It is designed to be called from code, not just clicked in a UI.
                </p>
              </div>

              <div className="space-y-4 font-sans text-body font-light text-text-secondary leading-relaxed">
                <p>
                  By bypassing virtual layers and intermediary writes, Fluxline routes schema conversions and data replication directly. The migration agent runs locally by default at <code className="text-text-primary bg-bg-base px-1.5 py-0.5 rounded-none font-mono text-xs border border-neutral-805">http://localhost:8000</code>.
                </p>
                <p>
                  Automate database syncs and cutovers with the discover and migrate endpoints detailed below.
                </p>
              </div>

              <div className="p-4 bg-bg-base rounded-none border border-border-default space-y-2">
                <span className="text-[10px] font-mono text-text-secondary uppercase tracking-wider block font-bold">CLI quickstart</span>
                <pre className="text-xs font-mono text-neutral-350 overflow-x-auto">
                  curl -X POST http://localhost:8000/health
                </pre>
              </div>
            </div>
          )}

          {activeSection === 'api-discover' && (
            <div className="space-y-6 animate-in fade-in duration-300">
              <div className="space-y-2 pb-4 border-b border-border-default">
                <div className="inline-flex items-center space-x-2 bg-bg-sunken border border-border-default rounded-none px-2.5 py-1 text-xs font-mono font-bold text-neutral-350">
                  <span>POST</span>
                  <span>/discover</span>
                </div>
                <h1 className="text-h1 font-sans font-bold text-text-primary pt-2">Database Schema Discovery</h1>
                <p className="font-sans text-body text-text-secondary font-light">Inspects tables, column types, constraints, and total row-counts of a source database.</p>
              </div>

              <div className="space-y-6">
                <div className="space-y-2.5">
                  <h3 className="font-sans text-h3 font-semibold text-text-secondary uppercase tracking-wider">Request JSON Payload</h3>
                  <pre className="text-xs font-mono text-text-primary bg-bg-base p-4 rounded-none border border-neutral-805 overflow-x-auto leading-relaxed">
                    {discoverRequestShape}
                  </pre>
                </div>

                <div className="space-y-2.5">
                  <h3 className="font-sans text-h3 font-semibold text-text-secondary uppercase tracking-wider">Response JSON Payload</h3>
                  <pre className="text-xs font-mono text-neutral-350 bg-bg-base p-4 rounded-none border border-neutral-805 overflow-x-auto leading-relaxed">
                    {discoverResponseShape}
                  </pre>
                </div>
              </div>
            </div>
          )}

          {activeSection === 'api-migrate' && (
            <div className="space-y-6 animate-in fade-in duration-300">
              <div className="space-y-2 pb-4 border-b border-border-default">
                <div className="inline-flex items-center space-x-2 bg-bg-sunken border border-border-default rounded-none px-2.5 py-1 text-xs font-mono font-bold text-neutral-350">
                  <span>POST</span>
                  <span>/migrate</span>
                </div>
                <h1 className="text-h1 font-sans font-bold text-text-primary pt-2">Execute Migration Pipeline</h1>
                <p className="font-sans text-body text-text-secondary font-light">Runs a deterministic schema compilation, applies DDL statements to target, and streams binary data packet packages.</p>
              </div>

              <div className="space-y-6">
                <div className="space-y-2.5">
                  <h3 className="font-sans text-h3 font-semibold text-text-secondary uppercase tracking-wider">Request JSON Payload</h3>
                  <pre className="text-xs font-mono text-text-primary bg-bg-base p-4 rounded-none border border-neutral-805 overflow-x-auto leading-relaxed">
                    {migrateRequestShape}
                  </pre>
                </div>

                <div className="space-y-2.5">
                  <h3 className="font-sans text-h3 font-semibold text-text-secondary uppercase tracking-wider">Response JSON Payload</h3>
                  <pre className="text-xs font-mono text-neutral-350 bg-bg-base p-4 rounded-none border border-neutral-805 overflow-x-auto leading-relaxed">
                    {migrateResponseShape}
                  </pre>
                </div>
              </div>
            </div>
          )}

          {activeSection === 'validation-math' && (
            <div className="space-y-6 animate-in fade-in duration-300">
              <div className="space-y-2 pb-4 border-b border-border-default">
                <h1 className="text-h1 font-sans font-bold text-text-primary">Validation Algebra</h1>
                <p className="font-sans text-body text-text-secondary font-light">Mathematical evaluation scoring of schema mapping parity and row count validations.</p>
              </div>

              <div className="space-y-4 font-sans text-body font-light text-text-secondary leading-relaxed">
                <p>
                  Fluxline performs deterministic schema post-migration validation checks. The final accuracy scoring begins at <code className="text-text-primary font-mono bg-bg-base px-1 rounded-none border border-neutral-805">100</code> and receives cumulative deductions for structural drift and gaps:
                </p>
              </div>

              {/* LaTeX Formula Block */}
              <div className="p-6 bg-bg-base border border-border-default rounded-none text-center space-y-3">
                <span className="text-[10px] font-mono text-text-secondary uppercase tracking-wider block font-bold">Scoring Equation</span>
                <div className="text-base text-text-primary overflow-x-auto py-2 font-serif select-none">
                  {"S = \\max \\left( 0,\\, 100 - \\sum_{\\text{tables}} \\left( 20 \\cdot \\mathbb{I}_{\\Delta\\text{row}} + 15 \\cdot \\mathbb{I}_{\\Delta\\text{checksum}} + 10 \\cdot \\mathbb{I}_{\\text{no PK}} + 5 \\cdot N_{\\Delta\\text{FK}} + 3 \\cdot N_{\\Delta\\text{idx}} + 2 \\cdot N_{\\Delta\\text{const}} \\right) \\right)"}
                </div>
              </div>

              {/* Deductions weights table */}
              <div className="space-y-3">
                <h3 className="font-sans text-h3 font-semibold text-text-secondary uppercase tracking-wider">Penalty Weight Registry</h3>
                <div className="bg-bg-base rounded-none border border-border-default overflow-hidden">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-bg-raised border-b border-border-default text-text-secondary">
                      <tr>
                        <th className="px-4 py-3 font-bold uppercase tracking-wider">Detection Fault</th>
                        <th className="px-4 py-3 font-bold uppercase tracking-wider">Penalty Deduction</th>
                        <th className="px-4 py-3 font-bold uppercase tracking-wider">Code Identifier</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-neutral-800 text-text-secondary">
                      <tr className="hover:bg-[#1E1E20]/40 transition-colors">
                        <td className="px-4 py-3 font-sans font-semibold text-text-primary">Row count mismatch</td>
                        <td className="px-4 py-3 text-red-400 font-bold">-20 points</td>
                        <td className="px-4 py-3">row_count_match</td>
                      </tr>
                      <tr className="hover:bg-[#1E1E20]/40 transition-colors">
                        <td className="px-4 py-3 font-sans font-semibold text-text-primary">Checksum mismatch</td>
                        <td className="px-4 py-3 text-red-400 font-bold">-15 points</td>
                        <td className="px-4 py-3">checksum_match</td>
                      </tr>
                      <tr className="hover:bg-[#1E1E20]/40 transition-colors">
                        <td className="px-4 py-3 font-sans font-semibold text-text-primary">Missing primary key</td>
                        <td className="px-4 py-3 text-red-400 font-bold">-10 points</td>
                        <td className="px-4 py-3">pk_exists</td>
                      </tr>
                      <tr className="hover:bg-[#1E1E20]/40 transition-colors">
                        <td className="px-4 py-3 font-sans font-semibold text-text-primary">Missing foreign keys</td>
                        <td className="px-4 py-3 text-red-400 font-bold">-5 points per FK</td>
                        <td className="px-4 py-3">missing_fks</td>
                      </tr>
                      <tr className="hover:bg-[#1E1E20]/40 transition-colors">
                        <td className="px-4 py-3 font-sans font-semibold text-text-primary">Missing indexes</td>
                        <td className="px-4 py-3 text-red-400 font-bold">-3 points per Index</td>
                        <td className="px-4 py-3">missing_indexes</td>
                      </tr>
                      <tr className="hover:bg-[#1E1E20]/40 transition-colors">
                        <td className="px-4 py-3 font-sans font-semibold text-text-primary">Missing check constraints</td>
                        <td className="px-4 py-3 text-red-400 font-bold">-2 points per Constraint</td>
                        <td className="px-4 py-3">missing_constraints</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  )
}
