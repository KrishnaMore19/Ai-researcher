import type React from "react"
import { cn } from "@/lib/utils"

type Color = "green" | "yellow" | "red" | "blue" | "purple"
type Variant = "filled" | "outline" | "subtle"

const colorMap: Record<Color, { bg: string; text: string; ring: string }> = {
  green: {
    bg: "bg-[color:var(--color-success)]",
    text: "text-[color:var(--color-success-foreground)]",
    ring: "ring-[color:var(--color-success)]",
  },
  yellow: { bg: "bg-yellow-400", text: "text-black", ring: "ring-yellow-400" },
  red: { bg: "bg-red-500", text: "text-white", ring: "ring-red-500" },
  blue: { bg: "bg-primary", text: "text-primary-foreground", ring: "ring-primary" },
  purple: { bg: "bg-secondary", text: "text-secondary-foreground", ring: "ring-secondary" },
}

export function Badge({
  children,
  color = "blue",
  variant = "filled",
  className,
}: {
  children: React.ReactNode
  color?: Color
  variant?: Variant
  className?: string
}) {
  const c = colorMap[color]
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-1 text-xs",
        variant === "filled" && `${c.bg} ${c.text}`,
        variant === "outline" && `border ${c.ring} text-foreground`,
        variant === "subtle" && `bg-muted/20 text-foreground`,
        className,
      )}
    >
      {children}
    </span>
  )
}
