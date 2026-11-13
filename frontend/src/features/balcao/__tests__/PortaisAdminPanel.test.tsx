import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { PortaisAdminPanel } from '../components/PortaisAdminPanel';
import { balcaoService } from '../services/balcaoService';

vi.mock('../services/balcaoService', async (importOriginal) => {
  const original = await importOriginal<typeof import('../services/balcaoService')>();
  return {
    ...original,
    balcaoService: {
      ...original.balcaoService,
      criarPortal: vi.fn(),
      revogarPortal: vi.fn(),
    },
  };
});

describe('PortaisAdminPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('gera novo portal com token único e revoga portal existente', async () => {
    vi.mocked(balcaoService.criarPortal).mockResolvedValue({
      id: 'portal-uuid-1',
      token: 'token-secreto-abc',
      ativo: true,
      criado_em: '2026-11-13T11:00:00Z',
    });
    vi.mocked(balcaoService.revogarPortal).mockResolvedValue({
      id: 'portal-uuid-1',
      ativo: false,
    });

    render(<PortaisAdminPanel />);

    fireEvent.click(screen.getByRole('button', { name: /Gerar Novo Portal/i }));

    await waitFor(() => {
      expect(screen.getByText(/\/portal\/token-secreto-abc/)).toBeTruthy();
    });

    fireEvent.change(screen.getByLabelText(/ID do portal para revogar/i), {
      target: { value: 'portal-uuid-1' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Revogar Portal/i }));

    await waitFor(() => {
      expect(screen.getByRole('status').textContent).toMatch(/portal-uuid-1 revogado/i);
    });
  });
});
