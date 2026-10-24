import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { GabinetesPlataforma } from './GabinetesPlataforma';
import { api } from '@/services/api';

vi.mock('@/services/api', () => ({ api: { get: vi.fn(), post: vi.fn(), patch: vi.fn() } }));

const GABINETE = {
  id_tenant: 't-1', nm_mandato: 'Gabinete Deputada Estadual Delegada Nadine',
  ds_cargo_mandato: 'Deputada Estadual', is_ativo: true, emails_admin: 'nadine.demo@campanha.com.br',
};

describe('GabinetesPlataforma', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.get).mockResolvedValue({ data: [GABINETE] });
  });

  it('lista os gabinetes com o admin e o status', async () => {
    render(<GabinetesPlataforma />);

    await waitFor(() => expect(screen.getByText('Gabinete Deputada Estadual Delegada Nadine')).toBeTruthy());
    expect(screen.getByText(/nadine\.demo@campanha\.com\.br/)).toBeTruthy();
    expect(screen.getByText(/ativo/)).toBeTruthy();
  });

  it('cria um gabinete enviando o admin e a senha inicial', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({ data: {} });
    const { container } = render(<GabinetesPlataforma />);
    await waitFor(() => expect(screen.getByText(/nadine/)).toBeTruthy());

    const campos = container.querySelectorAll('form input');
    fireEvent.change(campos[0], { target: { value: 'Gabinete Novo' } });
    fireEvent.change(campos[1], { target: { value: 'Vereador' } });
    fireEvent.change(campos[3], { target: { value: 'novo.admin@campanha.com.br' } });
    fireEvent.change(campos[4], { target: { value: 'senha-inicial-123' } });
    fireEvent.submit(container.querySelector('form')!);

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/api/v1/plataforma/gabinetes', expect.objectContaining({
      nm_mandato: 'Gabinete Novo', email_admin: 'novo.admin@campanha.com.br', senha_inicial: 'senha-inicial-123',
    })));
  });

  it('desativa um gabinete pela API', async () => {
    vi.mocked(api.patch).mockResolvedValueOnce({ data: {} });
    render(<GabinetesPlataforma />);
    await waitFor(() => expect(screen.getByText('Desativar')).toBeTruthy());

    fireEvent.click(screen.getByText('Desativar'));

    await waitFor(() => expect(api.patch).toHaveBeenCalledWith('/api/v1/plataforma/gabinetes/t-1', { is_ativo: false }));
  });
});
