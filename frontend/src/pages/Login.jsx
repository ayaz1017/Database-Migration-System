import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { Eye, EyeOff, Loader2, ArrowRight, KeyRound } from 'lucide-react'
import toast from 'react-hot-toast'
import AuthLayout from '../components/Auth/AuthLayout'
import SocialButtons from '../components/Auth/SocialButtons'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [isDemoLoading, setIsDemoLoading] = useState(false)
  const navigate = useNavigate()

  const { login } = useAuth()
  const { register, handleSubmit, setValue, formState: { errors } } = useForm()

  const onSubmit = async (data) => {
    setIsLoading(true)
    try {
      await login(data.email, data.password)
      toast.success('Successfully logged in')
      navigate('/app')
    } catch (err) {
      toast.error(err.message || 'Login failed: Invalid email or password')
    } finally {
      setIsLoading(false)
    }
  }

  const handleDemoLogin = async () => {
    setIsDemoLoading(true)
    setValue('email', 'admin@example.com')
    setValue('password', 'admin')
    try {
      await login('admin@example.com', 'admin')
      toast.success('Logged in with Demo Admin credentials')
      navigate('/app')
    } catch (err) {
      toast.error(err.message || 'Demo login failed')
    } finally {
      setIsDemoLoading(false)
    }
  }

  return (
    <AuthLayout>
      <div className="bg-[#121216] border border-zinc-800 rounded-xl p-7 sm:p-8 shadow-xl w-full">
        
        <div className="mb-5">
          <h2 className="font-sans text-xl font-bold text-white mb-1 tracking-tight">Sign in to Fluxline</h2>
          <p className="text-xs text-zinc-400">Access your workspace and live migration pipelines</p>
        </div>

        {/* Demo Login Quick Action */}
        <div className="mb-5 p-3 bg-zinc-900/80 border border-zinc-800 rounded-lg flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-6 h-6 rounded-md bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
              <KeyRound className="w-3.5 h-3.5" />
            </div>
            <div>
              <p className="text-xs font-semibold text-zinc-200">1-Click Demo Login</p>
              <p className="text-[11px] font-mono text-zinc-400">admin@example.com / admin</p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleDemoLogin}
            disabled={isDemoLoading || isLoading}
            className="px-2.5 py-1 bg-zinc-800 hover:bg-zinc-700 active:bg-zinc-750 text-zinc-200 text-xs font-medium rounded-md border border-zinc-700 transition-all flex items-center space-x-1 disabled:opacity-50 cursor-pointer"
          >
            {isDemoLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : <span>Auto Fill</span>}
          </button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-3.5">
          
          {/* Email */}
          <div>
            <label className="block font-sans text-xs font-medium text-zinc-400 mb-1">Email address</label>
            <input 
              type="email" 
              {...register('email', { required: 'Email is required' })}
              className={`w-full bg-zinc-950 border ${errors.email ? 'border-red-500/50 focus:border-red-500' : 'border-zinc-800 focus:border-indigo-500'} rounded-lg px-3 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none transition-colors`}
              placeholder="name@company.com"
            />
            {errors.email && <p className="mt-1 text-xs text-red-400">{errors.email.message}</p>}
          </div>

          {/* Password */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block font-sans text-xs font-medium text-zinc-400">Password</label>
              <Link to="/forgot-password" className="text-xs font-medium text-indigo-400 hover:text-indigo-300 transition-colors">
                Forgot password?
              </Link>
            </div>
            <div className="relative">
              <input 
                type={showPassword ? 'text' : 'password'}
                {...register('password', { required: 'Password is required' })}
                className={`w-full bg-zinc-950 border ${errors.password ? 'border-red-500/50 focus:border-red-500' : 'border-zinc-800 focus:border-indigo-500'} rounded-lg pl-3 pr-10 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none transition-colors`}
                placeholder="••••••••"
              />
              <button 
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 p-1 text-zinc-500 hover:text-zinc-300 transition-colors cursor-pointer"
              >
                {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
              </button>
            </div>
            {errors.password && <p className="mt-1 text-xs text-red-400">{errors.password.message}</p>}
          </div>

          {/* Submit */}
          <button 
            type="submit" 
            disabled={isLoading || isDemoLoading}
            className="w-full flex items-center justify-center space-x-2 bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white font-sans text-xs font-semibold py-2.5 px-4 rounded-lg transition-all shadow-sm disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer pt-2"
          >
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : (
              <>
                <span>Sign In to Console</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </>
            )}
          </button>

        </form>

        <div className="relative my-5">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-zinc-800"></div>
          </div>
          <div className="relative flex justify-center text-[10px] uppercase">
            <span className="bg-[#121216] px-2 text-zinc-500 font-medium tracking-wider">Or continue with</span>
          </div>
        </div>

        <SocialButtons mode="Sign In" />

        <p className="mt-5 text-center text-xs text-zinc-400">
          Don't have an account?{' '}
          <Link to="/register" className="font-semibold text-indigo-400 hover:text-indigo-300 transition-colors">
            Create account
          </Link>
        </p>

      </div>
    </AuthLayout>
  )
}
