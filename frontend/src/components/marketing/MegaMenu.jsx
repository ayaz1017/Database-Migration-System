import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronRight } from 'lucide-react'

export default function MegaMenu({ title, items, isOpen, onMouseEnter, onMouseLeave }) {
  return (
    <div 
      className="relative group"
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      <button className={`
        flex items-center space-x-1 px-3 py-1.5 rounded-md font-sans text-sm font-medium transition-colors cursor-pointer
        ${isOpen ? 'text-white bg-white/[0.08]' : 'text-zinc-400 hover:text-white hover:bg-white/[0.04]'}
      `}>
        <span>{title}</span>
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 6, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 6, scale: 0.98 }}
            transition={{ duration: 0.15, ease: 'easeOut' }}
            className="absolute top-full left-1/2 -translate-x-1/2 mt-2 w-[580px] bg-[#121216] border border-zinc-800 rounded-xl shadow-xl p-5 overflow-hidden origin-top z-50 ring-1 ring-white/[0.04]"
          >
            <div className="relative z-10 grid grid-cols-2 gap-x-6 gap-y-4">
              {items.map((item, idx) => (
                <a
                  key={idx}
                  href={item.href}
                  className="group/item flex items-start space-x-3 p-2.5 rounded-lg hover:bg-zinc-800/60 transition-colors"
                >
                  <div className="mt-0.5 flex-shrink-0 w-8 h-8 rounded-md bg-zinc-800/80 border border-zinc-700/60 flex items-center justify-center text-zinc-400 group-hover/item:text-indigo-400 group-hover/item:border-indigo-500/30 group-hover/item:bg-indigo-500/10 transition-colors">
                    <item.icon className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="flex items-center font-sans font-medium text-sm text-zinc-200 group-hover/item:text-white transition-colors">
                      {item.name}
                      {item.isNew && (
                        <span className="ml-2 px-1.5 py-0.2 text-[9px] uppercase font-mono font-bold tracking-wider text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 rounded">New</span>
                      )}
                    </div>
                    <p className="mt-0.5 font-sans text-xs text-zinc-500 leading-snug group-hover/item:text-zinc-400 transition-colors">
                      {item.description}
                    </p>
                  </div>
                </a>
              ))}
            </div>

            {/* Bottom docs link block */}
            <div className="relative z-10 mt-4 pt-3.5 border-t border-zinc-800/80 flex items-center justify-between">
              <p className="text-xs text-zinc-500">Need architectural specifications?</p>
              <a href="/docs" className="flex items-center text-xs font-medium text-indigo-400 hover:text-indigo-300 transition-colors group/cta">
                View DDL Engine Specs 
                <ChevronRight className="w-3.5 h-3.5 ml-1 group-hover/cta:translate-x-0.5 transition-transform" />
              </a>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
