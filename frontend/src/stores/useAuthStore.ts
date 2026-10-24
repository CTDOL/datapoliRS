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
  /** Preferências pessoais do usuário, gravadas no servidor (tb_users.preferencias). */
  preferencias?: PreferenciasUsuario;
}

export interface PreferenciasUsuario {
  mapa_padrao: 'liderancas' | 'votacao' | 'cruzada';
  fontes_legislativas: { alrs: boolean; camara: boolean; senado: boolean };
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  login: (user: User) => void;
  logout: () => void;
  /** Troca o tema sem recarregar: o layout reaplica o data-tema a partir deste valor. */
  atualizarTema: (tema: 'escuro' | 'claro') => void;
  /** Atualiza só as chaves informadas das preferências do usuário logado. */
  atualizarPreferencias: (parcial: Partial<PreferenciasUsuario>) => void;
}

export const useAuthStore = create<AuthState>()((set) => ({
  user: null,
  isAuthenticated: false,
  login: (user) => set({ user, isAuthenticated: true }),
  logout: () => set({ user: null, isAuthenticated: false }),
  atualizarTema: (tema) => set((estado) => (estado.user ? { user: { ...estado.user, tp_tema: tema } } : {})),
  atualizarPreferencias: (parcial) =>
    set((estado) =>
      estado.user
        ? { user: { ...estado.user, preferencias: { ...estado.user.preferencias, ...parcial } as PreferenciasUsuario } }
        : {}
    ),
}));
