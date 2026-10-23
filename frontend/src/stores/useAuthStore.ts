import { create } from 'zustand';

interface User {
  email: string;
  tenant_id: string;
  role: string;
  /** Nome do gabinete (tb_tenants.nm_mandato), usado no cabeçalho. */
  nm_mandato?: string | null;
  /** Senha pendente: o sistema mostra o formulário de troca antes de liberar as telas (ADR 037). */
  must_change_password?: boolean;
  /** Cor de destaque do gabinete (ADR 038). Null = padrão da plataforma. */
  cor_primaria?: string | null;
  cor_secundaria?: string | null;
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
