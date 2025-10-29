"use client"
import { cn } from "@/lib/utils"
import { type ReactNode, type InputHTMLAttributes, forwardRef } from "react"

interface Props extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  icon?: ReactNode
  error?: string
}

export const Input = forwardRef<HTMLInputElement, Props>(function Input(
  { className, label, icon, error, ...props },
  ref,
) {
  return (
    <label className="block text-sm">
      {label && <span className="mb-1 block text-muted-foreground">{label}</span>}
      <div
        className={cn(
          "flex items-center gap-2 rounded-lg border bg-card px-3 py-2 focus-within:ring-2 focus-within:ring-primary/40",
          error && "border-red-500 ring-red-500/30",
        )}
      >
        {icon && <span className="text-muted-foreground">{icon}</span>}
        <input
          ref={ref}
          className={cn("w-full bg-transparent outline-none placeholder:text-muted-foreground/70", className)}
          {...props}
        />
      </div>
      {error && <span className="mt-1 block text-xs text-red-500">{error}</span>}
    </label>
  )
})
