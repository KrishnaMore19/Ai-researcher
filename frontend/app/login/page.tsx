// app/login/page.tsx
"use client"
import { Mail, Lock } from "lucide-react"
import type React from "react"
import Link from "next/link"
import { useState, useEffect, useRef } from "react"
import { useSearchParams } from "next/navigation"
import { Button } from "@/components/button"
import { Input } from "@/components/input"
import { ThemeToggle } from "@/components/theme-toggle"
import { useToast } from "@/components/toast-provider"
import { useAuthStore } from "@/store"
import { Spinner } from "@/components/ui/spinner"

export default function LoginPage() {
  const searchParams = useSearchParams()
  const { showToast } = useToast()
  
  // Zustand store
  const { login, logout, isAuthenticated, loading, error, clearError } = useAuthStore()
  
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [isRedirecting, setIsRedirecting] = useState(false)
  const redirectAttempts = useRef(0)

  // Check for redirect loop and clear auth if detected
  useEffect(() => {
    if (searchParams.get('redirect') === '/dashboard') {
      redirectAttempts.current += 1
      
      // If we've tried to redirect more than 3 times, clear auth
      if (redirectAttempts.current > 3) {
        console.log('Redirect loop detected, clearing auth...')
        logout()
        redirectAttempts.current = 0
      }
    }
  }, [searchParams, logout])

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    clearError()
    
    if (!email || !password) {
      showToast("Please enter email and password", "error")
      return
    }

    try {
      console.log('Attempting login...')
      await login(email, password)
      console.log('Login successful!')
      showToast("Welcome back!", "success")
      
      // Show redirecting loader
      setIsRedirecting(true)
      
      // Redirect after successful login
      const redirect = searchParams.get('redirect') || '/dashboard'
      console.log('Redirecting to:', redirect)
      
      // Small delay to ensure state is saved
      setTimeout(() => {
        window.location.href = redirect
      }, 500)
    } catch (err: any) {
      console.error('Login error:', err)
      setIsRedirecting(false)
      showToast(err.message || "Login failed", "error")
    }
  }

  return (
    <>
      {/* Full Screen Loader During Redirect */}
      {isRedirecting && (
        <div className="fixed inset-0 bg-background/95 backdrop-blur-sm flex flex-col items-center justify-center z-50 gap-3">
          <Spinner className="size-10" />
          <p className="text-sm text-muted-foreground animate-pulse">Redirecting to dashboard...</p>
        </div>
      )}

      <div className="relative grid min-h-dvh place-items-center overflow-hidden">
        <div className="pointer-events-none absolute inset-0 -z-10">
          <div className="animate-[spin_25s_linear_infinite] absolute -top-40 -left-40 h-96 w-96 rounded-full bg-secondary/30 blur-3xl" />
          <div className="animate-[spin_30s_linear_infinite_reverse] absolute -bottom-40 -right-40 h-96 w-96 rounded-full bg-primary/30 blur-3xl" />
        </div>

        <div className="absolute right-4 top-4">
          <ThemeToggle />
        </div>

        <div className="w-full max-w-md rounded-2xl glass p-6">
          <div className="mb-6 flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-primary" />
            <div>
              <h1 className="text-xl font-semibold">AI Research</h1>
              <p className="text-sm text-muted-foreground">Sign in to continue</p>
            </div>
          </div>

          <form onSubmit={onSubmit} className="space-y-4">
            <Input
              label="Email"
              icon={<Mail size={16} />}
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.currentTarget.value)}
              error={error && !email ? "Email is required" : undefined}
              disabled={isRedirecting}
            />
            <Input
              label="Password"
              icon={<Lock size={16} />}
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.currentTarget.value)}
              error={error && !password ? "Password is required" : undefined}
              disabled={isRedirecting}
            />
            
            {error && (
              <p className="text-sm text-red-500">{error}</p>
            )}
            
            <Button 
              type="submit" 
              loading={loading || isRedirecting} 
              className="w-full" 
              disabled={loading || isRedirecting}
            >
              {isRedirecting ? 'Redirecting...' : loading ? 'Logging in...' : 'Login'}
            </Button>
          </form>

          <p className="mt-4 text-center text-sm text-muted-foreground">
            {"Don't have an account? "}
            <Link href="/register" className="text-primary hover:underline">
              Sign up
            </Link>
          </p>
        </div>
      </div>
    </>
  )
}