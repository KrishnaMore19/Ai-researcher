// components/AuthProvider.tsx
'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuthStore } from '@/store';

interface AuthProviderProps {
  children: React.ReactNode;
}

export default function AuthProvider({ children }: AuthProviderProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { checkAuth, isAuthenticated } = useAuthStore();

  // Protected routes
  const protectedRoutes = [
    '/dashboard',
    '/documents',
    '/chat',
    '/notes',
    '/settings',
    '/subscription',
  ];

  // Public routes
  const publicRoutes = ['/', '/login', '/register'];

  useEffect(() => {
    // Don't do anything on public routes - let the page handle it
    if (publicRoutes.includes(pathname)) {
      return;
    }

    // Check authentication status on mount and route change
    const isAuth = checkAuth();

    // Check if current route is protected
    const isProtectedRoute = protectedRoutes.some((route) =>
      pathname.startsWith(route)
    );

    // If trying to access protected route without auth
    if (isProtectedRoute && !isAuth) {
      router.push(`/login?redirect=${pathname}`);
    }
  }, [pathname, checkAuth, isAuthenticated, router]);

  return <>{children}</>;
}