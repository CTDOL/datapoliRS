import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { CabecalhoSessao } from './CabecalhoSessao';
import { useAuthStore } from '@/stores/useAuthStore';

describe('CabecalhoSessao', () => {
  beforeEach(() => {
    useAuthStore.setState({ user: null, isAuthenticated: false });
  });

  it('não aparece sem sessão', () => {
    const { container } = render(<CabecalhoSessao />);
    expect(container.innerHTML).toBe('');
  });

  it('mostra gabinete, usuário e perfil traduzido do papel', () => {
    useAuthStore.setState({
      user: {
        email: 'nadine.demo@campanha.com.br',
        tenant_id: 'abc',
        role: 'admin',
        nm_mandato: 'Gabinete Deputada Estadual Delegada Nadine',
      },
      isAuthenticated: true,
    });

    render(<CabecalhoSessao />);

    expect(screen.getByText('Gabinete Deputada Estadual Delegada Nadine')).toBeTruthy();
    expect(screen.getByText('nadine.demo@campanha.com.br')).toBeTruthy();
    expect(screen.getByText('Administrador')).toBeTruthy();
  });

  it('sem nome de gabinete mostra travessão em vez de vazio', () => {
    useAuthStore.setState({
      user: { email: 'x@y.com', tenant_id: 'abc', role: 'leitor' },
      isAuthenticated: true,
    });

    render(<CabecalhoSessao />);

    expect(screen.getByText('—')).toBeTruthy();
    expect(screen.getByText('Leitor')).toBeTruthy();
  });
});
