import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ObservabilidadePlataforma } from './ObservabilidadePlataforma';
import { api } from '@/services/api';

vi.mock('@/services/api', () => ({ api: { get: vi.fn(), post: vi.fn() } }));

const SAUDE = { api: { status: 'ok', versao: '2.0.0', ambiente: 'development' }, banco: { status: 'ok', latencia_ms: 2 }, cache: { status: 'indisponivel', detalhe: 'modo fallback' } };
const REGISTRO = { created_at: '2026-10-23T10:00:00Z', evento: 'login_falha', email: 'x@y.com', caminho: '/api/v1/auth/login', ip: '127.0.0.1', status_http: 401 };

function roteador(url: string) {
  if (url.endsWith('/saude')) return Promise.resolve({ data: SAUDE });
  if (url.endsWith('/alertas')) return Promise.resolve({ data: [{ severidade: 'alta', titulo: 'Tentativas de login repetidas', detalhe: 'x@y.com: 5 falhas' }] });
  return Promise.resolve({ data: [REGISTRO] });
}

describe('ObservabilidadePlataforma', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.get).mockImplementation((url: string) => roteador(url));
  });

  it('mostra saúde, alertas e a trilha de acesso', async () => {
    render(<ObservabilidadePlataforma />);

    await waitFor(() => expect(screen.getByText('Tentativas de login repetidas')).toBeTruthy());
    expect(screen.getAllByText('ok').length).toBe(2); // API e banco
    expect(screen.getAllByText('login_falha').length).toBeGreaterThan(0); // opção do filtro e linha da tabela
    expect(screen.getByText('indisponivel')).toBeTruthy();
  });

  it('expurgo só acontece depois da confirmação', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({ data: { removidos: 3 } });
    render(<ObservabilidadePlataforma />);
    await waitFor(() => expect(screen.getByText('Tentativas de login repetidas')).toBeTruthy());

    fireEvent.click(screen.getByText(/Expurgar acima de 6 meses/));
    expect(api.post).not.toHaveBeenCalled();
    fireEvent.click(screen.getByText('Confirmar expurgo'));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/api/v1/plataforma/logs/expurgo'));
    await waitFor(() => expect(screen.getByText(/3 registro\(s\)/)).toBeTruthy());
  });
});
