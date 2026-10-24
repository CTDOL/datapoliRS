'use client';

import { useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { ROTULO_STATUS, TarefaQuadro } from './useQuadroTarefas';

const DIAS_SEMANA = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'];
const MESES = [
  'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
  'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro',
];

/** Data local no formato AAAA-MM-DD, o mesmo que o backend devolve em prazo. */
function chaveData(data: Date): string {
  const mes = String(data.getMonth() + 1).padStart(2, '0');
  const dia = String(data.getDate()).padStart(2, '0');
  return `${data.getFullYear()}-${mes}-${dia}`;
}

function formatarDia(chave: string): string {
  const [ano, mes, dia] = chave.split('-');
  return `${dia}/${mes}/${ano}`;
}

/** Visão mensal por prazo, com a lista das tarefas do dia escolhido e das tarefas sem prazo. */
export function CalendarioTarefas({ tarefas }: { tarefas: TarefaQuadro[] }) {
  const hoje = new Date();
  const hojeChave = chaveData(hoje);
  const [mes, setMes] = useState(new Date(hoje.getFullYear(), hoje.getMonth(), 1));
  const [diaSelecionado, setDiaSelecionado] = useState(hojeChave);

  const porDia = new Map<string, TarefaQuadro[]>();
  const semPrazo: TarefaQuadro[] = [];
  for (const tarefa of tarefas) {
    if (!tarefa.prazo) {
      semPrazo.push(tarefa);
      continue;
    }
    porDia.set(tarefa.prazo, [...(porDia.get(tarefa.prazo) ?? []), tarefa]);
  }

  const diasNoMes = new Date(mes.getFullYear(), mes.getMonth() + 1, 0).getDate();
  const celulas: (Date | null)[] = [
    ...Array<null>(mes.getDay()).fill(null),
    ...Array.from({ length: diasNoMes }, (_, i) => new Date(mes.getFullYear(), mes.getMonth(), i + 1)),
  ];
  while (celulas.length % 7 !== 0) celulas.push(null);

  const estaAtrasada = (t: TarefaQuadro) =>
    !!t.prazo && t.prazo < hojeChave && !(['Concluída', 'Cancelada'] as string[]).includes(t.tp_status);
  const doDia = porDia.get(diaSelecionado) ?? [];

  const mudarMes = (deslocamento: number) =>
    setMes(new Date(mes.getFullYear(), mes.getMonth() + deslocamento, 1));

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={() => mudarMes(-1)}
          aria-label="Mês anterior"
          className="p-2 rounded-lg text-zinc-300 hover:bg-zinc-800"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
        <h2 className="text-sm font-semibold capitalize text-white">
          {MESES[mes.getMonth()]} de {mes.getFullYear()}
        </h2>
        <button
          type="button"
          onClick={() => mudarMes(1)}
          aria-label="Próximo mês"
          className="p-2 rounded-lg text-zinc-300 hover:bg-zinc-800"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>

      <div role="grid" aria-label="Calendário de tarefas" className="grid grid-cols-7 gap-1 text-center">
        {DIAS_SEMANA.map((d) => (
          <div key={d} role="columnheader" className="text-[11px] uppercase text-zinc-500 py-1">{d}</div>
        ))}
        {celulas.map((data, indice) => {
          if (!data) return <div key={`vazio-${indice}`} />;
          const chave = chaveData(data);
          const tarefasDoDia = porDia.get(chave) ?? [];
          const temAtraso = tarefasDoDia.some(estaAtrasada);
          const selecionado = chave === diaSelecionado;
          return (
            <button
              key={chave}
              type="button"
              role="gridcell"
              onClick={() => setDiaSelecionado(chave)}
              aria-label={`${formatarDia(chave)}: ${tarefasDoDia.length} ${tarefasDoDia.length === 1 ? 'tarefa' : 'tarefas'}`}
              aria-selected={selecionado}
              className={`relative rounded-lg border py-2 text-sm transition-colors ${
                selecionado ? 'border-[color:var(--cor-primaria)] bg-zinc-800 text-white' : 'border-zinc-800 text-zinc-300 hover:bg-zinc-800/60'
              } ${chave === hojeChave ? 'font-bold' : ''}`}
            >
              {data.getDate()}
              {tarefasDoDia.length > 0 && (
                <span className="mt-0.5 block text-[10px] text-zinc-400">{tarefasDoDia.length}</span>
              )}
              {temAtraso && <span className="absolute top-1 right-1 h-1.5 w-1.5 rounded-full bg-red-400" aria-label="Tem tarefa atrasada" />}
            </button>
          );
        })}
      </div>

      <section aria-label="Tarefas do dia" className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-4 space-y-2">
        <h3 className="text-xs font-semibold uppercase text-zinc-300">Tarefas de {formatarDia(diaSelecionado)} ({doDia.length})</h3>
        {doDia.length === 0 && <p className="text-xs text-zinc-500">Nenhuma tarefa neste dia.</p>}
        {doDia.map((t) => (
          <ItemTarefa key={t.id_tarefa} tarefa={t} atrasada={estaAtrasada(t)} />
        ))}
      </section>

      {semPrazo.length > 0 && (
        <section aria-label="Tarefas sem prazo" className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-4 space-y-2">
          <h3 className="text-xs font-semibold uppercase text-zinc-300">Sem prazo ({semPrazo.length})</h3>
          {semPrazo.map((t) => (
            <ItemTarefa key={t.id_tarefa} tarefa={t} atrasada={false} />
          ))}
        </section>
      )}
    </div>
  );
}

function ItemTarefa({ tarefa, atrasada }: { tarefa: TarefaQuadro; atrasada: boolean }) {
  const nomes = (tarefa.responsaveis ?? []).map((r) => r.nm_completo);
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-3">
      <p className="text-sm text-white">{tarefa.titulo}</p>
      <p className="text-xs text-zinc-500">
        {ROTULO_STATUS[tarefa.tp_status]}
        {atrasada && <span className="ml-2 text-red-300">· atrasada</span>}
        {nomes.length > 0 ? ` · ${nomes.join(', ')}` : ' · sem responsável'}
      </p>
    </div>
  );
}
