import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { Loader2, ArrowRight, ArrowLeft, KeyRound } from 'lucide-react'
import toast from 'react-hot-toast'
import AuthLayout from '../components/Auth/AuthLayout'

export default function ForgotPassword() {
  const [isLoading, setIsLoading] = useState(false)
  const [isSubmitted, setIsSubmitted] = useState(false)
  const { register, handleSubmit, formState: { errors } } = useForm()

  const onSubmit = async () => {
    setIsLoading(true)
    try {
      await new Promise((resolve) => setTimeout(resolve, 600))
      setIsSubmitted(true)
      toast.success('Password reset instructions sent!')
    } catch {
      toast.error('Failed to send reset link')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <AuthLayout>
      <div className="bg-[#121216] border border-zinc-800 rounded-xl p-7 sm:p-8 shadow-xl w-full">
        
        <div className="mb-5">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mb-3 text-indigo-400">
            <KeyRound className="w-4 h-4" />
          </div>
          <h2 className="font-sans text-xl font-bold text-white mb-1 tracking-tight">Reset password</h2>
          <p className="text-xs text-zinc-400">
            {isSubmitted 
              ? "We've sent password reset instructions to your email." 
              : "Enter your registered email address to receive recovery instructions."}
          </p>
        </div>

        {!isSubmitted ? (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-3.5">
            <div>
              <label className="block font-sans text-xs font-medium text-zinc-400 mb-1">Email address</label>
              <input 
                type="email" 
                {...register('email', { required: 'Email is required' })}
                className={`w-full bg-zinc-950 border ${errors.email ? 'border-red-500/50 focus:border-red-500' : 'border-zinc-800 focus:border-indigo-500'} rounded-lg px-3 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none transition-colors`}
                placeholder="name@company.com"
              />
              {errors.email && <p className="mt-1 text-[11px] text-red-400">{errors.email.message}</p>}
            </div>

            <button 
              type="submit" 
              disabled={isLoading}
              className="w-full flex items-center justify-center space-x-2 bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white font-sans text-xs font-semibold py-2.5 px-4 rounded-lg transition-all shadow-sm disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer pt-2"
            >
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : (
                <>
                  <span>Send Reset Link</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </form>
        ) : (
          <div className="p-3.5 bg-zinc-900 border border-zinc-800 rounded-lg text-center space-y-2">
            <p className="text-xs text-zinc-300">
              For local demo instances, you can sign in directly with: <br/>
              <strong className="font-mono text-indigo-400">admin@example.com / admin</strong>
            </p>
          </div>
        )}

        <div className="mt-5 text-center">
          <Link to="/login" className="inline-flex items-center space-x-1.5 text-xs text-zinc-400 hover:text-white transition-colors">
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Sign In</span>
          </Link>
        </div>

      </div>
    </AuthLayout>
  )
}
