'use client';

import { useEffect, type ReactNode } from 'react';
import { useUserStore } from '@/stores/user';
import { getMe, createUser } from '@/lib/api';
import { Spinner } from '@/components/ui/Spinner';

export function Bootstrap({ children }: { children: ReactNode }) {
  const { bootstrapped, user, setUser, setUserId, setBootstrapped } = useUserStore();

  useEffect(() => {
    async function boot() {
      const stored = localStorage.getItem('userId');
      if (stored) {
        setUserId(stored);
        try {
          const user = await getMe();
          setUser(user);
          setBootstrapped(true);
          return;
        } catch {
          // fall through to create
        }
      }

      try {
        const user = await createUser({
          display_name: 'Demo User',
          email: 'demo@contentmarketer.com',
        });
        setUser(user);
        setUserId(user.id);
        localStorage.setItem('userId', user.id);
        setBootstrapped(true);
      } catch {
        // bootstrap failed — still show UI
        setBootstrapped(true);
      }
    }

    boot();
  }, [setUser, setUserId, setBootstrapped]);

  if (!bootstrapped) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <>
      <nav className="bg-navy-950 text-white px-6 py-3 flex items-center justify-between border-b border-navy-800">
        <span className="font-semibold text-base tracking-tight">Content Marketer</span>
        {user && (
          <div className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-full bg-primary-500/20 text-primary-300 flex items-center justify-center text-xs font-medium">
              {user.display_name.charAt(0).toUpperCase()}
            </div>
            <span className="text-sm text-navy-300">{user.display_name}</span>
          </div>
        )}
      </nav>
      {children}
    </>
  );
}
