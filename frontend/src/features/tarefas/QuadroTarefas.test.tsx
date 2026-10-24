import { describe, it, expect, vi, beforeEach } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { QuadroTarefas } from './QuadroTarefas';
import { usePermissoes } from '@/stores/usePermissoes';
import { useQuadroTarefas } from './useQuadroTarefas';

vi.mock('@/stores/usePermissoes', () => ({ usePermissoes: vi.fn() }));
vi.mock('next/navigation', () => ({ useSearchParams: () => new URLSearchParams() }));
vi.mock('./useQuadroTarefas', () => ({
  STATUS_QUADRO: ['Pendente', 'Em Andamento', 'Concluída'],
  ROTULO_STATUS: { Pendente: 'Aguardando início', 'Em Andamento': 'Em andamento', Concluída: 'Concluída' },
  useQuadroTarefas: vi.fn(),
}));

const TAREFAS = [
  { id_tarefa: '1', titulo: 'Ligar para a secretaria', tp_status: 'Pendente', id_projeto_lei: 'pl-1', nm_lideranca_responsavel: 'STIVE' },
  { id_tarefa: '2', titulo: 'Enviar ofício', tp_status: 'Concluída', id_emenda: 'em-1' },
];

function preparar(podeEscrever: boolean) {
  vi.mocked(usePermissoes).mockReturnValue({ podeEscrever, podeExcluir: false });
  vi.mocked(useQuadroTarefas).mockReturnValue({
    tarefas: TAREFAS as never,
    carregando: false,
    erro: null,
    mover: vi.fn(),
    listarComentarios: vi.fn().mockResolvedValue([]),
    comentar: vi.fn(),
    criar: vi.fn().mockResolvedValue(true),
    recarregar: vi.fn(),
  });
}

describe('QuadroTarefas', () => {
  beforeEach(() => vi.clearAllMocks());

  it('mostra as colunas com as tarefas em cada uma', () => {
    preparar(true);
    render(<QuadroTarefas />);

    expect(screen.getByRole('region', { name: 'Coluna Pendente' }).textContent).toContain('Ligar para a secretaria');
    // Concluídas ficam ocultas por padrão e aparecem ao ligar o filtro.
    expect(screen.queryByRole('region', { name: 'Coluna Concluída' })).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Mostrar concluídas' }));
    expect(screen.getByRole('region', { name: 'Coluna Concluída' }).textContent).toContain('Enviar ofício');
  });

  it('leitor vê o andamento, mas não move cartões nem comenta', () => {
    preparar(false);
    render(<QuadroTarefas />);

    expect(screen.queryByRole('button', { name: 'Mover para a próxima coluna' })).toBeNull();
    expect(screen.queryByLabelText('Registrar andamento')).toBeNull();
  });

  it('admin e operador movem cartões', () => {
    preparar(true);
    render(<QuadroTarefas />);

    expect(screen.getAllByRole('button', { name: 'Mover para a próxima coluna' }).length).toBeGreaterThan(0);
  });
});
