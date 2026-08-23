import React from 'react'
import { ShieldAlert, RefreshCw, ArrowLeft } from 'lucide-react'

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null, errorInfo: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo })
    console.error('Fluxline Application Fault caught by boundary:', error, errorInfo)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null })
    window.location.href = '/app'
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-[#060608] text-[#FAFAFA] flex items-center justify-center p-6 font-sans">
          {/* Ambient Glow */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-red-500/5 rounded-full blur-[100px] pointer-events-none"></div>

          <div className="max-w-xl w-full bg-[#0D0D12] border border-[#F43F5E]/30 rounded-3xl p-8 md:p-10 shadow-2xl relative z-10 space-y-6 text-center animate-in fade-in duration-300">
            <div className="w-16 h-16 rounded-full bg-[#F43F5E]/10 border border-[#F43F5E]/30 flex items-center justify-center mx-auto text-[#F43F5E] shadow-[0_0_30px_rgba(244,63,94,0.15)]">
              <ShieldAlert className="w-8 h-8" />
            </div>
            
            <div className="space-y-2">
              <h1 className="font-sans text-h3 font-bold tracking-tight text-[#FAFAFA]">Application Runtime Fault</h1>
              <p className="font-sans text-body-sm text-[#8F8F9E] max-w-sm mx-auto leading-relaxed">
                An unexpected component rendering loop or state crash occurred. The compiler lock prevents cascade damage.
              </p>
            </div>

            {this.state.error && (
              <div className="bg-[#13131A] border border-white/5 p-4 rounded-2xl text-left max-h-48 overflow-y-auto scrollbar-thin shadow-inner">
                <span className="text-[10px] font-mono text-[#F43F5E] font-bold block mb-1 uppercase tracking-wider">Exception Trace</span>
                <p className="font-mono text-caption text-[#8F8F9E] break-all leading-normal">
                  {this.state.error.toString()}
                </p>
              </div>
            )}

            <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-3">
              <button
                onClick={this.handleReset}
                className="w-full sm:w-auto px-6 py-3 bg-[#F43F5E] hover:bg-[#E11D48] text-white text-xs font-bold rounded-xl transition-all shadow-[0_0_20px_rgba(244,63,94,0.25)] flex items-center justify-center space-x-2 cursor-pointer"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Recover & Restart Workspace</span>
              </button>
              <a
                href="/"
                className="w-full sm:w-auto px-6 py-3 bg-[#13131A] hover:bg-[#1C1C24] border border-white/5 rounded-xl text-xs font-bold text-[#FAFAFA] transition-all flex items-center justify-center space-x-2"
              >
                <ArrowLeft className="w-4 h-4 text-[#8F8F9E]" />
                <span>Return Home</span>
              </a>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
