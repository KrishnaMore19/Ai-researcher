import { cn } from "@/lib/utils"
import type { HTMLAttributes } from "react"

export function Card({
  className,
  glass,
  hover = true,
  ...props
}: HTMLAttributes<HTMLDivElement> & { glass?: boolean; hover?: boolean }) {
  return (
    <div
      className={cn(
        "rounded-xl border bg-card text-card-foreground",
        glass && "glass",
        hover && "elevate",
        "p-4",
        className,
      )}
      {...props}
    />
  )
}
