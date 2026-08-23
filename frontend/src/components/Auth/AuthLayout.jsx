import React from 'react'
import { motion } from 'framer-motion'
import { Database, CheckCircle2, ShieldCheck, Zap, Terminal, ArrowLeft } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function AuthLayout({ children }) {
  return (
    <div className="min-h-screen bg-[#09090b] flex flex-col md:flex-row font-sans selection:bg-indigo-500/30 selection:text-white">
      
      {/* Left Developer Showcase Panel (Hidden on Mobile) */}
      <div className="hidden md:flex md:w-1/2 lg:w-[46%] relative bg-[#0d0d11] border-r border-zinc-800/80 overflow-hidden flex-col justify-between p-10 lg:p-14">
        
        {/* Subtle background grid */}
        <div className="absolute inset-0 pointer-events-none z-0">
          <div 
            className="absolute inset-0 opacity-[0.035]" 
            style={{ backgroundImage: `radial-gradient(#ffffff 1px, transparent 1px)`, backgroundSize: '24px 24px' }} 
          />
          <div className="absolute top-0 left-0 w-full h-[300px] bg-gradient-to-b from-indigo-500/10 to-transparent opacity-50" />
        </div>

        {/* Top Brand & Back to Home */}
        <div className="relative z-10 flex items-center justify-between">
          <Link to="/" className="flex items-center space-x-2.5 group w-fit">
            <div className="w-8 h-8 rounded-lg bg-zinc-900 border border-zinc-700 flex items-center justify-center text-indigo-400 group-hover:border-indigo-500/50 transition-colors shadow-sm">
              <Database className="w-4 h-4" />
            </div>
            <span className="font-sans text-base font-bold tracking-tight text-white">Fluxline</span>
          </Link>

          <Link to="/" className="text-xs font-mono text-zinc-400 hover:text-zinc-200 flex items-center space-x-1 transition-colors">
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>fluxline.io</span>
          </Link>
        </div>

        {/* Middle Code/Terminal Preview */}
        <div className="relative z-10 my-8">
          <div className="rounded-xl border border-zinc-800 bg-[#09090c] shadow-xl overflow-hidden font-mono text-xs">
            <div className="h-8 bg-zinc-900/80 border-b border-zinc-800 flex items-center justify-between px-3">
              <div className="flex items-center space-x-1.5">
                <div className="w-2 h-2 rounded-full bg-zinc-700" />
                <div className="w-2 h-2 rounded-full bg-zinc-700" />
                <div className="w-2 h-2 rounded-full bg-zinc-700" />
                <span className="text-[10px] text-zinc-500 ml-2">migration-agent.log</span>
              </div>
              <span className="text-[10px] text-emerald-400 font-medium">● 34.2k rows/s</span>
            </div>
            <div className="p-4 text-zinc-300 space-y-1.5 leading-relaxed text-[11px]">
              <div className="text-zinc-500">// Compiled AST Schema & Parity Digest</div>
              <div><span className="text-indigo-400">source:</span> "PostgreSQL 16 (45M rows)"</div>
              <div><span className="text-emerald-400">target:</span> "MySQL 8.0 Aurora Cluster"</div>
              <div><span className="text-sky-400">mode:</span> "Parallel Keyset Stream (8 workers)"</div>
              <div className="pt-1.5 text-zinc-400">
                [10:42:19] Keyset chunk #3412 flushed (100% SHA-256 match)
              </div>
              <div className="text-emerald-400 font-semibold">
                ✓ Zero constraint locks • 0 downtime cutover active
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Feature Summary & Testimonial */}
        <div className="relative z-10 space-y-4">
          <div className="space-y-2 text-xs text-zinc-300">
            <div className="flex items-center space-x-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              <span>Deterministic AST DDL type translation</span>
            </div>
            <div className="flex items-center space-x-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              <span>Parallel keyset streaming (35k+ rows/s)</span>
            </div>
            <div className="flex items-center space-x-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              <span>Byte-for-byte SHA256 parity verification</span>
            </div>
          </div>

          <div className="pt-4 border-t border-zinc-800/80 text-xs text-zinc-400 italic">
            "Fluxline gave us the confidence to migrate our 180M row financial database over a weekend without downtime."
            <div className="mt-1 not-italic font-mono text-[11px] text-zinc-500">— Staff Data Architect, Series B Fintech</div>
          </div>
        </div>

      </div>

      {/* Right Auth Form Panel */}
      <div className="flex-1 flex flex-col relative items-center justify-center p-6 sm:p-12 min-h-screen bg-[#09090b]">
        
        {/* Mobile Brand Header */}
        <div className="md:hidden w-full max-w-[400px] mb-6 flex items-center justify-between">
          <Link to="/" className="flex items-center space-x-2">
            <div className="w-7 h-7 rounded-md bg-zinc-900 border border-zinc-700 flex items-center justify-center text-indigo-400">
              <Database className="w-3.5 h-3.5" />
            </div>
            <span className="font-sans text-sm font-bold text-white">Fluxline</span>
          </Link>
          <Link to="/" className="text-xs text-zinc-400 hover:text-white">Back to Home</Link>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
          className="w-full max-w-[400px] relative z-10"
        >
          {children}
        </motion.div>

      </div>
    </div>
  )
}
