import { create } from 'zustand';
import type { UserResponse } from '@/types';

interface UserState {
  userId: string;
  user: UserResponse | null;
  bootstrapped: boolean;
  setUser: (user: UserResponse) => void;
  setUserId: (id: string) => void;
  setBootstrapped: (v: boolean) => void;
}

export const useUserStore = create<UserState>((set) => ({
  userId: '',
  user: null,
  bootstrapped: false,
  setUser: (user) => set({ user }),
  setUserId: (id) => set({ userId: id }),
  setBootstrapped: (v) => set({ bootstrapped: v }),
}));
