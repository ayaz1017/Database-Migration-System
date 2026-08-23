import React from 'react'
import { motion, useReducedMotion } from 'framer-motion'

export default function EmptyState({ 
  icon: Icon, 
  title, 
  description, 
  actionLabel, 
  onAction,
  secondaryActionLabel,
  onSecondaryAction 
}) {
  const shouldReduceMotion = useReducedMotion()

  return (
    <motion.div 
      initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 200, damping: 25 }}
      className="flex flex-col items-center justify-center text-center p-12 bg-bg-panel/40 border border-border-card rounded-2xl max-w-lg mx-auto"
    >
      <div className="w-16 h-16 rounded-2xl bg-accent-solid/5 border border-accent-border/20 flex items-center justify-center mb-6 relative">
        {/* Glow effect */}
        <div className="absolute inset-0 rounded-2xl bg-accent-solid/10 blur-xl opacity-40"></div>
        {Icon && <Icon className="w-8 h-8 text-accent-solid relative z-10" />}
      </div>

      <h3 className="font-sans text-h4 font-semibold text-stark-white tracking-tight mb-2">
        {title}
      </h3>
      
      <p className="font-sans text-body-sm text-muted-slate mb-6 leading-relaxed max-w-sm">
        {description}
      </p>

      {(actionLabel || secondaryActionLabel) && (
        <div className="flex flex-wrap items-center justify-center gap-3">
          {actionLabel && (
            <motion.button
              whileHover={shouldReduceMotion ? {} : { scale: 1.02 }}
              whileTap={shouldReduceMotion ? {} : { scale: 0.98 }}
              onClick={onAction}
              className="px-4 py-2.5 bg-accent-solid hover:bg-accent-hover text-stark-white text-xs font-semibold rounded-lg shadow-lg shadow-accent-glow/20 transition-all focus:outline-none focus:ring-2 focus:ring-accent-solid"
            >
              {actionLabel}
            </motion.button>
          )}

          {secondaryActionLabel && (
            <motion.button
              whileHover={shouldReduceMotion ? {} : { scale: 1.02 }}
              whileTap={shouldReduceMotion ? {} : { scale: 0.98 }}
              onClick={onSecondaryAction}
              className="px-4 py-2.5 bg-bg-card hover:bg-bg-popover border border-border-card text-muted-slate hover:text-stark-white text-xs font-semibold rounded-lg transition-all focus:outline-none focus:ring-2 focus:ring-border-focus"
            >
              {secondaryActionLabel}
            </motion.button>
          )}
        </div>
      )}
    </motion.div>
  )
}
