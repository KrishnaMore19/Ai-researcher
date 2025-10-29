"use client"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { BarChart3, FileText, MessageSquare, NotebookPen, CreditCard } from "lucide-react"
import { useAuthStore } from "@/store"

const items = [
  { href: "/dashboard", label: "Dashboard", icon: BarChart3 },
  { href: "/documents", label: "Documents", icon: FileText },
  { href: "/chat", label: "Chat", icon: MessageSquare },
  { href: "/notes", label: "Notes", icon: NotebookPen },
  { href: "/subscription", label: "subscription", icon: CreditCard }, // Pricing + settings separate in nav bar
]

export function Sidebar() {
  const pathname = usePathname()
  const { user } = useAuthStore()
  
  return (
    <aside className="hidden md:flex md:w-64 md:flex-col gap-2 p-4 border-r bg-card">
      <div className="mb-4">
        <Link href="/dashboard" className="inline-flex items-center gap-2">
          <div className="h-8 w-8 rounded-lg bg-primary" />
          <span className="font-semibold text-lg">AI Research</span>
        </Link>
      </div>
      <nav className="flex flex-col gap-1">
        {items.map((i) => {
          const Icon = i.icon
          const active = pathname.startsWith(i.href)
          return (
            <Link
              key={i.href}
              href={i.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm hover:bg-muted/10",
                active && "bg-primary/10 text-primary",
              )}
            >
              <Icon size={18} />
              {i.label}
            </Link>
          )
        })}
      </nav>
      <div className="mt-auto text-xs text-muted-foreground">
        <p>Signed in as</p>
        <p className="font-medium text-foreground">{user?.email || "No email available"}</p>
      </div>
    </aside>
  )
}