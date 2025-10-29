"use client"
import { createContext, useCallback, useContext, useMemo, useState } from "react"
import type React from "react"

import { X } from "lucide-react"

type ToastType = "success" | "error" | "info" | "warning"
type Toast = { id: number; title: string; type: ToastType }

const ToastCtx = createContext<{ showToast: (title: string, type?: ToastType) => void } | null>(null)

export function useToast() {
  const ctx = useContext(ToastCtx)
  if (!ctx) throw new Error("useToast must be used within ToastProvider")
  return ctx
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])
  const showToast = useCallback((title: string, type: ToastType = "info") => {
    const id = Date.now()
    setToasts((t) => [...t, { id, title, type }])
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 3000)
  }, [])
  const value = useMemo(() => ({ showToast }), [showToast])

  return (
    <ToastCtx.Provider value={value}>
      {children}
      <div className="pointer-events-none fixed right-4 top-4 z-50 flex flex-col gap-2">
        {toasts.map((t) => (
          <div
            key={t.id}
            className="pointer-events-auto glass rounded-lg border px-4 py-2 shadow-md animate-in slide-in-from-top-4"
          >
            <div className="flex items-center gap-3">
              <span
                className={
                  t.type === "success"
                    ? "h-2 w-2 rounded-full bg-[color:var(--color-success)]"
                    : t.type === "error"
                      ? "h-2 w-2 rounded-full bg-red-500"
                      : t.type === "warning"
                        ? "h-2 w-2 rounded-full bg-yellow-400"
                        : "h-2 w-2 rounded-full bg-primary"
                }
              />
              <p className="text-sm">{t.title}</p>
              <button
                className="ml-4 rounded p-1 hover:bg-muted/20"
                onClick={() => setToasts((s) => s.filter((x) => x.id !== t.id))}
              >
                <X size={14} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  )
}
