import React from 'react'

export default function Skeleton({ className = '', variant = 'rect', width, height }) {
  const styles = {
    width: width || undefined,
    height: height || undefined,
  }

  const baseClass = 'bg-white/[0.04] animate-pulse'
  const variantClass = 
    variant === 'circle' ? 'rounded-full' :
    variant === 'card' ? 'rounded-2xl border border-white/5 bg-[#13131A]/30' :
    'rounded-lg'

  return (
    <div 
      className={`${baseClass} ${variantClass} ${className}`} 
      style={styles}
      role="progressbar"
      aria-valuemin="0"
      aria-valuemax="100"
      aria-label="Loading workspace components..."
    />
  )
}

export function SkeletonGrid({ count = 3, cols = 1, className = '', height = '100px' }) {
  return (
    <div className={`grid gap-4 grid-cols-${cols} ${className}`}>
      {Array.from({ length: count }).map((_, i) => (
        <Skeleton key={i} variant="card" height={height} />
      ))}
    </div>
  )
}
