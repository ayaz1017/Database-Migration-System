import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Check, Shield, Zap, Building2, ArrowRight } from 'lucide-react'

const TIERS = [
  {
    name: 'Developer',
    icon: Zap,
    priceMonthly: 49,
    priceYearly: 39,
    description: 'For small engineering teams running self-serve database migrations.',
    features: [
      'Up to 100GB Streaming Transfer',
      'PostgreSQL, MySQL & SQLite Engines',
      'Standard CDC Sync (< 1s latency)',
      'Automated DDL Schema Discovery',
      'Community & Standard Support'
    ],
    color: 'text-sky-400',
    border: 'border-zinc-800 hover:border-zinc-700',
    bg: 'bg-zinc-900/40'
  },
  {
    name: 'Team & Cluster',
    icon: Shield,
    priceMonthly: 249,
    priceYearly: 199,
    description: 'For high-throughput production cutovers with live continuous replication.',
    features: [
      'Up to 5TB Streaming Transfer',
      'All SQL Engines + Oracle & SQL Server',
      'Sub-millisecond Keyset CDC Streaming',
      'AST Dialect Compiler & Pre-flight Validator',
      'Byte-for-Byte SHA256 Checksum Parity',
      'Priority Engineering Support'
    ],
    color: 'text-indigo-400',
    border: 'border-indigo-500/50 shadow-lg shadow-indigo-950/20',
    bg: 'bg-zinc-900/80',
    isPopular: true
  },
  {
    name: 'Enterprise',
    icon: Building2,
    priceMonthly: 'Custom',
    priceYearly: 'Custom',
    description: 'Mission-critical zero-downtime cutovers with dedicated VPC agents.',
    features: [
      'Unlimited Data Volume & Clusters',
      'Air-Gapped On-Premise Deployments',
      'Custom Dialect Rules & AST Plugins',
      'Dedicated Infrastructure Architect',
      '99.999% SLA Guarantee',
      'SOC2 / HIPAA / ISO Compliance Audit Log'
    ],
    color: 'text-emerald-400',
    border: 'border-zinc-800 hover:border-zinc-700',
    bg: 'bg-zinc-900/40'
  }
]

export default function PricingCards() {
  const [isYearly, setIsYearly] = useState(true)

  return (
    <div className="flex flex-col items-center mt-10">
      {/* Toggle */}
      <div className="flex items-center space-x-3 mb-10">
        <span className={`font-sans text-xs font-medium ${!isYearly ? 'text-white font-semibold' : 'text-zinc-400'}`}>Monthly</span>
        <button 
          onClick={() => setIsYearly(!isYearly)}
          className="w-11 h-6 bg-zinc-800 rounded-full relative p-0.5 transition-colors hover:bg-zinc-700 border border-zinc-700 cursor-pointer"
        >
          <motion.div 
            layout
            className="w-4 h-4 bg-indigo-500 rounded-full shadow"
            animate={{ x: isYearly ? 20 : 0 }}
            transition={{ type: "spring", stiffness: 500, damping: 30 }}
          />
        </button>
        <span className={`font-sans text-xs font-medium flex items-center ${isYearly ? 'text-white font-semibold' : 'text-zinc-400'}`}>
          Yearly <span className="ml-1.5 text-[10px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-1.5 py-0.2 rounded">Save 20%</span>
        </span>
      </div>

      {/* Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-6xl mx-auto">
        {TIERS.map((tier, idx) => (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.08, duration: 0.3 }}
            key={tier.name}
            className={`relative p-6 md:p-7 rounded-xl border transition-all duration-200 flex flex-col ${tier.border} ${tier.bg}`}
          >
            {tier.isPopular && (
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-indigo-600 text-white text-[10px] font-mono font-bold uppercase tracking-wider px-3 py-0.5 rounded-full shadow-sm">
                Recommended
              </div>
            )}
            
            <tier.icon className={`w-6 h-6 mb-4 ${tier.color}`} />
            <h3 className="font-sans text-base font-bold text-white mb-1">{tier.name}</h3>
            <p className="font-sans text-xs text-zinc-400 min-h-[36px] mb-5 leading-relaxed">{tier.description}</p>
            
            <div className="mb-6 flex items-baseline space-x-1">
              {typeof tier.priceMonthly === 'number' ? (
                <>
                  <span className="font-sans text-3xl font-bold text-white tracking-tight">
                    ${isYearly ? tier.priceYearly : tier.priceMonthly}
                  </span>
                  <span className="font-sans text-xs text-zinc-400">/month</span>
                </>
              ) : (
                <span className="font-sans text-3xl font-bold text-white tracking-tight">Custom</span>
              )}
            </div>

            <div className="flex-1">
              <ul className="space-y-3 mb-6">
                {tier.features.map(f => (
                  <li key={f} className="flex items-start space-x-2.5 font-sans text-xs text-zinc-300">
                    <Check className={`w-3.5 h-3.5 shrink-0 mt-0.5 ${tier.color}`} />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
            </div>

            <a 
              href="/app/new"
              className={`w-full py-2.5 rounded-lg font-sans text-xs font-semibold transition-all flex items-center justify-center space-x-1.5 ${
                tier.isPopular 
                  ? 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-sm' 
                  : 'bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-zinc-700'
              }`}
            >
              <span>{tier.priceMonthly === 'Custom' ? 'Contact Solutions' : 'Get Started'}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </a>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
