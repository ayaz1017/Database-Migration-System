import { motion } from 'framer-motion'
import VolumeCalculator from '../components/Pricing/VolumeCalculator'
import PricingCards from '../components/Pricing/PricingCards'

export default function Pricing() {
  return (
    <div className="min-h-screen bg-[#09090b] relative overflow-hidden custom-scrollbar pb-20">
      {/* Main Container */}
      <div className="relative z-10 w-full max-w-6xl mx-auto px-6 pt-24 pb-12 flex flex-col min-h-screen">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="text-center"
        >
          <div className="inline-flex items-center space-x-2 bg-zinc-900 border border-zinc-800 px-3 py-1 rounded-full text-zinc-300 font-mono text-xs font-medium mb-4">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
            <span>TRANSPARENT PRICING</span>
          </div>
          <h1 className="font-sans text-3xl sm:text-4xl font-bold text-white tracking-tight mb-3">
            Predictable pricing for data engineering teams.
          </h1>
          <p className="font-sans text-sm text-zinc-400 max-w-xl mx-auto">
            Pay only for what you stream. No hidden egress charges, no row count caps, with full self-hosted air-gapped options.
          </p>
        </motion.div>

        {/* Pricing Components */}
        <div className="w-full">
          <PricingCards />
          <VolumeCalculator />
        </div>
      </div>
    </div>
  )
}
