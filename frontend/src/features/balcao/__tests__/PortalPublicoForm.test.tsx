import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { PortalPublicoForm } from '../components/PortalPublicoForm';
import { balcaoService, LIMITE_ANEXO_BYTES } from '../services/balcaoService';

vi.mock('../services/balcaoService', async (importOriginal) => {
  const original = await importOriginal<typeof import('../services/balcaoService')>();
  return {
    ...original,
    balcaoService: {
      ...original.balcaoService,
      enviarEntradaPortal: vi.fn(),
    },
  };
});

describe('PortalPublicoForm (BAL-01 / BAL-02)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('envia demanda e exibe apenas confirmação genérica sem protocolo nem id', async () => {
    vi.mocked(balcaoService.enviarEntradaPortal).mockResolvedValue({
      mensagem: 'Solicitação recebida com sucesso.',
    });

    render(<PortalPublicoForm token="tok-123" />);

    fireEvent.change(screen.getByLabelText(/Descreva sua solicitação/i), {
      target: { value: 'Precisamos de apoio para transporte escolar em Santa Maria.' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Enviar solicitação/i }));

    await waitFor(() => {
      expect(screen.getByRole('status').textContent).toContain('Solicitação recebida com sucesso.');
    });

    expect(balcaoService.enviarEntradaPortal).toHaveBeenCalledWith(
      'tok-123',
      'Precisamos de apoio para transporte escolar em Santa Maria.',
      null
    );
    expect(screen.queryByText(/BAL-2026/i)).toBeNull();
  });

  it('rejeita arquivo acima de 10 MB antes de chamar a API', async () => {
    render(<PortalPublicoForm token="tok-123" />);

    const arquivoGrande = new File(['x'], 'grande.pdf', { type: 'application/pdf' });
    Object.defineProperty(arquivoGrande, 'size', { value: LIMITE_ANEXO_BYTES + 1 });

    const input = screen.getByLabelText(/Anexar documento ou foto/i);
    fireEvent.change(input, { target: { files: [arquivoGrande] } });

    expect(screen.getByRole('alert').textContent).toMatch(/limite máximo de 10 MB/i);
    expect(balcaoService.enviarEntradaPortal).not.toHaveBeenCalled();
  });

  it.each([
    [404, /inválido ou foi desativado/i],
    [413, /limite máximo de 10 MB/i],
    [415, /Formato de arquivo não permitido/i],
    [429, /Muitas solicitações seguidas/i],
    [503, /temporariamente indisponível/i],
  ])('trata erro HTTP %i da API do portal', async (status, esperado) => {
    vi.mocked(balcaoService.enviarEntradaPortal).mockRejectedValue({
      response: { status },
    });

    render(<PortalPublicoForm token="tok-123" />);
    fireEvent.change(screen.getByLabelText(/Descreva sua solicitação/i), {
      target: { value: 'Texto de teste' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Enviar solicitação/i }));

    await waitFor(() => {
      expect(screen.getByRole('alert').textContent).toMatch(esperado);
    });
  });
});
