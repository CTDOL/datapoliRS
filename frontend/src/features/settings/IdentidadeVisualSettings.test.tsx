import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { IdentidadeVisualSettings } from './IdentidadeVisualSettings';
import { api } from '@/services/api';

vi.mock('@/services/api', () => ({ api: { get: vi.fn(), put: vi.fn() } }));

describe('IdentidadeVisualSettings', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.get).mockResolvedValue({ data: { cor_primaria: '#1d4ed8', cor_secundaria: null } });
  });

  it('leitura: campos desabilitados e sem botão de salvar para quem não é admin', async () => {
    render(<IdentidadeVisualSettings isAdmin={false} />);

    await waitFor(() => expect(screen.getByLabelText('Cor primária')).toBeTruthy());
    expect((screen.getByLabelText('Cor primária') as HTMLInputElement).disabled).toBe(true);
    expect(screen.queryByText('Salvar cores')).toBeNull();
  });

  it('admin salva as cores pela API', async () => {
    vi.mocked(api.put).mockResolvedValueOnce({ data: {} });
    const { container } = render(<IdentidadeVisualSettings isAdmin={true} />);

    await waitFor(() => expect(screen.getByLabelText('Cor primária')).toBeTruthy());
    fireEvent.submit(container.querySelector('form')!);

    await waitFor(() => expect(api.put).toHaveBeenCalledWith('/api/v1/gabinete/tema',
      { cor_primaria: '#1d4ed8', cor_secundaria: '#0e7490', tp_tema: 'escuro' }));
  });

  it('mostra o motivo quando a API recusa a cor (contraste)', async () => {
    vi.mocked(api.put).mockRejectedValueOnce({ response: { data: { detail: 'Cor com contraste insuficiente' } } });
    const { container } = render(<IdentidadeVisualSettings isAdmin={true} />);

    await waitFor(() => expect(screen.getByLabelText('Cor primária')).toBeTruthy());
    fireEvent.submit(container.querySelector('form')!);

    await waitFor(() => expect(screen.getByRole('alert').textContent).toContain('contraste insuficiente'));
  });
});
