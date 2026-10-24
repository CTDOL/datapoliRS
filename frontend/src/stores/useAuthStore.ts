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
  /** Tema da interface do gabinete. Ausente ou null é tratado como escuro. */
  tp_tema?: 'escuro' | 'claro' | null;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  login: (user: User) => void;
  logout: () => void;
  /** Troca o tema sem recarregar: o layout reaplica o data-tema a partir deste valor. */
  atualizarTema: (tema: 'escuro' | 'claro') => void;
}

export const useAuthStore = create<AuthState>()((set) => ({
  user: null,
  isAuthenticated: false,
  login: (user) => set({ user, isAuthenticated: true }),
  logout: () => set({ user: null, isAuthenticated: false }),
  atualizarTema: (tema) => set((estado) => (estado.user ? { user: { ...estado.user, tp_tema: tema } } : {})),
}));
