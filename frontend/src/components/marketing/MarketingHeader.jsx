import React, { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Database, Shield, Zap, RefreshCw, BarChart3, Server, Lock, Search, Terminal, ArrowRight } from 'lucide-react'
import MegaMenu from './MegaMenu'
import CommandPalette from '../CommandPalette'

const PRODUCT_ITEMS = [
  { name: 'Migration Engine', description: 'Zero-downtime cross-dialect streaming replication', icon: Database, href: '/docs' },
  { name: 'AST Schema Compiler', description: 'Type-safe DDL translation across all major engines', icon: RefreshCw, href: '/docs' },
  { name: 'Parity & Checksum Validator', description: 'Byte-for-byte row and constraint verification', icon: Shield, href: '/docs' },
  { name: 'CDC Log Streaming', description: 'Real-time WAL and binlog change data capture', icon: Zap, href: '/docs', isNew: true },
]

const SOLUTIONS_ITEMS = [
  { name: 'Enterprise Infrastructure', description: 'Air-gapped and SOC2-compliant VPC deployments', icon: Lock, href: '/pricing' },
  { name: 'Financial Ledgers', description: 'Deterministic ACID migration with zero loss guarantees', icon: BarChart3, href: '/pricing' },
  { name: 'Cloud Migration', description: 'Fast on-prem SQL Server/Oracle to Cloud Postgres/MySQL', icon: Server, href: '/pricing' },
  { name: 'CI/CD & GitOps', description: 'Automated ephemeral staging branch migrations', icon: Terminal, href: '/docs' },
]

export default function MarketingHeader() {
  const [isScrolled, setIsScrolled] = useState(false)
  const [activeMenu, setActiveMenu] = useState(null)
  const [cmdPaletteOpen, setCmdPaletteOpen] = useState(false)
  const { pathname } = useLocation()

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 15)
    }
    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <>
      <header className={`
        fixed top-0 left-0 right-0 z-50 transition-all duration-200 border-b
        ${isScrolled 
          ? 'bg-[#09090b]/90 backdrop-blur-md border-white/[0.08] py-3 shadow-lg shadow-black/30' 
          : 'bg-transparent border-transparent py-4'}
      `}>
        <div className="max-w-[1360px] mx-auto px-6 md:px-10 flex items-center justify-between">
          
          {/* Brand */}
          <div className="flex items-center space-x-6">
            <Link to="/" className="flex items-center space-x-3 group relative z-10" onClick={() => setActiveMenu(null)}>
              <div className="w-9 h-9 rounded-lg bg-zinc-900 border border-white/10 flex items-center justify-center text-zinc-100 group-hover:border-indigo-500/50 group-hover:text-indigo-400 transition-all shadow-sm">
                <Database className="w-4 h-4 text-indigo-400" />
              </div>
              <div className="flex items-center space-x-2">
                <span className="font-sans text-[17px] font-bold tracking-tight text-white">
                  Fluxline
                </span>
                <span className="hidden sm:inline-flex px-1.5 py-0.5 text-[10px] font-mono font-medium text-zinc-400 bg-zinc-800/80 rounded border border-zinc-700/60">
                  v2.4
                </span>
              </div>
            </Link>

            {/* Live Operational Status Pill */}
            <div className="hidden 2xl:flex items-center space-x-2 px-2.5 py-1 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-[11px] font-mono font-medium text-emerald-400 shrink-0">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>Engines Operational</span>
            </div>
          </div>

          {/* Desktop Nav */}
          <nav className="hidden lg:flex items-center space-x-1">
            <MegaMenu 
              title="Product" 
              items={PRODUCT_ITEMS} 
              isOpen={activeMenu === 'product'}
              onMouseEnter={() => setActiveMenu('product')}
              onMouseLeave={() => setActiveMenu(null)}
            />
            <MegaMenu 
              title="Solutions" 
              items={SOLUTIONS_ITEMS} 
              isOpen={activeMenu === 'solutions'}
              onMouseEnter={() => setActiveMenu('solutions')}
              onMouseLeave={() => setActiveMenu(null)}
            />
            <Link 
              to="/architecture"
              className={`px-3 py-1.5 rounded-md font-sans text-sm font-medium transition-colors ${pathname === '/architecture' ? 'text-white bg-white/10' : 'text-zinc-400 hover:text-white hover:bg-white/[0.04]'}`}
              onMouseEnter={() => setActiveMenu(null)}
            >
              Architecture
            </Link>
            <Link 
              to="/pricing"
              className={`px-3 py-1.5 rounded-md font-sans text-sm font-medium transition-colors ${pathname === '/pricing' ? 'text-white bg-white/10' : 'text-zinc-400 hover:text-white hover:bg-white/[0.04]'}`}
              onMouseEnter={() => setActiveMenu(null)}
            >
              Pricing
            </Link>
            <Link 
              to="/sandbox"
              className={`px-3 py-1.5 rounded-md font-sans text-sm font-medium transition-colors ${pathname === '/sandbox' ? 'text-white bg-white/10' : 'text-zinc-400 hover:text-white hover:bg-white/[0.04]'}`}
              onMouseEnter={() => setActiveMenu(null)}
            >
              SQL Lab
            </Link>
            <Link 
              to="/docs"
              className={`px-3 py-1.5 rounded-md font-sans text-sm font-medium transition-colors ${pathname === '/docs' ? 'text-white bg-white/10' : 'text-zinc-400 hover:text-white hover:bg-white/[0.04]'}`}
              onMouseEnter={() => setActiveMenu(null)}
            >
              Docs
            </Link>
          </nav>

          {/* CTAs & Command Search */}
          <div className="flex items-center space-x-3 z-10" onMouseEnter={() => setActiveMenu(null)}>
            <button
              onClick={() => setCmdPaletteOpen(true)}
              className="hidden sm:flex items-center space-x-2 px-2.5 py-1.5 rounded-lg bg-zinc-900/90 hover:bg-zinc-800 border border-zinc-800 text-xs text-zinc-400 hover:text-zinc-200 transition-all cursor-pointer shadow-sm"
              title="Search commands (Ctrl+K)"
            >
              <Search className="w-3.5 h-3.5" />
              <span>Search...</span>
              <kbd className="px-1.5 py-0.5 bg-zinc-800 rounded text-[10px] text-zinc-400 border border-zinc-700">Ctrl K</kbd>
            </button>

            <Link 
              to="/login"
              className="hidden md:block font-sans text-sm font-medium text-zinc-400 hover:text-white transition-colors px-2.5 py-1.5"
            >
              Sign In
            </Link>
            
            <Link 
              to="/app"
              className="px-4 py-2 rounded-lg font-sans text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 transition-all shadow-sm flex items-center space-x-1.5"
            >
              <span>Console</span>
            </Link>
          </div>

        </div>
      </header>

      <CommandPalette 
        isOpen={cmdPaletteOpen} 
        onClose={() => setCmdPaletteOpen(false)} 
        currentTheme="dark"
      />
    </>
  )
}

