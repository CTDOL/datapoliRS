import { create } from 'zustand';

interface User {
  email: string;
  tenant_id: string;
  role: string;
  /** Nome do gabinete (tb_tenants.nm_mandato), usado no cabeçalho. */
  nm_mandato?: string | null;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  login: (user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()((set) => ({
  user: null,
  isAuthenticated: false,
  login: (user) => set({ user, isAuthenticated: true }),
  logout: () => set({ user: null, isAuthenticated: false }),
}));
