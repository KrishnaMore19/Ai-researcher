"use client"
import { Moon, Sun } from "lucide-react"
import { useEffect, useState } from "react"
import { cn } from "@/lib/utils"

export function ThemeToggle({ className }: { className?: string }) {
  const [dark, setDark] = useState(false)

  useEffect(() => {
    if (dark) {
      document.documentElement.classList.add("dark")
    } else {
      document.documentElement.classList.remove("dark")
    }
  }, [dark])

  return (
    <button
      aria-label="Toggle theme"
      onClick={() => setDark((d) => !d)}
      className={cn(
        "inline-flex items-center gap-2 rounded-lg border px-3 py-2 text-sm elevate bg-card text-foreground focus-ring",
        className,
      )}
    >
      {dark ? <Sun size={18} /> : <Moon size={18} />}
      <span className="hidden sm:inline">{dark ? "Light" : "Dark"}</span>
    </button>
  )
}
