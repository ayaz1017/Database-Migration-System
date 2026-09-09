import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { Loader2, ArrowLeft, KeyRound, Mail, Database } from 'lucide-react'
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
      <div className="w-full">
        
        {/* Brand Header */}
        <div className="flex flex-col items-center text-center mb-6">
          <div className="w-9 h-9 rounded-xl bg-[#242d76] text-white flex items-center justify-center shadow-md shadow-[#242d76]/20 mb-2">
            <KeyRound className="w-5 h-5" />
          </div>
          <h1 className="text-2xl font-extrabold text-[#242d76] tracking-tight">Reset password</h1>
          <p className="text-xs text-slate-500 mt-1 max-w-xs">
            {isSubmitted 
              ? "We've sent password reset instructions to your email." 
              : "Enter your registered email address to receive recovery instructions."}
          </p>
        </div>

        {!isSubmitted ? (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Email address <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                  <Mail className="w-4 h-4" />
                </div>
                <input 
                  type="email" 
                  autoComplete="email"
                  {...register('email', { required: 'Email is required' })}
                  className={`w-full bg-white border ${errors.email ? 'border-red-400 focus:border-red-500' : 'border-slate-300 hover:border-slate-400 focus:border-[#242d76] focus:ring-2 focus:ring-[#242d76]/15'} rounded-lg pl-10 pr-3.5 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 transition-all outline-none shadow-xs`}
                  placeholder="name@company.com"
                />
              </div>
              {errors.email && <p className="mt-1 text-xs text-red-500">{errors.email.message}</p>}
            </div>

            <button 
              type="submit" 
              disabled={isLoading}
              className="w-full py-2.5 px-6 rounded-full bg-[#242d76] hover:bg-[#1a225e] active:bg-[#141b4c] text-white font-medium text-sm transition-all shadow-md shadow-[#242d76]/20 flex items-center justify-center cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed mt-2"
            >
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <span>Send Reset Link</span>}
            </button>
          </form>
        ) : (
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-center space-y-2">
            <p className="text-xs text-slate-600">
              For local demo instances, you can sign in directly with: <br/>
              <strong className="font-mono text-[#242d76]">admin@example.com / admin</strong>
            </p>
          </div>
        )}

        <div className="mt-6 text-center">
          <Link to="/login" className="inline-flex items-center space-x-1.5 text-xs text-slate-500 hover:text-[#242d76] font-medium transition-colors">
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Log in</span>
          </Link>
        </div>

      </div>
    </AuthLayout>
  )
}
