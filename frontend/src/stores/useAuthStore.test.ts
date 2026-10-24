import { beforeEach, describe, expect, it } from 'vitest';
import { useAuthStore } from './useAuthStore';

describe('atualizarTema', () => {
  beforeEach(() => {
    useAuthStore.setState({ user: null, isAuthenticated: false });
  });

  it('troca o tema do usuário logado sem tocar nos outros campos', () => {
    useAuthStore.getState().login({ email: 'a@x.com', tenant_id: 't1', role: 'admin', tp_tema: 'escuro' });

    useAuthStore.getState().atualizarTema('claro');

    expect(useAuthStore.getState().user?.tp_tema).toBe('claro');
    expect(useAuthStore.getState().user?.email).toBe('a@x.com');
    expect(useAuthStore.getState().isAuthenticated).toBe(true);
  });

  it('sem usuário logado, não cria estado de usuário', () => {
    useAuthStore.getState().atualizarTema('claro');

    expect(useAuthStore.getState().user).toBeNull();
  });
});
