// app/register/page.tsx
"use client"
import { Mail, Lock, User, ShieldCheck } from "lucide-react"
import type React from "react"
import Link from "next/link"
import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/button"
import { Input } from "@/components/input"
import { ThemeToggle } from "@/components/theme-toggle"
import { useToast } from "@/components/toast-provider"
import { ProgressBar } from "@/components/progress-bar"
import { useAuthStore } from "@/store"
import { Spinner } from "@/components/ui/spinner"

function strength(pw: string) {
  let s = 0
  if (pw.length >= 8) s++
  if (/[A-Z]/.test(pw)) s++
  if (/[a-z]/.test(pw)) s++
  if (/\d/.test(pw)) s++
  if (/[^A-Za-z0-9]/.test(pw)) s++
  return Math.min(4, s)
}

export default function RegisterPage() {
  const router = useRouter()
  const { showToast } = useToast()
  
  // Zustand store
  const { register, isAuthenticated, loading, error, clearError } = useAuthStore()
  
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirm, setConfirm] = useState("")
  const [agree, setAgree] = useState(false)
  const [isRedirecting, setIsRedirecting] = useState(false)

  // Redirect if already logged in
  useEffect(() => {
    if (isAuthenticated) {
      console.log('Already authenticated, redirecting to dashboard')
      setIsRedirecting(true)
      window.location.href = '/dashboard'
    }
  }, [isAuthenticated])

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    clearError()
    
    if (!name || !email || !password || !confirm) {
      showToast("Please fill all fields", "error")
      return
    }
    if (password !== confirm) {
      showToast("Passwords do not match", "error")
      return
    }
    if (!agree) {
      showToast("Please agree to the Terms & Conditions", "error")
      return
    }
    
    const s = strength(password)
    if (s < 2) {
      showToast("Password is too weak", "error")
      return
    }

    try {
      console.log('Attempting registration...')
      await register(name, email, password)
      console.log('Registration successful!')
      showToast("Account created successfully!", "success")
      
      // Show redirecting loader
      setIsRedirecting(true)
      
      // Force redirect after successful registration
      console.log('Redirecting to dashboard...')
      setTimeout(() => {
        window.location.href = '/dashboard'
      }, 500)
    } catch (err: any) {
      console.error('Registration error:', err)
      setIsRedirecting(false)
      showToast(err.message || "Registration failed", "error")
    }
  }

  const s = strength(password)
  const pct = (s / 4) * 100

  return (
    <>
      {/* Full Screen Loader During Redirect */}
      {isRedirecting && (
        <div className="fixed inset-0 bg-background/95 backdrop-blur-sm flex flex-col items-center justify-center z-50 gap-3">
          <Spinner className="size-10" />
          <p className="text-sm text-muted-foreground animate-pulse">Setting up your account...</p>
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
              <h1 className="text-xl font-semibold">Create your account</h1>
              <p className="text-sm text-muted-foreground">Join AI Research</p>
            </div>
          </div>

          <form onSubmit={onSubmit} className="space-y-4">
            <Input
              label="Full Name"
              icon={<User size={16} />}
              value={name}
              onChange={(e) => setName(e.currentTarget.value)}
              disabled={isRedirecting}
            />
            <Input
              label="Email"
              icon={<Mail size={16} />}
              type="email"
              value={email}
              onChange={(e) => setEmail(e.currentTarget.value)}
              disabled={isRedirecting}
            />
            <Input
              label="Password"
              icon={<Lock size={16} />}
              type="password"
              value={password}
              onChange={(e) => setPassword(e.currentTarget.value)}
              disabled={isRedirecting}
            />
            <div className="space-y-2">
              <ProgressBar value={pct} max={100} color={pct < 50 ? "red" : pct < 75 ? "yellow" : "green"} />
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <ShieldCheck size={14} />
                <span>Password strength: {pct < 50 ? "Weak" : pct < 75 ? "Medium" : "Strong"}</span>
              </div>
            </div>
            <Input
              label="Confirm Password"
              icon={<Lock size={16} />}
              type="password"
              value={confirm}
              onChange={(e) => setConfirm(e.currentTarget.value)}
              disabled={isRedirecting}
            />
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                className="accent-primary"
                checked={agree}
                onChange={(e) => setAgree(e.currentTarget.checked)}
                disabled={isRedirecting}
              />
              I agree to the Terms & Conditions
            </label>
            
            {error && <p className="text-sm text-red-500">{error}</p>}
            
            <Button 
              type="submit" 
              loading={loading || isRedirecting} 
              className="w-full" 
              disabled={loading || isRedirecting}
            >
              {isRedirecting ? 'Redirecting...' : loading ? 'Creating Account...' : 'Create Account'}
            </Button>
          </form>

          <p className="mt-4 text-center text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link href="/login" className="text-primary hover:underline">
              Log in
            </Link>
          </p>
        </div>
      </div>
    </>
  )
}