import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { TrocaSenhaObrigatoria } from './TrocaSenhaObrigatoria';
import { useAuthStore } from '@/stores/useAuthStore';
import { api } from '@/services/api';

vi.mock('@/services/api', () => ({ api: { post: vi.fn() } }));

describe('TrocaSenhaObrigatoria', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAuthStore.setState({ user: null, isAuthenticated: false });
  });

  it('não aparece quando a senha não está pendente', () => {
    useAuthStore.setState({ user: { email: 'a@b.com', tenant_id: 't', role: 'admin', must_change_password: false }, isAuthenticated: true });
    const { container } = render(<TrocaSenhaObrigatoria />);
    expect(container.innerHTML).toBe('');
  });

  it('não envia quando a confirmação não confere', () => {
    useAuthStore.setState({ user: { email: 'a@b.com', tenant_id: 't', role: 'admin', must_change_password: true }, isAuthenticated: true });
    const { container } = render(<TrocaSenhaObrigatoria />);
    const campos = container.querySelectorAll('input');
    fireEvent.change(campos[0], { target: { value: 'senha-inicial-123' } });
    fireEvent.change(campos[1], { target: { value: 'senha-nova-456' } });
    fireEvent.change(campos[2], { target: { value: 'outra-senha-789' } });
    fireEvent.submit(container.querySelector('form')!);
    expect(screen.getByRole('alert').textContent).toContain('não confere');
    expect(api.post).not.toHaveBeenCalled();
  });

  it('troca a senha e libera o sistema', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({ data: {} });
    useAuthStore.setState({ user: { email: 'a@b.com', tenant_id: 't', role: 'admin', must_change_password: true }, isAuthenticated: true });
    const { container } = render(<TrocaSenhaObrigatoria />);
    const campos = container.querySelectorAll('input');
    fireEvent.change(campos[0], { target: { value: 'senha-inicial-123' } });
    fireEvent.change(campos[1], { target: { value: 'senha-nova-456' } });
    fireEvent.change(campos[2], { target: { value: 'senha-nova-456' } });
    fireEvent.submit(container.querySelector('form')!);
    await vi.waitFor(() => expect(useAuthStore.getState().user?.must_change_password).toBe(false));
    expect(api.post).toHaveBeenCalledWith('/api/v1/auth/trocar-senha', { senha_atual: 'senha-inicial-123', nova_senha: 'senha-nova-456' });
  });
});
