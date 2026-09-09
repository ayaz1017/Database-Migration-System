import { useState, useEffect } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { Eye, EyeOff, Loader2, KeyRound, Database, Mail } from 'lucide-react'
import toast from 'react-hot-toast'
import AuthLayout from '../components/Auth/AuthLayout'
import SocialButtons from '../components/Auth/SocialButtons'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [isDemoLoading, setIsDemoLoading] = useState(false)
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()

  useEffect(() => {
    const error = searchParams.get('error')
    if (error) {
      toast.error(decodeURIComponent(error), { duration: 6000 })
      searchParams.delete('error')
      setSearchParams(searchParams, { replace: true })
    }
  }, [searchParams, setSearchParams])

  const { login } = useAuth()
  const { register, handleSubmit, setValue, formState: { errors } } = useForm()

  const onSubmit = async (data) => {
    setIsLoading(true)
    try {
      await login(data.email, data.password)
      toast.success('Signed in successfully')
      navigate('/app')
    } catch (err) {
      toast.error(err.message || 'Invalid email or password')
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
      toast.success('Signed in with demo admin credentials')
      navigate('/app')
    } catch (err) {
      toast.error(err.message || 'Demo login failed')
    } finally {
      setIsDemoLoading(false)
    }
  }

  return (
    <AuthLayout>
      <div className="w-full">
        
        {/* Brand Header (matches reference: logo + tagline) */}
        <div className="flex flex-col items-center text-center mb-6 sm:mb-7">
          <div className="flex items-center space-x-2.5 mb-1.5">
            <div className="w-9 h-9 rounded-xl bg-[#242d76] text-white flex items-center justify-center shadow-md shadow-[#242d76]/20">
              <Database className="w-5 h-5" />
            </div>
            <span className="text-3xl font-extrabold text-[#242d76] tracking-tight">Fluxline</span>
          </div>
          <p className="text-xs sm:text-sm font-medium text-[#242d76]/75">
            The heart of your database migration
          </p>
        </div>

        {/* Primary Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          
          {/* Email field with Mail icon */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Email <span className="text-red-500">*</span>
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
                placeholder="Enter your email"
              />
            </div>
            {errors.email && <p className="mt-1 text-xs text-red-500">{errors.email.message}</p>}
          </div>

          {/* Password field with Eye toggle */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Password <span className="text-red-500">*</span>
            </label>
            <div className="relative">
              <input 
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                {...register('password', { required: 'Password is required' })}
                className={`w-full bg-white border ${errors.password ? 'border-red-400 focus:border-red-500' : 'border-slate-300 hover:border-slate-400 focus:border-[#242d76] focus:ring-2 focus:ring-[#242d76]/15'} rounded-lg pl-3.5 pr-10 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 transition-all outline-none shadow-xs`}
                placeholder="Enter password"
              />
              <button 
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600 transition-colors cursor-pointer"
                title={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            {errors.password && <p className="mt-1 text-xs text-red-500">{errors.password.message}</p>}
          </div>

          {/* Options row: Remember me + Forgot password */}
          <div className="flex items-center justify-between pt-1">
            <label className="flex items-center space-x-2 cursor-pointer select-none">
              <input 
                type="checkbox" 
                className="w-4 h-4 rounded border-slate-300 accent-[#242d76] cursor-pointer" 
              />
              <span className="text-xs text-slate-600 font-normal">Remember me</span>
            </label>
            
            <Link 
              to="/forgot-password" 
              className="text-xs font-semibold text-[#4e5ac8] hover:text-[#242d76] hover:underline transition-colors"
            >
              Forgot password?
            </Link>
          </div>

          {/* Log in Pill Button */}
          <button 
            type="submit" 
            disabled={isLoading || isDemoLoading}
            className="w-full py-2.5 px-6 rounded-full bg-[#242d76] hover:bg-[#1a225e] active:bg-[#141b4c] text-white font-medium text-sm transition-all shadow-md shadow-[#242d76]/20 flex items-center justify-center cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed mt-3"
          >
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <span>Log in</span>}
          </button>

        </form>

        {/* Sign up prompt */}
        <p className="mt-4 text-center text-xs text-slate-600">
          Don't have an account?{' '}
          <Link to="/register" className="font-semibold text-[#4e5ac8] hover:text-[#242d76] hover:underline transition-colors">
            Sign up.
          </Link>
        </p>

        {/* Divider */}
        <div className="flex items-center my-4">
          <div className="flex-1 border-t border-slate-200"></div>
          <span className="px-3 text-[10px] text-slate-400 font-medium tracking-wider uppercase">or continue with</span>
          <div className="flex-1 border-t border-slate-200"></div>
        </div>

        {/* Social Buttons */}
        <SocialButtons mode="Sign In" />

        {/* Discreet Local Evaluator Helper */}
        <div className="mt-4 p-2.5 rounded-xl bg-slate-50 border border-slate-200/80 flex flex-col sm:flex-row sm:items-center justify-between gap-1 text-xs">
          <div className="flex items-center space-x-2 text-slate-600">
            <KeyRound className="w-3.5 h-3.5 text-slate-400 shrink-0" />
            <span>Evaluating locally?</span>
          </div>
          <button
            type="button"
            onClick={handleDemoLogin}
            disabled={isDemoLoading || isLoading}
            className="text-xs text-[#4e5ac8] hover:text-[#242d76] font-semibold transition-colors cursor-pointer disabled:opacity-50 text-left sm:text-right"
          >
            {isDemoLoading ? 'Filling...' : 'Auto-fill demo credentials'}
          </button>
        </div>

        {/* Legal Disclaimer (matching reference: By creating an account or logging in...) */}
        <p className="mt-5 text-center text-[11px] text-slate-400 leading-relaxed max-w-xs mx-auto">
          By creating an account or logging in, you agree to the current{' '}
          <a href="#terms" className="underline hover:text-slate-600">Terms of Service</a> and{' '}
          <a href="#privacy" className="underline hover:text-slate-600">Privacy Policy</a>
        </p>

      </div>
    </AuthLayout>
  )
}
