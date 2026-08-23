import React, { useEffect, useState } from 'react'
import { animate, useReducedMotion } from 'framer-motion'

export default function AnimatedCounter({ value, duration = 1.2, formatter = (v) => v.toLocaleString() }) {
  const [displayValue, setDisplayValue] = useState(0)
  const shouldReduceMotion = useReducedMotion()

  useEffect(() => {
    if (shouldReduceMotion) {
      setDisplayValue(value)
      return
    }

    const controls = animate(0, value, {
      duration,
      ease: 'easeOut',
      onUpdate: (latest) => {
        setDisplayValue(Math.round(latest))
      }
    })

    return () => controls.stop()
  }, [value, duration, shouldReduceMotion])

  return <span>{formatter(displayValue)}</span>
}
