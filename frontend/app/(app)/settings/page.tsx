"use client"
import { Button } from "@/components/button"
import { Card } from "@/components/card"
import { useState, useEffect } from "react"
import { useToast } from "@/components/toast-provider"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useAuthStore } from "@/store"
import { useSettingsStore } from "@/store"
import { useRouter } from "next/navigation"

export default function SettingsPage() {
  const { showToast } = useToast()
  const router = useRouter()
  const { user, logout } = useAuthStore()
  
  // Get preferences from settings store
  const { preferences, setDefaultModel, setTheme, setNotifications, updatePreferences } = useSettingsStore()
  
  const [loading, setLoading] = useState(false)
  const [deleteLoading, setDeleteLoading] = useState(false)
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  
  // Local state for preferences (synced with store)
  const [model, setModel] = useState(preferences.defaultModel)
  const [theme, setThemeState] = useState(preferences.theme)
  const [responseLength, setResponseLength] = useState<'Concise' | 'Balanced' | 'Detailed'>('Balanced')
  const [autoSave, setAutoSave] = useState<'On' | 'Off'>('On')

  // Load user data and preferences on mount
  useEffect(() => {
    if (user) {
      setName(user.full_name || "")
      setEmail(user.email || "")
    }
    
    // Sync local state with store
    setModel(preferences.defaultModel)
    setThemeState(preferences.theme)
  }, [user, preferences])

  async function updateProfile() {
    if (!name.trim() || !email.trim()) {
      showToast("Please fill in all fields", "error")
      return
    }

    setLoading(true)
    try {
      // TODO: Implement API call to update user profile
      // For now, just show success message
      await new Promise(resolve => setTimeout(resolve, 800))
      showToast("Profile updated successfully", "success")
    } catch (error) {
      showToast("Failed to update profile", "error")
    } finally {
      setLoading(false)
    }
  }

  function savePreferences() {
    try {
      // Update all preferences in store
      updatePreferences({
        defaultModel: model,
        theme: theme,
      })
      
      // Apply theme immediately
      setTheme(theme)
      
      showToast("Preferences saved successfully", "success")
    } catch (error) {
      showToast("Failed to save preferences", "error")
    }
  }

  function handleLogout() {
    try {
      logout()
      showToast("Logged out successfully", "success")
      router.push("/login")
    } catch (error) {
      showToast("Failed to logout", "error")
    }
  }

  async function handleDeleteAccount() {
    const confirmed = window.confirm(
      "Are you sure you want to delete your account? This action cannot be undone."
    )
    
    if (!confirmed) return

    setDeleteLoading(true)
    try {
      // TODO: Implement API call to delete account
      await new Promise(resolve => setTimeout(resolve, 1000))
      showToast("Account scheduled for deletion", "error")
      logout()
      router.push("/login")
    } catch (error) {
      showToast("Failed to delete account", "error")
    } finally {
      setDeleteLoading(false)
    }
  }

  return (
    <div className="grid gap-6">
      <Card glass className="p-5">
        <h2 className="mb-4 text-sm font-semibold text-muted-foreground">Profile</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="text-sm">
            <span className="mb-1 block text-muted-foreground">Full Name</span>
            <input
              className="w-full rounded-lg border bg-card px-3 py-2 outline-none"
              value={name}
              onChange={(e) => setName(e.currentTarget.value)}
            />
          </label>
          <label className="text-sm">
            <span className="mb-1 block text-muted-foreground">Email</span>
            <input
              className="w-full rounded-lg border bg-card px-3 py-2 outline-none"
              value={email}
              onChange={(e) => setEmail(e.currentTarget.value)}
            />
          </label>
        </div>
        <div className="mt-4">
          <Button onClick={updateProfile} loading={loading}>
            Update Profile
          </Button>
        </div>
      </Card>

      <Card glass className="p-5">
        <h2 className="mb-4 text-sm font-semibold text-muted-foreground">AI Preferences</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <label className="text-sm">
            <span className="mb-1 block text-muted-foreground">Default AI Model</span>
            <Select value={model} onValueChange={setModel}>
              <SelectTrigger className="w-full bg-card dark:bg-black dark:text-white">
                <SelectValue placeholder="Select model" />
              </SelectTrigger>
              <SelectContent className="dark:bg-black dark:text-white dark:border-white/10">
                <SelectItem value="llama">Llama 3.1</SelectItem>
                <SelectItem value="dolphin">Dolphin 2.9</SelectItem>
                <SelectItem value="gemma">Gemma 2</SelectItem>
              </SelectContent>
            </Select>
          </label>
          
          <label className="text-sm">
            <span className="mb-1 block text-muted-foreground">Response Length</span>
            <Select value={responseLength} onValueChange={(v: string) => setResponseLength(v as 'Concise' | 'Balanced' | 'Detailed')}>
              <SelectTrigger className="w-full bg-card dark:bg-black dark:text-white">
                <SelectValue placeholder="Select length" />
              </SelectTrigger>
              <SelectContent className="dark:bg-black dark:text-white dark:border-white/10">
                <SelectItem value="Concise">Concise</SelectItem>
                <SelectItem value="Balanced">Balanced</SelectItem>
                <SelectItem value="Detailed">Detailed</SelectItem>
              </SelectContent>
            </Select>
          </label>

          <label className="text-sm">
            <span className="mb-1 block text-muted-foreground">Theme</span>
            <Select value={theme} onValueChange={(v: string) => setThemeState(v as "Light" | "Dark" | "Auto")}>
              <SelectTrigger className="w-full bg-card dark:bg-black dark:text-white">
                <SelectValue placeholder="Select theme" />
              </SelectTrigger>
              <SelectContent className="dark:bg-black dark:text-white dark:border-white/10">
                <SelectItem value="Light">Light</SelectItem>
                <SelectItem value="Dark">Dark</SelectItem>
                <SelectItem value="Auto">Auto</SelectItem>
              </SelectContent>
            </Select>
          </label>

          <label className="text-sm">
            <span className="mb-1 block text-muted-foreground">Auto-Save Notes</span>
            <Select value={autoSave} onValueChange={(v: string) => setAutoSave(v as "On" | "Off")}>
              <SelectTrigger className="w-full bg-card dark:bg-black dark:text-white">
                <SelectValue placeholder="Select preference" />
              </SelectTrigger>
              <SelectContent className="dark:bg-black dark:text-white dark:border-white/10">
                <SelectItem value="On">Enabled</SelectItem>
                <SelectItem value="Off">Disabled</SelectItem>
              </SelectContent>
            </Select>
          </label>
        </div>
        <div className="mt-4">
          <Button onClick={savePreferences}>Save Preferences</Button>
        </div>
      </Card>

      <Card glass className="p-5">
        <h2 className="mb-4 text-sm font-semibold text-muted-foreground">Danger Zone</h2>
        <div className="flex flex-wrap gap-2">
          <Button variant="ghost" onClick={handleLogout}>
            Logout
          </Button>
          <Button 
            variant="danger" 
            onClick={handleDeleteAccount}
            loading={deleteLoading}
          >
            Delete Account
          </Button>
        </div>
      </Card>
    </div>
  )
}