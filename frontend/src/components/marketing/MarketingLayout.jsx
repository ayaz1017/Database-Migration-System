import React, { useEffect } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import MarketingHeader from './MarketingHeader'
import MarketingFooter from './MarketingFooter'

export default function MarketingLayout() {
  const { pathname } = useLocation()

  // Scroll restoration on route change
  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' })
  }, [pathname])

  return (
    <div className="min-h-screen bg-[#09090b] text-zinc-100 font-sans relative overflow-x-hidden selection:bg-indigo-500/30 selection:text-white flex flex-col">
      
      {/* Refined Ambient Background Grid & Vignette */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
        {/* Top subtle radial highlight */}
        <div 
          className="absolute top-0 left-1/2 -translate-x-1/2 w-[1100px] h-[500px] opacity-40"
          style={{
            background: 'radial-gradient(ellipse 60% 50% at 50% 0%, rgba(99, 102, 241, 0.15), transparent 100%)'
          }}
        />

        {/* Crisp subtle dot grid */}
        <div 
          className="absolute inset-0 opacity-[0.035]" 
          style={{ 
            backgroundImage: `radial-gradient(#ffffff 1px, transparent 1px)`, 
            backgroundSize: '24px 24px' 
          }} 
        />

        {/* Bottom subtle edge fade */}
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-[#09090b]/80" />
      </div>

      {/* Sticky Global Header */}
      <div className="relative z-50">
        <MarketingHeader />
      </div>

      {/* Main Content Area */}
      <main className="relative z-10 flex-1 flex flex-col min-h-screen">
        <AnimatePresence mode="wait">
          <motion.div
            key={pathname}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
            className="flex-1 flex flex-col"
          >
            <Outlet />
          </motion.div>
        </AnimatePresence>
      </main>

      {/* Global Footer */}
      <div className="relative z-40 mt-auto">
        <MarketingFooter />
      </div>

    </div>
  )
}
