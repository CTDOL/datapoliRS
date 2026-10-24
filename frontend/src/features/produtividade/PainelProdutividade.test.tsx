import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { PainelProdutividade } from './PainelProdutividade';
import { api } from '@/services/api';

vi.mock('@/services/api', () => ({ api: { get: vi.fn() } }));

const DADOS = {
  tarefas: { total: 5, pendente: 2, em_andamento: 1, concluida: 2, atrasadas: 1 },
  por_responsavel: [{ nome: 'STIVE', abertas: 2, concluidas: 1 }, { nome: null, abertas: 1, concluidas: 0 }],
  comentarios_ultimos_7_dias: 4,
  projetos_lei: 10,
  emendas: 3,
};

describe('PainelProdutividade', () => {
  beforeEach(() => vi.clearAllMocks());

  it('mostra os indicadores e a carga por responsável', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: DADOS });
    render(<PainelProdutividade />);

    expect(await screen.findByText('Atrasadas')).toBeTruthy();
    expect(screen.getByText('Comentários (7 dias)')).toBeTruthy();
    expect(screen.getByText('STIVE')).toBeTruthy();
    expect(screen.getByText('Sem responsável')).toBeTruthy();
  });

  it('mostra erro quando o painel não carrega', async () => {
    vi.mocked(api.get).mockRejectedValue(new Error('403'));
    render(<PainelProdutividade />);

    expect(await screen.findByRole('alert')).toBeTruthy();
  });
});
