import React, { useEffect } from 'react'
import { Database, ArrowLeft, Shield, ChevronDown, MessageCircle } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function AuthLayout({ children }) {
  // Seamlessly adapt body background for light auth experience
  useEffect(() => {
    const origBg = document.body.style.backgroundColor
    const origBgImg = document.body.style.backgroundImage
    const origColor = document.body.style.color

    document.body.style.backgroundColor = '#ffffff'
    document.body.style.backgroundImage = 'none'
    document.body.style.color = '#1e293b'

    return () => {
      document.body.style.backgroundColor = origBg
      document.body.style.backgroundImage = origBgImg
      document.body.style.color = origColor
    }
  }, [])

  return (
    <div className="w-full min-h-screen flex-1 bg-white flex flex-col lg:flex-row font-sans selection:bg-[#242d76]/10 selection:text-[#242d76] relative overflow-x-hidden">
      
      {/* LEFT PANEL (Desktop only): Visual illustration with organic wave divider */}
      <div className="hidden lg:flex lg:w-[46%] xl:w-[48%] relative flex-col justify-between p-8 xl:p-12 overflow-hidden bg-gradient-to-br from-[#eff3fb] via-[#e5ecf8] to-[#dce5f6] self-stretch min-h-screen">
        
        {/* Top brand header */}
        <div className="relative z-10 flex items-center justify-between">
          <Link to="/" className="flex items-center space-x-2.5 group">
            <div className="w-8 h-8 rounded-lg bg-white border border-slate-200 shadow-xs flex items-center justify-center text-[#242d76] group-hover:border-[#242d76]/40 transition-colors">
              <Database className="w-4 h-4" />
            </div>
            <span className="font-sans text-sm font-bold tracking-tight text-[#1e2768]">Fluxline</span>
          </Link>
        </div>

        {/* Center: Database 3D Isometric Illustration in elevated showcase card */}
        <div className="relative z-10 my-auto flex flex-col items-center text-center px-4 py-6 w-full max-w-[420px] mx-auto">
          <div className="w-full bg-white rounded-2xl p-6 xl:p-8 shadow-xl shadow-slate-300/40 border border-slate-200/80 transition-all hover:shadow-2xl hover:shadow-slate-300/50">
            
            {/* Engine Live Status Bar */}
            <div className="flex items-center justify-between mb-4 border-b border-slate-100 pb-3">
              <div className="flex items-center space-x-2">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
                <span className="text-xs font-semibold text-slate-700">Migration Engine Live</span>
              </div>
              <span className="text-[11px] font-medium text-slate-400">AST Keyset Stream</span>
            </div>

            {/* Database 3D Graphic */}
            <img 
              src="/images/database-illustration.jpg" 
              alt="Database Migration Engine" 
              className="w-full h-auto max-h-[260px] xl:max-h-[290px] object-contain mx-auto select-none pointer-events-none"
            />
          </div>

          {/* Subtitle & Value Proposition */}
          <div className="mt-6 max-w-sm">
            <h2 className="text-base xl:text-lg font-bold text-[#1e2768] tracking-tight">
              Zero-Downtime Migration Engine
            </h2>
            <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">
              Automated schema AST translation, real-time parity verification, and high-throughput keyset replication.
            </p>
          </div>
        </div>

        {/* Bottom Trust & Reliability Badge */}
        <div className="relative z-10 flex items-center space-x-2 text-xs text-slate-500">
          <Shield className="w-3.5 h-3.5 text-[#242d76]" />
          <span>Read-only source isolation • Keyset pagination • AES-256</span>
        </div>

        {/* Organic S-Curve Wave Divider (matches reference image) */}
        <div className="absolute top-0 bottom-0 -right-[1px] w-16 xl:w-24 pointer-events-none z-20 h-full">
          <svg 
            viewBox="0 0 100 1000" 
            preserveAspectRatio="none" 
            className="w-full h-full fill-white"
            xmlns="http://www.w3.org/2000/svg"
          >
            {/* White area covers the right side; curve boundary defines the smooth wave shape */}
            <path d="M 100,0 L 40,0 C 40,180 85,340 85,490 C 85,640 15,820 40,1000 L 100,1000 Z" />
          </svg>
        </div>

      </div>

      {/* RIGHT PANEL: Pure White Container for Login / Auth Forms */}
      <div className="flex-1 w-full bg-white flex flex-col justify-between p-4 sm:p-8 lg:p-12 xl:p-16 min-h-screen relative z-10 self-stretch">
        
        {/* Top Navigation */}
        <div className="w-full max-w-[360px] sm:max-w-[380px] mx-auto flex items-center justify-end">
          <Link 
            to="/" 
            className="text-xs text-slate-500 hover:text-slate-800 flex items-center space-x-1.5 transition-colors font-medium py-1 px-2.5 rounded-md hover:bg-slate-100"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to website</span>
          </Link>
        </div>

        {/* Form Container */}
        <div className="my-auto w-full max-w-[360px] sm:max-w-[380px] mx-auto py-4">
          {children}
        </div>

        {/* Footer Row (matching reference: English (US) ▾ & Get Support) */}
        <div className="w-full max-w-[360px] sm:max-w-[380px] mx-auto flex items-center justify-between text-xs text-slate-500 pt-5 border-t border-slate-100">
          <div className="flex items-center space-x-1.5 text-slate-500 hover:text-slate-800 cursor-pointer select-none transition-colors">
            <span>English (US)</span>
            <ChevronDown className="w-3 h-3 text-slate-400" />
          </div>

          <a 
            href="mailto:support@fluxline.dev" 
            className="flex items-center space-x-1.5 text-slate-500 hover:text-slate-800 transition-colors"
          >
            <MessageCircle className="w-3.5 h-3.5 text-slate-400" />
            <span>Get Support</span>
          </a>
        </div>

      </div>

    </div>
  )
}
