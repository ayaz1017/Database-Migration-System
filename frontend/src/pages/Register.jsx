import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { Eye, EyeOff, Loader2, ArrowRight } from 'lucide-react'
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
      <div className="bg-[#121216] border border-zinc-800 rounded-xl p-7 sm:p-8 shadow-xl w-full">
        
        <div className="mb-5">
          <h2 className="font-sans text-xl font-bold text-white mb-1 tracking-tight">Create your account</h2>
          <p className="text-xs text-zinc-400">Start deterministic migrations with zero downtime</p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-3.5">
          
          <div className="grid grid-cols-2 gap-3">
            {/* First Name */}
            <div>
              <label className="block font-sans text-xs font-medium text-zinc-400 mb-1">First name</label>
              <input 
                type="text" 
                {...register('firstName', { required: 'First name is required' })}
                className={`w-full bg-zinc-950 border ${errors.firstName ? 'border-red-500/50' : 'border-zinc-800 focus:border-indigo-500'} rounded-lg px-3 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none transition-colors`}
                placeholder="Jane"
              />
              {errors.firstName && <p className="mt-1 text-[11px] text-red-400">{errors.firstName.message}</p>}
            </div>
            {/* Last Name */}
            <div>
              <label className="block font-sans text-xs font-medium text-zinc-400 mb-1">Last name</label>
              <input 
                type="text" 
                {...register('lastName', { required: 'Last name is required' })}
                className={`w-full bg-zinc-950 border ${errors.lastName ? 'border-red-500/50' : 'border-zinc-800 focus:border-indigo-500'} rounded-lg px-3 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none transition-colors`}
                placeholder="Doe"
              />
              {errors.lastName && <p className="mt-1 text-[11px] text-red-400">{errors.lastName.message}</p>}
            </div>
          </div>

          {/* Email */}
          <div>
            <label className="block font-sans text-xs font-medium text-zinc-400 mb-1">Work email</label>
            <input 
              type="email" 
              {...register('email', { required: 'Email is required' })}
              className={`w-full bg-zinc-950 border ${errors.email ? 'border-red-500/50 focus:border-red-500' : 'border-zinc-800 focus:border-indigo-500'} rounded-lg px-3 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none transition-colors`}
              placeholder="jane@company.com"
            />
            {errors.email && <p className="mt-1 text-[11px] text-red-400">{errors.email.message}</p>}
          </div>

          {/* Password */}
          <div>
            <label className="block font-sans text-xs font-medium text-zinc-400 mb-1">Password</label>
            <div className="relative">
              <input 
                type={showPassword ? 'text' : 'password'}
                {...register('password', { 
                  required: 'Password is required',
                  minLength: { value: 6, message: 'Must be at least 6 characters' }
                })}
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
            {errors.password && <p className="mt-1 text-[11px] text-red-400">{errors.password.message}</p>}
          </div>

          {/* Submit */}
          <button 
            type="submit" 
            disabled={isLoading}
            className="w-full flex items-center justify-center space-x-2 bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white font-sans text-xs font-semibold py-2.5 px-4 rounded-lg transition-all shadow-sm disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer pt-2"
          >
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : (
              <>
                <span>Create Workspace</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </>
            )}
          </button>
          
          <p className="text-[11px] text-zinc-500 text-center mt-1.5 leading-relaxed">
            By signing up, you agree to our <a href="#" className="text-zinc-400 hover:text-white underline">Terms</a> and <a href="#" className="text-zinc-400 hover:text-white underline">Privacy Policy</a>.
          </p>
        </form>

        <div className="relative my-5">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-zinc-800"></div>
          </div>
          <div className="relative flex justify-center text-[10px] uppercase">
            <span className="bg-[#121216] px-2 text-zinc-500 font-medium tracking-wider">Or register with</span>
          </div>
        </div>

        <SocialButtons mode="Sign Up" />

        <p className="mt-5 text-center text-xs text-zinc-400">
          Already have an account?{' '}
          <Link to="/login" className="font-semibold text-indigo-400 hover:text-indigo-300 transition-colors">
            Sign In
          </Link>
        </p>

      </div>
    </AuthLayout>
  )
}
