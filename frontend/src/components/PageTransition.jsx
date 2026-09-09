import React from 'react'
import { motion, useReducedMotion } from 'framer-motion'

export default function PageTransition({ children }) {
  const shouldReduceMotion = useReducedMotion()

  return (
    <motion.div
      initial={shouldReduceMotion ? { opacity: 1 } : { opacity: 0 }}
      animate={shouldReduceMotion ? { opacity: 1 } : { opacity: 1 }}
      exit={shouldReduceMotion ? { opacity: 1 } : { opacity: 0 }}
      transition={{ duration: shouldReduceMotion ? 0 : 0.2, ease: 'easeInOut' }}
      className="w-full min-h-screen flex flex-col flex-1"
    >
      {children}
    </motion.div>
  )
}
