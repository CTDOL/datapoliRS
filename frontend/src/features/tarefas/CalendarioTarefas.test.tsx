import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { CalendarioTarefas } from './CalendarioTarefas';
import type { TarefaQuadro } from './useQuadroTarefas';

function chaveHoje(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

const base = { id_tarefa: '', tenant_id: '', titulo: '', tp_status: 'Pendente' as const };

describe('CalendarioTarefas', () => {
  it('mostra as tarefas do dia escolhido e as sem prazo', () => {
    const tarefas: TarefaQuadro[] = [
      { ...base, id_tarefa: '1', titulo: 'Ligar para a secretaria', prazo: chaveHoje() },
      { ...base, id_tarefa: '2', titulo: 'Ideia solta', prazo: null },
    ];
    render(<CalendarioTarefas tarefas={tarefas} />);

    expect(screen.getByRole('region', { name: 'Tarefas do dia' }).textContent).toContain('Ligar para a secretaria');
    expect(screen.getByRole('region', { name: 'Tarefas sem prazo' }).textContent).toContain('Ideia solta');
  });

  it('indica o número de tarefas no dia e troca a lista ao escolher outro dia', () => {
    const tarefas: TarefaQuadro[] = [
      { ...base, id_tarefa: '1', titulo: 'Tarefa de hoje', prazo: chaveHoje() },
    ];
    render(<CalendarioTarefas tarefas={tarefas} />);

    const diaComTarefa = screen.getByRole('gridcell', { name: /: 1 tarefa$/ });
    expect(diaComTarefa).toBeTruthy();

    const outroDia = screen.getAllByRole('gridcell').find((c) => c.getAttribute('aria-label')?.endsWith(': 0 tarefas'));
    fireEvent.click(outroDia!);
    expect(screen.getByRole('region', { name: 'Tarefas do dia' }).textContent).toContain('Nenhuma tarefa neste dia.');
  });
});
