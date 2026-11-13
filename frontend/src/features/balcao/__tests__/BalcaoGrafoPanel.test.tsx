import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { BalcaoGrafoPanel } from '../components/BalcaoGrafoPanel';
import { balcaoService } from '../services/balcaoService';

vi.mock('../services/balcaoService', async (importOriginal) => {
  const original = await importOriginal<typeof import('../services/balcaoService')>();
  return {
    ...original,
    balcaoService: {
      ...original.balcaoService,
      obterGrafo: vi.fn(),
    },
  };
});

describe('BalcaoGrafoPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renderiza nós e exibe conexões ao selecionar um nó', async () => {
    vi.mocked(balcaoService.obterGrafo).mockResolvedValue({
      nos: [
        { id: 'atdo-1', tipo: 'ATENDIDO', rotulo: 'João da Silva' },
        { id: 'mun-1', tipo: 'MUNICIPIO', rotulo: 'Porto Alegre' },
      ],
      arestas: [{ origem: 'atdo-1', destino: 'mun-1', tipo: 'RESIDE_EM' }],
    });

    render(<BalcaoGrafoPanel />);

    const noAtendido = await screen.findByText('João da Silva');
    expect(screen.getByText('Porto Alegre')).toBeTruthy();

    fireEvent.click(noAtendido);

    await waitFor(() => {
      expect(screen.getByText('RESIDE_EM')).toBeTruthy();
    });
  });
});
