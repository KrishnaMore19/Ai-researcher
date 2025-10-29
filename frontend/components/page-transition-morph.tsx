// components/page-transition.tsx
"use client"

import { useEffect, useRef } from 'react'
import { usePathname } from 'next/navigation'
import gsap from 'gsap'

interface PageTransitionProps {
  children: React.ReactNode
}

export function PageTransitionMorph({ children }: PageTransitionProps) {
  const pathname = usePathname()
  const contentRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const content = contentRef.current
    if (!content) return

    // Scroll to top on page change
    window.scrollTo({ top: 0, behavior: 'smooth' })

    // Simple, clean animation
    const tl = gsap.timeline()

    tl.fromTo(
      content,
      {
        opacity: 0,
        y: 20,
      },
      {
        opacity: 1,
        y: 0,
        duration: 0.6,
        ease: 'power2.out',
      }
    )

    return () => {
      tl.kill()
    }
  }, [pathname])

  return (
    <div ref={contentRef}>
      {children}
    </div>
  )
}