import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { BalcaoCaixa } from '../components/BalcaoCaixa';
import { balcaoService } from '../services/balcaoService';
import { useAuthStore } from '@/stores/useAuthStore';

vi.mock('../services/balcaoService', async (importOriginal) => {
  const original = await importOriginal<typeof import('../services/balcaoService')>();
  return {
    ...original,
    balcaoService: {
      ...original.balcaoService,
      listarEntradas: vi.fn(),
      obterEntrada: vi.fn(),
      efetivarEntrada: vi.fn(),
      descartarEntrada: vi.fn(),
      obterTimelineAtendido: vi.fn(),
      anexarAoAtendimento: vi.fn(),
      resolverAtendimento: vi.fn(),
    },
  };
});

describe('BalcaoCaixa (Triagem, Efetivação, Timeline e Resolução BAL-09/BAL-10)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAuthStore.setState({
      user: {
        email: 'operador@gabinete.rs',
        tenant_id: '11111111-1111-1111-1111-111111111111',
        role: 'operador',
      },
    });
  });

  it('carrega entrada, exibe alerta de assunto resolvido (365 dias), efetiva e exige evidência na resolução', async () => {
    vi.mocked(balcaoService.listarEntradas).mockResolvedValue([
      {
        id: 'ent-1',
        status: 'PENDENTE',
        texto_original: 'Solicito reforma da escola estadual em Santa Maria.',
        dados_extraidos: { nome: 'Maria Silva', telefone: '55999990000' },
        criado_em: '2026-11-13T10:00:00Z',
      },
    ]);

    vi.mocked(balcaoService.obterEntrada).mockResolvedValue({
      id: 'ent-1',
      status: 'PENDENTE',
      texto_original: 'Solicito reforma da escola estadual em Santa Maria.',
      dados_extraidos: { nome: 'Maria Silva', telefone: '55999990000' },
      criado_em: '2026-11-13T10:00:00Z',
      sugestoes: [
        {
          id: 'sug-1',
          atendimento_relacionado_id: 'atd-old',
          score_similaridade: 0.85,
          motivo: 'Demanda semelhante já resolvida nos últimos 365 dias',
        },
      ],
      anexos: [],
    });

    vi.mocked(balcaoService.efetivarEntrada).mockResolvedValue({
      atendimento_id: 'atd-1',
      atendido_id: 'atdo-1',
      protocolo: 'BAL-2026-000001',
    });

    vi.mocked(balcaoService.obterTimelineAtendido).mockResolvedValue([
      {
        tipo: 'ATENDIMENTO',
        id: 'atd-1',
        protocolo: 'BAL-2026-000001',
        tipo_evento: 'ABERTURA',
        resumo: 'Reforma da escola estadual',
        ocorrido_em: '2026-11-13T10:05:00Z',
      },
    ]);

    render(<BalcaoCaixa />);

    const itemLista = await screen.findByText(/Solicito reforma da escola estadual/i);
    fireEvent.click(itemLista);

    await waitFor(() => {
      expect(
        screen.getByText(/Alerta de assunto semelhante já resolvido \(365 dias\)/i)
      ).toBeTruthy();
    });

    fireEvent.click(screen.getByRole('button', { name: /Efetivar Entrada/i }));

    await waitFor(() => {
      expect(screen.getByText('BAL-2026-000001')).toBeTruthy();
    });

    // BAL-09: tentar resolver sem evidência exibe alerta e não chama API
    fireEvent.change(screen.getByLabelText(/Despacho de conclusão/i), {
      target: { value: 'Ofício encaminhado à SEDUC.' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Resolver Atendimento/i }));

    expect(screen.getByText(/Anexe uma evidência/i)).toBeTruthy();
    expect(balcaoService.resolverAtendimento).not.toHaveBeenCalled();

    // Anexa evidência e resolve com sucesso
    vi.mocked(balcaoService.anexarAoAtendimento).mockResolvedValue({
      id: 'anx-evid-1',
      mime_type: 'application/pdf',
      tamanho_bytes: 1024,
    });
    vi.mocked(balcaoService.resolverAtendimento).mockResolvedValue({
      id: 'res-1',
      atendimento_id: 'atd-1',
      resolvido_em: '2026-11-13T10:10:00Z',
    });

    const evidenciaFile = new File(['%PDF-1.4'], 'oficio.pdf', { type: 'application/pdf' });
    fireEvent.change(screen.getByLabelText(/Anexar evidência/i), {
      target: { files: [evidenciaFile] },
    });

    await waitFor(() => {
      expect(screen.getByText('Evidência anexada')).toBeTruthy();
    });

    fireEvent.click(screen.getByRole('button', { name: /Resolver Atendimento/i }));

    await waitFor(() => {
      expect(balcaoService.resolverAtendimento).toHaveBeenCalledWith('atd-1', {
        despacho: 'Ofício encaminhado à SEDUC.',
        evidencia_anexo_id: 'anx-evid-1',
      });
    });
  });
});
