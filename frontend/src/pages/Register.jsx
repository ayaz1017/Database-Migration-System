import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { Eye, EyeOff, Loader2, Database, Mail } from 'lucide-react'
import toast from 'react-hot-toast'
import AuthLayout from '../components/Auth/AuthLayout'
import SocialButtons from '../components/Auth/SocialButtons'
import { useAuth } from '../context/AuthContext'

export default function Register() {
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const navigate = useNavigate()
  const { register: registerUser } = useAuth()

  const { register, handleSubmit, formState: { errors } } = useForm()

  const onSubmit = async (data) => {
    setIsLoading(true)
    try {
      await registerUser(data.email, data.password)
      toast.success('Account created successfully! Welcome to Fluxline.')
      navigate('/app')
    } catch (err) {
      toast.error(err.message || 'Registration failed. That email may already be in use.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <AuthLayout>
      <div className="w-full">
        
        {/* Brand Header */}
        <div className="flex flex-col items-center text-center mb-6">
          <div className="flex items-center space-x-2 mb-1.5">
            <div className="w-8 h-8 rounded-xl bg-[#242d76] text-white flex items-center justify-center shadow-md shadow-[#242d76]/20">
              <Database className="w-4 h-4" />
            </div>
            <span className="text-2xl font-extrabold text-[#242d76] tracking-tight">Fluxline</span>
          </div>
          <p className="text-xs text-slate-500">
            Start high-performance database migrations with zero downtime
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-3.5">
          
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                First name <span className="text-red-500">*</span>
              </label>
              <input 
                type="text" 
                {...register('firstName', { required: 'Required' })}
                className={`w-full bg-white border ${errors.firstName ? 'border-red-400 focus:border-red-500' : 'border-slate-300 hover:border-slate-400 focus:border-[#242d76] focus:ring-2 focus:ring-[#242d76]/15'} rounded-lg px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 transition-all outline-none shadow-xs`}
                placeholder="Jane"
              />
              {errors.firstName && <p className="mt-1 text-[11px] text-red-500">{errors.firstName.message}</p>}
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Last name <span className="text-red-500">*</span>
              </label>
              <input 
                type="text" 
                {...register('lastName', { required: 'Required' })}
                className={`w-full bg-white border ${errors.lastName ? 'border-red-400 focus:border-red-500' : 'border-slate-300 hover:border-slate-400 focus:border-[#242d76] focus:ring-2 focus:ring-[#242d76]/15'} rounded-lg px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 transition-all outline-none shadow-xs`}
                placeholder="Doe"
              />
              {errors.lastName && <p className="mt-1 text-[11px] text-red-500">{errors.lastName.message}</p>}
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Work email <span className="text-red-500">*</span>
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <Mail className="w-4 h-4" />
              </div>
              <input 
                type="email" 
                autoComplete="email"
                {...register('email', { required: 'Work email is required' })}
                className={`w-full bg-white border ${errors.email ? 'border-red-400 focus:border-red-500' : 'border-slate-300 hover:border-slate-400 focus:border-[#242d76] focus:ring-2 focus:ring-[#242d76]/15'} rounded-lg pl-9 pr-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 transition-all outline-none shadow-xs`}
                placeholder="jane@company.com"
              />
            </div>
            {errors.email && <p className="mt-1 text-xs text-red-500">{errors.email.message}</p>}
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Password <span className="text-red-500">*</span>
            </label>
            <div className="relative">
              <input 
                type={showPassword ? 'text' : 'password'}
                autoComplete="new-password"
                {...register('password', { 
                  required: 'Password is required',
                  minLength: { value: 6, message: 'Must be at least 6 characters' }
                })}
                className={`w-full bg-white border ${errors.password ? 'border-red-400 focus:border-red-500' : 'border-slate-300 hover:border-slate-400 focus:border-[#242d76] focus:ring-2 focus:ring-[#242d76]/15'} rounded-lg pl-3 pr-10 py-2 text-sm text-slate-900 placeholder:text-slate-400 transition-all outline-none shadow-xs`}
                placeholder="••••••••"
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

          <button 
            type="submit" 
            disabled={isLoading}
            className="w-full py-2.5 px-6 rounded-full bg-[#242d76] hover:bg-[#1a225e] active:bg-[#141b4c] text-white font-medium text-sm transition-all shadow-md shadow-[#242d76]/20 flex items-center justify-center cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed mt-2"
          >
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <span>Create account</span>}
          </button>

        </form>

        {/* Divider */}
        <div className="flex items-center my-4">
          <div className="flex-1 border-t border-slate-200"></div>
          <span className="px-3 text-[10px] text-slate-400 font-medium tracking-wider uppercase">or</span>
          <div className="flex-1 border-t border-slate-200"></div>
        </div>

        <SocialButtons mode="Sign Up" />

        <p className="mt-5 text-center text-xs text-slate-600">
          Already have an account?{' '}
          <Link to="/login" className="font-semibold text-[#4e5ac8] hover:text-[#242d76] hover:underline transition-colors">
            Log in
          </Link>
        </p>

        <p className="mt-5 text-center text-[11px] text-slate-400 leading-relaxed max-w-xs mx-auto">
          By registering, you agree to our{' '}
          <a href="#terms" className="underline hover:text-slate-600">Terms of Service</a> and{' '}
          <a href="#privacy" className="underline hover:text-slate-600">Privacy Policy</a>
        </p>

      </div>
    </AuthLayout>
  )
}
