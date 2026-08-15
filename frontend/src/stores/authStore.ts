import { create } from 'zustand';

interface AuthState {
  accessToken: string | null;
  csrfToken: string | null;
  isAuthenticated: boolean;
  user: any | null;

  setTokens: (access: string, csrf: string) => void;
  setUser: (user: any) => void;
  logout: () => void;
  getAccessToken: () => string | null;
  getCsrfToken: () => string | null;
}

// Access token stored ONLY in memory (NOT localStorage)
let memoryAccessToken: string | null = null;

export const useAuthStore = create<AuthState>((set, get) => ({
  accessToken: null,
  csrfToken: null,
  isAuthenticated: false,
  user: null,

  setTokens: (access: string, csrf: string) => {
    memoryAccessToken = access;
    set({ accessToken: access, csrfToken: csrf, isAuthenticated: true });
  },

  setUser: (user: any) => {
    set({ user });
  },

  logout: () => {
    memoryAccessToken = null;
    // Clear legacy localStorage
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('auth-storage');
    localStorage.removeItem('token');
    set({ accessToken: null, csrfToken: null, isAuthenticated: false, user: null });
  },

  getAccessToken: () => memoryAccessToken,
  getCsrfToken: () => get().csrfToken,
}));
