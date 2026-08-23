import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion'
import { Database, CheckSquare, Sparkles, AlertCircle, ArrowRight, ShieldCheck, Play, Pause, ChevronLeft, ChevronRight, HardDrive, Layers, Clock, X } from 'lucide-react'
import { DialectIcon } from '../components/DialectBadge'
import AnimatedCounter from '../components/AnimatedCounter'

export default function Demo({ isOpen, onClose }) {
  const navigate = useNavigate()
  const [step, setStep] = useState(1)
  const [isPlaying, setIsPlaying] = useState(true)
  const shouldReduceMotion = useReducedMotion()

  const totalSteps = 5

  // Auto-advance logic
  useEffect(() => {
    if (!isPlaying) return
    const timer = setInterval(() => {
      setStep(prev => (prev === totalSteps ? 1 : prev + 1))
    }, 7000) // 7 seconds per step

    return () => clearInterval(timer)
  }, [isPlaying])

  const nextStep = () => {
    setStep(prev => (prev === totalSteps ? 1 : prev + 1))
  }

  const prevStep = () => {
    setStep(prev => (prev === 1 ? totalSteps : prev - 1))
  }

  const stepContent = [
    {
      num: 1,
      title: "Connect your databases",
      desc: "Securely input credentials for your source and destination servers. Fluxline auto-detects dialect features, network configurations, and driver constraints instantly."
    },
    {
      num: 2,
      title: "Pick exactly what to migrate",
      desc: "Select schemas, tables, or specific database objects. Our dependency engine automatically includes related foreign key tables with tooltips explaining the relationship."
    },
    {
      num: 3,
      title: "AI agents take over",
      desc: "Specialized agents translate DDL dialects, map proprietary data types, refactor stored procedures, and stream table data dynamically in parallel worker threads."
    },
    {
      num: 4,
      title: "Validation and automatic fixes",
      desc: "Fluxline runs automated integrity tests on the destination schema. If any constraints fail, validation agents invoke SQL generation to self-heal and resolve issues instantly."
    },
    {
      num: 5,
      title: "Get a full verification report",
      desc: "Review final data counts, schema translation reviews, performance metrics, and a total validation accuracy score. You are now ready to switch over production traffic."
    }
  ]

  // Render Step 1 diagram: Connect Databases
  const renderStep1Diagram = () => {
    if (shouldReduceMotion) {
      return (
        <div className="flex items-center justify-center space-x-12 h-64">
          <div className="flex flex-col items-center p-4 bg-bg-card border border-border-card rounded-2xl w-32 shadow-lg">
            <DialectIcon dialect="mssql" className="w-8 h-8 mb-2" />
            <span className="text-xs font-mono font-bold text-stark-white">Source DB</span>
          </div>
          <div className="h-0.5 w-24 bg-accent-solid"></div>
          <div className="flex flex-col items-center p-4 bg-bg-card border border-border-card rounded-2xl w-32 shadow-lg">
            <DialectIcon dialect="postgres" className="w-8 h-8 mb-2" />
            <span className="text-xs font-mono font-bold text-status-info">Target DB</span>
          </div>
        </div>
      )
    }

    return (
      <div className="relative flex items-center justify-center w-full h-64 overflow-hidden">
        {/* Source server */}
        <motion.div 
          initial={{ x: -100, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ type: 'spring', stiffness: 100 }}
          className="flex flex-col items-center p-5 bg-bg-card/60 backdrop-blur-xl border border-border-card rounded-2xl w-36 shadow-xl relative z-10"
        >
          <div className="absolute inset-0 rounded-2xl bg-accent-glow/5 blur-xl -z-10"></div>
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 15, repeat: Infinity, ease: 'linear' }}
            className="w-12 h-12 rounded-full border border-dashed border-accent-solid/40 flex items-center justify-center mb-3"
          >
            <Database className="w-6 h-6 text-accent-solid" />
          </motion.div>
          <span className="text-xs font-bold text-stark-white font-display">Source Server</span>
          <span className="text-[10px] font-mono text-muted-slate mt-1">MSSQL</span>
        </motion.div>

        {/* Animated Connecting Cable */}
        <div className="w-24 h-1 relative overflow-hidden flex items-center">
          <div className="w-full h-0.5 bg-border-card absolute"></div>
          <motion.div 
            initial={{ left: '-100%' }}
            animate={{ left: '100%' }}
            transition={{ repeat: Infinity, duration: 2, ease: 'easeInOut' }}
            className="h-1 w-12 bg-gradient-to-r from-transparent via-accent-solid to-transparent absolute"
          />
        </div>

        {/* Target server */}
        <motion.div 
          initial={{ x: 100, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ type: 'spring', stiffness: 100, delay: 0.2 }}
          className="flex flex-col items-center p-5 bg-bg-card/60 backdrop-blur-xl border border-border-card rounded-2xl w-36 shadow-xl relative z-10"
        >
          <div className="absolute inset-0 rounded-2xl bg-status-info/5 blur-xl -z-10"></div>
          <motion.div
            animate={{ scale: [1, 1.05, 1] }}
            transition={{ duration: 3, repeat: Infinity }}
            className="w-12 h-12 rounded-full border border-dashed border-status-info/40 flex items-center justify-center mb-3"
          >
            <Database className="w-6 h-6 text-status-info" />
          </motion.div>
          <span className="text-xs font-bold text-stark-white font-display">Target Server</span>
          <span className="text-[10px] font-mono text-muted-slate mt-1">PostgreSQL</span>
        </motion.div>

        {/* Floating Dialect Badges in Background */}
        <motion.div 
          animate={{ y: [0, -10, 0] }}
          transition={{ repeat: Infinity, duration: 4, ease: 'easeInOut' }}
          className="absolute top-8 left-[15%] opacity-30"
        >
          <DialectIcon dialect="oracle" />
        </motion.div>
        <motion.div 
          animate={{ y: [0, 10, 0] }}
          transition={{ repeat: Infinity, duration: 5, ease: 'easeInOut', delay: 1 }}
          className="absolute bottom-8 right-[15%] opacity-30"
        >
          <DialectIcon dialect="mysql" />
        </motion.div>
      </div>
    )
  }

  // Render Step 2 diagram: Asset dependency selection
  const renderStep2Diagram = () => {
    if (shouldReduceMotion) {
      return (
        <div className="flex flex-col items-center justify-center space-y-3 h-64">
          <div className="flex items-center space-x-3 bg-bg-card border border-accent-border/30 p-3 rounded-xl w-64 shadow-md">
            <CheckSquare className="w-4 h-4 text-accent-solid" />
            <span className="text-xs font-mono text-stark-white">users</span>
          </div>
          <div className="flex items-center space-x-3 bg-bg-card border border-status-info-border/30 p-3 rounded-xl w-64 shadow-md">
            <CheckSquare className="w-4 h-4 text-status-info" />
            <span className="text-xs font-mono text-stark-white">orders (Auto-Included)</span>
          </div>
        </div>
      )
    }

    return (
      <div className="relative flex flex-col items-center justify-center w-full h-64">
        <div className="space-y-3 max-w-sm w-full relative z-10">
          {/* User Table (Explicitly ticked) */}
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center justify-between p-3.5 bg-bg-card/75 border border-accent-border/30 rounded-xl shadow-md relative"
          >
            <div className="flex items-center space-x-3">
              <motion.div 
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 0.3, delay: 1 }}
                className="w-4 h-4 rounded bg-accent-solid flex items-center justify-center"
              >
                <div className="w-1.5 h-1.5 bg-white rounded-full"></div>
              </motion.div>
              <span className="text-xs font-mono text-stark-white font-bold">users</span>
            </div>
            <span className="text-[9px] font-mono text-accent-solid font-bold uppercase tracking-wider bg-accent-solid/10 px-2 py-0.5 rounded border border-accent-border/20">Selected</span>
          </motion.div>

          {/* Connective Line */}
          <svg className="w-full h-12 overflow-visible select-none pointer-events-none opacity-80" style={{ margin: '-6px 0' }}>
            <motion.path
              d="M 32 0 L 32 24 L 280 24 L 280 48"
              fill="none"
              stroke="var(--color-status-info)"
              strokeWidth="1.5"
              strokeDasharray="4 4"
              initial={{ strokeDashoffset: 100 }}
              animate={{ strokeDashoffset: 0 }}
              transition={{ repeat: Infinity, duration: 4, ease: 'linear' }}
            />
          </svg>

          {/* Orders Table (Auto-Included due to FK) */}
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.5 }}
            className="flex items-center justify-between p-3.5 bg-bg-card/75 border border-status-info-border/30 rounded-xl shadow-md relative"
          >
            <div className="flex items-center space-x-3">
              <div className="w-4 h-4 rounded bg-status-info flex items-center justify-center">
                <div className="w-1.5 h-1.5 bg-white rounded-full"></div>
              </div>
              <span className="text-xs font-mono text-stark-white font-bold">orders</span>
            </div>
            
            {/* Dependency Tooltip */}
            <motion.div 
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 2.2, type: 'spring' }}
              className="absolute top-[-30px] right-2 bg-status-info border border-status-info-border text-white text-[9px] font-mono font-bold px-2 py-0.5 rounded shadow-lg flex items-center space-x-1"
            >
              <AlertCircle className="w-3 h-3" />
              <span>FK: orders.user_id &rarr; users.id</span>
            </motion.div>

            <span className="text-[9px] font-mono text-status-info font-bold uppercase tracking-wider bg-status-info-muted px-2 py-0.5 rounded border border-status-info-border">Auto-Included</span>
          </motion.div>
        </div>
      </div>
    )
  }

  // Render Step 3 diagram: AI Agents pipeline
  const renderStep3Diagram = () => {
    if (shouldReduceMotion) {
      return (
        <div className="flex items-center justify-center space-x-8 h-64">
          <div className="flex flex-col items-center p-3 bg-bg-card border border-border-card rounded-xl text-center w-24">
            <span className="text-xs font-mono font-bold text-accent-solid mb-1">Orchestrator</span>
          </div>
          <div className="flex flex-col items-center p-3 bg-bg-card border border-border-card rounded-xl text-center w-24">
            <span className="text-xs font-mono font-bold text-status-success mb-1">Schema Agent</span>
          </div>
          <div className="flex flex-col items-center p-3 bg-bg-card border border-border-card rounded-xl text-center w-24">
            <span className="text-xs font-mono font-bold text-status-info mb-1">Data Agent</span>
          </div>
        </div>
      )
    }

    return (
      <div className="relative flex items-center justify-center w-full h-64">
        <div className="flex items-center justify-between w-full max-w-lg px-6 relative z-10">
          
          {/* Orchestrator node */}
          <motion.div 
            animate={{ 
              boxShadow: ['0 0 10px rgba(139, 92, 246, 0.2)', '0 0 25px rgba(139, 92, 246, 0.5)', '0 0 10px rgba(139, 92, 246, 0.2)']
            }}
            transition={{ duration: 2, repeat: Infinity }}
            className="flex flex-col items-center justify-center p-4 bg-bg-card border border-accent-solid rounded-2xl w-28 text-center relative"
          >
            <Sparkles className="w-6 h-6 text-accent-solid mb-2" />
            <span className="text-[10px] font-mono font-bold text-stark-white uppercase tracking-wider">Orchestrator</span>
          </motion.div>

          {/* Pipelines */}
          <div className="flex-1 h-0.5 bg-border-card relative mx-4">
            <motion.div 
              animate={{ left: ['0%', '100%'] }}
              transition={{ repeat: Infinity, duration: 1.5, ease: 'linear' }}
              className="absolute top-1/2 -translate-y-1/2 w-2 h-2 rounded-full bg-status-success"
            />
            <motion.div 
              animate={{ left: ['0%', '100%'] }}
              transition={{ repeat: Infinity, duration: 1.5, ease: 'linear', delay: 0.75 }}
              className="absolute top-1/2 -translate-y-1/2 w-2 h-2 rounded-full bg-status-info"
            />
          </div>

          {/* AI Agents column */}
          <div className="flex flex-col space-y-6">
            {/* Schema Agent */}
            <motion.div 
              animate={{ 
                borderColor: ['rgba(16, 185, 129, 0.2)', 'rgba(16, 185, 129, 0.8)', 'rgba(16, 185, 129, 0.2)']
              }}
              transition={{ duration: 2, repeat: Infinity, delay: 0.5 }}
              className="flex items-center space-x-3 p-3 bg-bg-card border border-border-card rounded-xl w-40"
            >
              <HardDrive className="w-5 h-5 text-status-success" />
              <div className="flex flex-col">
                <span className="text-[10px] font-mono font-bold text-stark-white uppercase tracking-wider">Schema Agent</span>
                <span className="text-[9px] text-muted-slate">Translates DDL</span>
              </div>
            </motion.div>

            {/* Data Agent */}
            <motion.div 
              animate={{ 
                borderColor: ['rgba(59, 130, 246, 0.2)', 'rgba(59, 130, 246, 0.8)', 'rgba(59, 130, 246, 0.2)']
              }}
              transition={{ duration: 2, repeat: Infinity, delay: 1 }}
              className="flex items-center space-x-3 p-3 bg-bg-card border border-border-card rounded-xl w-40"
            >
              <Database className="w-5 h-5 text-status-info" />
              <div className="flex flex-col">
                <span className="text-[10px] font-mono font-bold text-stark-white uppercase tracking-wider">Data Agent</span>
                <span className="text-[9px] text-muted-slate">Streams Records</span>
              </div>
            </motion.div>
          </div>

        </div>
      </div>
    )
  }

  // Render Step 4 diagram: Validation and healing
  const renderStep4Diagram = () => {
    if (shouldReduceMotion) {
      return (
        <div className="flex flex-col items-center justify-center space-y-3 h-64">
          <div className="flex items-center space-x-2 text-status-error bg-status-error-muted px-4 py-2 border border-status-error-border rounded-xl">
            <AlertCircle className="w-4 h-4" />
            <span className="text-xs font-mono font-bold">Failed: FK Constraint mismatch</span>
          </div>
          <div className="flex items-center space-x-2 text-status-success bg-status-success-muted px-4 py-2 border border-status-success-border rounded-xl">
            <ShieldCheck className="w-4 h-4" />
            <span className="text-xs font-mono font-bold">AI Healed & Validated successfully</span>
          </div>
        </div>
      )
    }

    return (
      <div className="relative flex flex-col items-center justify-center w-full h-64 overflow-hidden">
        <AnimatePresence mode="wait">
          {/* We cycle through stages of validation: Check -> Fail -> Heal -> Pass */}
          <div className="relative z-10 w-full max-w-sm">
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="bg-bg-panel border border-border-card rounded-2xl p-6 shadow-xl space-y-4"
            >
              {/* Progress bar */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-[10px] font-mono font-bold text-muted-slate">
                  <span>INTEGRITY VERIFICATION</span>
                  <span>100%</span>
                </div>
                <div className="w-full h-1.5 bg-bg-canvas rounded-full overflow-hidden border border-border-card">
                  <motion.div 
                    animate={{ width: ['0%', '100%'] }}
                    transition={{ duration: 2, repeat: Infinity, repeatDelay: 3 }}
                    className="bg-accent-solid h-full"
                  />
                </div>
              </div>

              {/* Status logs */}
              <div className="p-3 bg-bg-card/50 rounded-xl border border-border-card font-mono text-[10px] space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-stark-white">Analyzing target constraints...</span>
                  <span className="text-status-success">PASS</span>
                </div>
                
                {/* Delayed animated logs */}
                <motion.div 
                  animate={{ 
                    opacity: [0, 1, 1, 0],
                    color: ['#F43F5E', '#F43F5E', '#F43F5E', '#F43F5E']
                  }}
                  transition={{ duration: 5, repeat: Infinity }}
                  className="flex items-center justify-between"
                >
                  <span>FK Constraint orders_user_id...</span>
                  <span className="font-bold">FAIL</span>
                </motion.div>

                {/* Auto healing trigger */}
                <motion.div 
                  animate={{ 
                    opacity: [0, 0, 1, 0]
                  }}
                  transition={{ duration: 5, repeat: Infinity }}
                  className="text-accent-solid font-bold flex items-center gap-1.5"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>AI Healing: Adjusting column data types...</span>
                </motion.div>

                {/* Success checkmark draw in */}
                <motion.div 
                  animate={{ 
                    opacity: [0, 0, 0, 1]
                  }}
                  transition={{ duration: 5, repeat: Infinity }}
                  className="flex items-center justify-between text-status-success font-bold"
                >
                  <span>Database check validated:</span>
                  <span className="flex items-center gap-1"><ShieldCheck className="w-3.5 h-3.5" /> SUCCESS</span>
                </motion.div>
              </div>
            </motion.div>
          </div>
        </AnimatePresence>
      </div>
    )
  }

  // Render Step 5 diagram: Full report
  const renderStep5Diagram = () => {
    return (
      <div className="relative flex items-center justify-center w-full h-64">
        <div className="grid grid-cols-2 gap-4 w-full max-w-sm relative z-10">
          {/* Tables card */}
          <motion.div 
            initial={shouldReduceMotion ? {} : { scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="bg-bg-panel border border-border-card rounded-xl p-4 flex flex-col justify-center text-center items-center shadow-md"
          >
            <Layers className="w-5 h-5 text-accent-solid mb-1" />
            <span className="text-[9px] font-mono font-bold text-muted-slate uppercase tracking-wider">Tables Completed</span>
            <span className="text-xl font-mono font-extrabold text-stark-white mt-1">
              <AnimatedCounter value={24} duration={1.5} />
            </span>
          </motion.div>

          {/* Rows card */}
          <motion.div 
            initial={shouldReduceMotion ? {} : { scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="bg-bg-panel border border-border-card rounded-xl p-4 flex flex-col justify-center text-center items-center shadow-md"
          >
            <Database className="w-5 h-5 text-status-info mb-1" />
            <span className="text-[9px] font-mono font-bold text-muted-slate uppercase tracking-wider">Rows Migrated</span>
            <span className="text-xl font-mono font-extrabold text-stark-white mt-1">
              <AnimatedCounter value={142580} duration={1.8} />
            </span>
          </motion.div>

          {/* Duration card */}
          <motion.div 
            initial={shouldReduceMotion ? {} : { scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="bg-bg-panel border border-border-card rounded-xl p-4 flex flex-col justify-center text-center items-center shadow-md"
          >
            <Clock className="w-5 h-5 text-status-warning mb-1" />
            <span className="text-[9px] font-mono font-bold text-muted-slate uppercase tracking-wider">Duration</span>
            <span className="text-xl font-mono font-extrabold text-stark-white mt-1">
              <span>8.45</span>
              <span className="text-xs text-muted-slate ml-0.5">s</span>
            </span>
          </motion.div>

          {/* Score card */}
          <motion.div 
            initial={shouldReduceMotion ? {} : { scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="bg-bg-panel border border-border-card rounded-xl p-4 flex flex-col justify-center text-center items-center shadow-md relative"
          >
            <div className="absolute inset-0 rounded-xl bg-status-success/5 blur-md -z-10"></div>
            <ShieldCheck className="w-5 h-5 text-status-success mb-1" />
            <span className="text-[9px] font-mono font-bold text-muted-slate uppercase tracking-wider">Accuracy Score</span>
            <span className="text-xl font-mono font-extrabold text-status-success mt-1">
              <AnimatedCounter value={100} duration={1.2} />
              <span className="text-xs font-sans ml-0.5">%</span>
            </span>
          </motion.div>
        </div>
      </div>
    )
  }

  // Determine which diagram to render based on current step
  const renderDiagram = () => {
    switch (step) {
      case 1: return renderStep1Diagram()
      case 2: return renderStep2Diagram()
      case 3: return renderStep3Diagram()
      case 4: return renderStep4Diagram()
      case 5: return renderStep5Diagram()
      default: return null
    }
  }

  if (isOpen !== undefined) {
    if (!isOpen) return null
    return (
      <AnimatePresence>
        <div className="fixed inset-0 z-[100] flex justify-end print:hidden">
          {/* Backdrop */}
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm"
          />
          
          {/* Slider Drawer */}
          <motion.div 
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="relative w-full max-w-xl bg-bg-panel border-l border-border-card p-6 flex flex-col h-full z-10 shadow-2xl overflow-y-auto pr-4 scrollbar-thin scrollbar-thumb-border-card"
          >
             {/* Drawer Header */}
             <div className="flex items-center justify-between pb-4 border-b border-border-card/60 mb-6 shrink-0">
               <div className="flex items-center space-x-2">
                 <Sparkles className="w-4 h-4 text-accent-solid animate-pulse" />
                 <h2 className="text-sm font-mono font-black text-stark-white uppercase tracking-wider">How Fluxline Works</h2>
               </div>
               <button onClick={onClose} className="p-1 rounded-lg hover:bg-bg-card border border-transparent hover:border-border-card text-muted-slate hover:text-stark-white transition-colors cursor-pointer">
                 <X className="w-5 h-5" />
               </button>
             </div>

             {/* Playback Controls */}
             <div className="flex justify-end mb-4 shrink-0">
               <button 
                 onClick={() => setIsPlaying(!isPlaying)}
                 className="px-3 py-1.5 bg-bg-card hover:bg-bg-popover border border-border-card rounded-lg text-muted-slate hover:text-stark-white transition-all text-[10px] flex items-center gap-1.5 cursor-pointer font-mono font-bold"
               >
                 {isPlaying ? (
                   <>
                     <Pause className="w-3.5 h-3.5 text-accent-solid" />
                     <span>PAUSE</span>
                   </>
                 ) : (
                   <>
                     <Play className="w-3.5 h-3.5 text-status-success animate-pulse" />
                     <span>AUTOPLAY</span>
                   </>
                 )}
               </button>
             </div>

             {/* Diagram Viewport (Stacked) */}
             <div className="bg-bg-canvas/60 border border-border-card/60 rounded-xl h-60 flex items-center justify-center relative overflow-hidden shadow-inner mb-6 shrink-0">
               <div className="absolute inset-0 bg-transparent opacity-10" style={{ 
                 backgroundImage: `radial-gradient(rgba(255, 255, 255, 0.15) 1px, transparent 1px)`,
                 backgroundSize: '20px 20px'
               }}></div>
               
               <AnimatePresence mode="wait">
                 <motion.div 
                   key={step}
                   initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, scale: 0.95 }}
                   animate={{ opacity: 1, scale: 1 }}
                   exit={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, scale: 0.95 }}
                   transition={{ duration: 0.35, ease: 'easeOut' }}
                   className="w-full h-full flex items-center justify-center"
                 >
                   {renderDiagram()}
                 </motion.div>
               </AnimatePresence>
             </div>

             {/* Step Content */}
             <div className="flex-1 flex flex-col justify-between min-h-[220px]">
               <div className="space-y-3">
                 <div className="flex items-center space-x-2">
                   <span className="w-5 h-5 rounded bg-accent-solid flex items-center justify-center text-[10px] font-mono font-bold text-white shadow-md">
                     {stepContent[step - 1].num}
                   </span>
                   <span className="text-[9px] font-mono text-accent-solid font-bold uppercase tracking-wider">Step {step} of {totalSteps}</span>
                 </div>
                 
                 <AnimatePresence mode="wait">
                   <motion.div
                     key={step}
                     initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, x: 10 }}
                     animate={{ opacity: 1, x: 0 }}
                     exit={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, x: -10 }}
                     transition={{ duration: 0.2 }}
                     className="space-y-2"
                   >
                     <h3 className="text-h3 font-sans font-semibold text-stark-white tracking-tight">
                       {stepContent[step - 1].title}
                     </h3>
                     <p className="font-sans text-body-sm text-muted-slate leading-relaxed">
                       {stepContent[step - 1].desc}
                     </p>
                   </motion.div>
                 </AnimatePresence>
               </div>

               {/* Controls */}
               <div className="space-y-4 pt-4 border-t border-border-card/60 mt-6 shrink-0">
                 <div className="flex items-center justify-between">
                   <div className="flex items-center space-x-1.5">
                     {stepContent.map((s, i) => (
                       <button
                         key={i}
                         onClick={() => {
                           setStep(i + 1)
                           setIsPlaying(false)
                         }}
                         className={`h-1 rounded-full transition-all cursor-pointer ${
                           step === i + 1 ? 'w-4 bg-accent-solid' : 'w-1.5 bg-border-card hover:bg-muted-slate'
                         }`}
                       />
                     ))}
                   </div>
                   
                   <div className="flex items-center space-x-1.5">
                     <button onClick={() => { prevStep(); setIsPlaying(false); }} className="p-1 bg-bg-card hover:bg-bg-popover border border-border-card rounded-lg text-muted-slate hover:text-stark-white transition-colors cursor-pointer">
                       <ChevronLeft className="w-3.5 h-3.5" />
                     </button>
                     <button onClick={() => { nextStep(); setIsPlaying(false); }} className="p-1 bg-bg-card hover:bg-bg-popover border border-border-card rounded-lg text-muted-slate hover:text-stark-white transition-colors cursor-pointer">
                       <ChevronRight className="w-3.5 h-3.5" />
                     </button>
                   </div>
                 </div>

                 {step === 5 && (
                   <motion.div initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} className="pt-2">
                     <button 
                       onClick={() => { onClose(); navigate('/app/new'); }}
                       className="w-full inline-flex items-center justify-center space-x-2 px-4 py-2.5 bg-status-success hover:bg-emerald-600 text-white text-xs font-semibold rounded-lg transition-all shadow-md cursor-pointer"
                     >
                       <span>Start First Migration</span>
                       <ArrowRight className="w-3.5 h-3.5" />
                     </button>
                   </motion.div>
                 )}
               </div>
             </div>

          </motion.div>
        </div>
      </AnimatePresence>
    )
  }

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8 relative min-h-[calc(100vh-4rem)] flex flex-col justify-center">
      {/* Background ambient glows */}
      <div className="absolute top-[-10%] left-[20%] w-[500px] h-[500px] rounded-full bg-accent-solid/5 blur-[120px] -z-10 pointer-events-none"></div>
      <div className="absolute bottom-[-10%] right-[15%] w-[450px] h-[450px] rounded-full bg-status-info/5 blur-[100px] -z-10 pointer-events-none"></div>

      {/* Hero Header */}
      <div className="text-center max-w-2xl mx-auto space-y-4">
        <div className="inline-flex items-center space-x-1.5 py-1 px-3 rounded-full bg-accent-muted border border-accent-border/30 text-[10px] font-mono font-bold text-accent-solid tracking-wider uppercase">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Interactive Explainer</span>
        </div>
        <h1 className="text-h1 font-sans font-bold text-stark-white tracking-tight">
          How Fluxline Works
        </h1>
        <p className="text-base text-muted-slate leading-relaxed">
          Fluxline simplifies schema conversions and data replication using specialized LLM agents and validation pipelines. Follow the interactive steps below.
        </p>
      </div>

      {/* Explainer Stepper Console */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 bg-bg-panel/40 backdrop-blur-xl border border-border-card rounded-3xl p-6 sm:p-10 shadow-2xl relative overflow-hidden items-center">
        
        {/* Playback Control Absolute Bar */}
        <div className="absolute top-4 right-4 flex items-center space-x-2 z-20">
          <button 
            onClick={() => setIsPlaying(!isPlaying)}
            className="p-2 bg-bg-card hover:bg-bg-popover border border-border-card rounded-lg text-muted-slate hover:text-stark-white transition-all text-xs flex items-center gap-1.5 cursor-pointer font-mono font-bold"
          >
            {isPlaying ? (
              <>
                <Pause className="w-3.5 h-3.5 text-accent-solid" />
                <span>PAUSE</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 text-status-success animate-pulse" />
                <span>AUTOPLAY</span>
              </>
            )}
          </button>
        </div>

        {/* Left Side: Animated Diagram Display */}
        <div className="lg:col-span-7 bg-bg-canvas/60 border border-border-card/60 rounded-2xl h-80 flex items-center justify-center relative overflow-hidden shadow-inner">
          {/* Subtle grid mesh background */}
          <div className="absolute inset-0 bg-transparent opacity-10" style={{ 
            backgroundImage: `radial-gradient(rgba(255, 255, 255, 0.15) 1px, transparent 1px)`,
            backgroundSize: '20px 20px'
          }}></div>
          
          <AnimatePresence mode="wait">
            <motion.div 
              key={step}
              initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.35, ease: 'easeOut' }}
              className="w-full h-full flex items-center justify-center"
            >
              {renderDiagram()}
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Right Side: Step Text content & Controls */}
        <div className="lg:col-span-5 space-y-6 flex flex-col justify-between h-full min-h-[280px]">
          <div className="space-y-4">
            {/* Step Badge */}
            <div className="flex items-center space-x-2">
              <span className="w-6 h-6 rounded-lg bg-accent-solid flex items-center justify-center text-[11px] font-mono font-bold text-white shadow-md shadow-accent-glow/20">
                {stepContent[step - 1].num}
              </span>
              <span className="text-[10px] font-mono text-accent-solid font-bold uppercase tracking-wider">Step {step} of {totalSteps}</span>
            </div>

            {/* Headline and description */}
            <AnimatePresence mode="wait">
              <motion.div
                key={step}
                initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, x: 15 }}
                animate={{ opacity: 1, x: 0 }}
                exit={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, x: -15 }}
                transition={{ duration: 0.25, ease: 'easeInOut' }}
                className="space-y-3.5"
              >
                <h2 className="text-[24px] font-sans font-semibold text-stark-white tracking-tight">
                  {stepContent[step - 1].title}
                </h2>
                <p className="font-sans text-body text-muted-slate leading-relaxed">
                  {stepContent[step - 1].desc}
                </p>
              </motion.div>
            </AnimatePresence>
          </div>

          {/* Stepper Dots & CTAs */}
          <div className="space-y-6 pt-4 border-t border-border-card/60">
            {/* Nav dots */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-1.5">
                {stepContent.map((s, i) => (
                  <button
                    key={i}
                    onClick={() => {
                      setStep(i + 1)
                      setIsPlaying(false) // Pause on user click
                    }}
                    className={`h-1.5 rounded-full transition-all cursor-pointer ${
                      step === i + 1 ? 'w-6 bg-accent-solid shadow-[0_0_8px_rgba(139,92,246,0.4)]' : 'w-2 bg-border-card hover:bg-muted-slate'
                    }`}
                  />
                ))}
              </div>

              {/* Prev / Next buttons */}
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => {
                    prevStep()
                    setIsPlaying(false)
                  }}
                  className="p-1.5 bg-bg-card hover:bg-bg-popover border border-border-card rounded-lg text-muted-slate hover:text-stark-white transition-colors cursor-pointer"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button
                  onClick={() => {
                    nextStep()
                    setIsPlaying(false)
                  }}
                  className="p-1.5 bg-bg-card hover:bg-bg-popover border border-border-card rounded-lg text-muted-slate hover:text-stark-white transition-colors cursor-pointer"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Start Migration CTA at Step 5 */}
            <AnimatePresence>
              {step === 5 && (
                <motion.div
                  initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, y: 10 }}
                  className="pt-2"
                >
                  <Link 
                    to="/app/new"
                    className="w-full inline-flex items-center justify-center space-x-2 px-5 py-3 bg-status-success hover:bg-emerald-600 text-white text-xs font-semibold rounded-xl transition-all shadow-lg shadow-emerald-600/20"
                  >
                    <span>Start Your First Migration</span>
                    <ArrowRight className="w-4 h-4" />
                  </Link>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

        </div>
      </div>
    </div>
  )
}
