import { cn } from "@/lib/utils"

export function ProgressBar({
  value,
  max,
  color = "blue",
  className,
}: {
  value: number
  max: number
  color?: "blue" | "green" | "yellow" | "red" | "purple"
  className?: string
}) {
  const pct = Math.min(100, Math.round((value / max) * 100))
  let bar = "bg-primary"
  if (color === "green") bar = "bg-[color:var(--color-success)]"
  if (color === "yellow") bar = "bg-yellow-400"
  if (color === "red") bar = "bg-red-500"
  if (color === "purple") bar = "bg-secondary"

  return (
    <div className={cn("w-full rounded-full bg-muted/20 h-2", className)} aria-label="progress">
      <div className={cn("h-2 rounded-full transition-all duration-500", bar)} style={{ width: `${pct}%` }} />
    </div>
  )
}
