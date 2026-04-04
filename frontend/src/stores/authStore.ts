import { create } from 'zustand';
import { api } from '@/lib/axios';
import type { User } from '@/types';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  tenantId: string | null;
  setAuth: (user: User, token: string, tenantId: string | null) => void;
  logout: () => void;
  refreshToken: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  tenantId: null,

  setAuth: (user, token, tenantId) => {
    set({ user, accessToken: token, tenantId });
  },

  logout: () => {
    set({ user: null, accessToken: null, tenantId: null });
  },

  refreshToken: async () => {
    try {
      const response = await api.post<{ data: { accessToken: string } }>(
        '/auth/refresh'
      );
      const newToken = response.data.data.accessToken;
      const currentState = get();
      set({
        accessToken: newToken,
        user: currentState.user,
        tenantId: currentState.tenantId,
      });
    } catch {
      get().logout();
      throw new Error('Token refresh failed');
    }
  },
}));
