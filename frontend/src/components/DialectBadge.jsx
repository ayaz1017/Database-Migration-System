import React from 'react'
import { Database } from 'lucide-react'

export function getDialectDetails(dialect) {
  const d = (dialect || '').toLowerCase()
  if (d === 'mssql') {
    return {
      name: 'Microsoft SQL Server',
      shortName: 'MSSQL',
      color: '#F43F5E', // Rose/Red
      bg: 'rgba(244, 63, 94, 0.08)',
      border: 'rgba(244, 63, 94, 0.25)',
      glow: 'rgba(244, 63, 94, 0.3)'
    }
  } else if (d === 'mysql') {
    return {
      name: 'MySQL',
      shortName: 'MySQL',
      color: '#06B6D4', // Cyan
      bg: 'rgba(6, 182, 212, 0.08)',
      border: 'rgba(6, 182, 212, 0.25)',
      glow: 'rgba(6, 182, 212, 0.3)'
    }
  } else if (d === 'postgres' || d === 'postgresql') {
    return {
      name: 'PostgreSQL',
      shortName: 'PostgreSQL',
      color: '#3B82F6', // Blue
      bg: 'rgba(59, 130, 246, 0.08)',
      border: 'rgba(59, 130, 246, 0.25)',
      glow: 'rgba(59, 130, 246, 0.3)'
    }
  } else if (d === 'oracle') {
    return {
      name: 'Oracle Database',
      shortName: 'Oracle',
      color: '#F97316', // Orange
      bg: 'rgba(249, 115, 22, 0.08)',
      border: 'rgba(249, 115, 22, 0.25)',
      glow: 'rgba(249, 115, 22, 0.3)'
    }
  }
  return {
    name: dialect,
    shortName: dialect.toUpperCase(),
    color: '#8B5CF6', // Violet
    bg: 'rgba(139, 92, 246, 0.08)',
    border: 'rgba(139, 92, 246, 0.25)',
    glow: 'rgba(139, 92, 246, 0.3)'
  }
}

export function DialectIcon({ dialect, className = "w-4 h-4", active = true }) {
  const details = getDialectDetails(dialect)
  return (
    <div 
      className="flex items-center justify-center rounded-lg border p-1.5 transition-all"
      style={{ 
        backgroundColor: active ? details.bg : 'rgba(255, 255, 255, 0.01)', 
        borderColor: active ? details.border : 'var(--color-border-card)',
        boxShadow: active ? `0 0 8px ${details.glow}` : 'none'
      }}
      title={details.name}
    >
      <Database className={className} style={{ color: active ? details.color : 'var(--color-muted-slate)' }} />
    </div>
  )
}

export default function DialectBadge({ dialect }) {
  const details = getDialectDetails(dialect)
  return (
    <span 
      className="inline-flex items-center space-x-1.5 py-1 px-2.5 rounded-md border font-mono text-caption font-semibold tracking-wider"
      style={{ 
        backgroundColor: details.bg, 
        borderColor: details.border,
        color: details.color 
      }}
    >
      <Database className="w-3 h-3" />
      <span>{details.shortName}</span>
    </span>
  )
}
