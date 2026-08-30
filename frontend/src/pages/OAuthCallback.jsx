import React, { useEffect, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuth } from '../context/AuthContext'

export default function OAuthCallback() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { fetchUser } = useAuth()
  const processedRef = useRef(false)

  useEffect(() => {
    if (processedRef.current) return
    processedRef.current = true

    const accessToken = searchParams.get('access_token')
    const refreshToken = searchParams.get('refresh_token')
    const rawRedirect = searchParams.get('redirect') || '/app'
    const error = searchParams.get('error')

    // Prevent open redirects: target must start with '/' and not '//'
    const redirectTarget =
      rawRedirect.startsWith('/') && !rawRedirect.startsWith('//')
        ? rawRedirect
        : '/app'

    if (error) {
      toast.error(decodeURIComponent(error), { duration: 5000 })
      navigate('/login', { replace: true })
      return
    }

    if (!accessToken || !refreshToken) {
      toast.error('Authentication response was incomplete. Please try again.')
      navigate('/login', { replace: true })
      return
    }

    const completeAuth = async () => {
      try {
        localStorage.setItem('access_token', accessToken)
        localStorage.setItem('refresh_token', refreshToken)
        if (fetchUser) {
          await fetchUser()
        }
        toast.success('Successfully authenticated!')
        navigate(redirectTarget, { replace: true })
      } catch (err) {
        console.error('Failed to complete OAuth setup:', err)
        toast.error('Session initialization failed. Please log in again.')
        navigate('/login', { replace: true })
      }
    }

    completeAuth()
  }, [searchParams, navigate, fetchUser])

  return (
    <div className="min-h-screen bg-[#0B0B0E] flex flex-col items-center justify-center p-4">
      <div className="bg-[#121216] border border-zinc-800 rounded-xl p-8 shadow-2xl flex flex-col items-center text-center max-w-sm w-full">
        <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mb-4">
          <Loader2 className="w-6 h-6 animate-spin" />
        </div>
        <h2 className="text-sm font-semibold text-white mb-1">Completing Sign-In</h2>
        <p className="text-xs text-zinc-400">Verifying credentials and preparing your workspace...</p>
      </div>
    </div>
  )
}
