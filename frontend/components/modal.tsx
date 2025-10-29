"use client"
import { X } from "lucide-react"
import { type ReactNode, useEffect } from "react"
import { cn } from "@/lib/utils"

export function Modal({
  isOpen,
  onClose,
  title,
  children,
  footer,
  className,
}: {
  isOpen: boolean
  onClose: () => void
  title?: string
  children?: ReactNode
  footer?: ReactNode
  className?: string
}) {
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose()
    }
    if (isOpen) window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [isOpen, onClose])

  if (!isOpen) return null
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/40 backdrop-blur-sm p-4" onClick={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={cn(
          "w-full max-w-lg rounded-2xl border bg-card text-card-foreground glass animate-in fade-in zoom-in-95 duration-200",
          className,
        )}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b p-4">
          <h3 className="text-lg font-semibold">{title}</h3>
          <button aria-label="Close" onClick={onClose} className="p-1 rounded-md hover:bg-muted/10">
            <X size={18} />
          </button>
        </div>
        <div className="p-4">{children}</div>
        {footer && <div className="border-t p-4">{footer}</div>}
      </div>
    </div>
  )
}
