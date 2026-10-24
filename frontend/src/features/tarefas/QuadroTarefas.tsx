'use client';

import { useEffect, useState } from 'react';
import { ChevronLeft, ChevronRight, Loader2, MessageSquare, X } from 'lucide-react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { usePermissoes } from '@/stores/usePermissoes';
import { STATUS_QUADRO, ROTULO_STATUS, StatusTarefa, TarefaQuadro, ComentarioTarefa, useQuadroTarefas } from './useQuadroTarefas';
import { NovaTarefaForm } from './NovaTarefaForm';
import { CalendarioTarefas } from './CalendarioTarefas';

// Status que saem de cena: não entram em atraso e ficam ocultos por padrão (concluídas).
const STATUS_ENCERRADOS: string[] = ['Concluída', 'Cancelada'];

/** Quadro de execução das tarefas do gabinete. Todos leem; admin e operador movem e comentam. */
export function QuadroTarefas() {
  const { podeEscrever } = usePermissoes();
  const { tarefas, carregando, erro, mover, listarComentarios, comentar, criar } = useQuadroTarefas();
  const [selecionada, setSelecionada] = useState<TarefaQuadro | null>(null);
  const [criandoTarefa, setCriandoTarefa] = useState(false);
  const [visao, setVisao] = useState<'quadro' | 'calendario'>('quadro');
  // Filtro vindo do mapa: /tarefas?lideranca=<id>. Sem o parâmetro, o quadro mostra todas as tarefas.
  const parametros = useSearchParams();
  const idLiderancaFiltro = parametros.get('lideranca');
  // Filtro vindo da tabela de emendas: /tarefas?emenda=<id>. Também pré-seleciona a emenda no formulário.
  const idEmendaFiltro = parametros.get('emenda');
  const [mostrarConcluidas, setMostrarConcluidas] = useState(false);
  const [soAtrasadas, setSoAtrasadas] = useState(false);
  const hoje = new Date().toISOString().slice(0, 10);
  const estaAtrasada = (t: TarefaQuadro) =>
    !!t.prazo && t.prazo < hoje && !STATUS_ENCERRADOS.includes(t.tp_status);
  const totalAtrasadas = tarefas.filter(estaAtrasada).length;
  const tarefasDoFiltro = tarefas.filter((t) =>
    (!idLiderancaFiltro || (t.responsaveis ?? []).some((r) => r.id_lideranca === idLiderancaFiltro))
    && (!idEmendaFiltro || t.id_emenda === idEmendaFiltro)
  );
  // Concluídas ficam ocultas por padrão. "Atrasada" é calculada pelo prazo, não é um status gravado.
  const tarefasVisiveis = tarefasDoFiltro.filter((t) =>
    (mostrarConcluidas || t.tp_status !== 'Concluída') && (!soAtrasadas || estaAtrasada(t))
  );
  const colunas = STATUS_QUADRO.filter((s) => mostrarConcluidas || s !== 'Concluída');
  const nomeLiderancaFiltro = idLiderancaFiltro
    ? tarefas.flatMap((t) => t.responsaveis ?? []).find((r) => r.id_lideranca === idLiderancaFiltro)?.nm_completo
    : null;

  if (carregando) {
    return <div className="flex items-center gap-2 text-zinc-400 text-sm"><Loader2 className="w-4 h-4 animate-spin" /> Carregando tarefas…</div>;
  }

  return (
    <div className="space-y-4">
      {erro && <p role="alert" className="text-sm text-red-400">{erro}</p>}
      {(idLiderancaFiltro || idEmendaFiltro) && (
        <div className="flex items-center justify-between gap-3 rounded-xl border border-zinc-700 bg-zinc-900/60 px-4 py-2.5 text-sm text-zinc-200">
          <span>
            {idLiderancaFiltro && <>Filtrado pela liderança{nomeLiderancaFiltro ? <strong> {nomeLiderancaFiltro}</strong> : ''}</>}
            {idLiderancaFiltro && idEmendaFiltro && ' · '}
            {idEmendaFiltro && 'Tarefas de uma emenda'}
            : {tarefasVisiveis.length} {tarefasVisiveis.length === 1 ? 'tarefa' : 'tarefas'}
          </span>
          <Link href="/tarefas" className="flex items-center gap-1 text-zinc-400 hover:text-white">
            <X className="w-4 h-4" /> Ver todas
          </Link>
        </div>
      )}
      {podeEscrever && (
        <div className="flex justify-end">
          <button
            type="button"
            onClick={() => setCriandoTarefa((v) => !v)}
            className="bg-[color:var(--cor-primaria)] hover:bg-[color:var(--cor-primaria-hover)] text-on-accent px-4 py-2 rounded-xl text-sm font-medium"
          >
            {criandoTarefa ? 'Fechar' : 'Nova tarefa'}
          </button>
        </div>
      )}
      {criandoTarefa && podeEscrever && (
        <NovaTarefaForm
          emendaInicial={idEmendaFiltro}
          onCriar={criar}
          onFechar={() => setCriandoTarefa(false)}
        />
      )}
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <button
          type="button"
          onClick={() => setSoAtrasadas((v) => !v)}
          aria-pressed={soAtrasadas}
          className={`rounded-full border px-3 py-1 ${soAtrasadas ? 'border-red-400 text-red-300' : 'border-zinc-700 text-zinc-300'}`}
        >
          Atrasadas ({totalAtrasadas})
        </button>
        <button
          type="button"
          onClick={() => setMostrarConcluidas((v) => !v)}
          aria-pressed={mostrarConcluidas}
          className={`rounded-full border px-3 py-1 ${mostrarConcluidas ? 'border-zinc-400 text-white' : 'border-zinc-700 text-zinc-300'}`}
        >
          {mostrarConcluidas ? 'Ocultar concluídas' : 'Mostrar concluídas'}
        </button>
        <div role="group" aria-label="Modo de visualização" className="ml-auto flex rounded-full border border-zinc-700 p-0.5">
          {(['quadro', 'calendario'] as const).map((opcao) => (
            <button
              key={opcao}
              type="button"
              onClick={() => setVisao(opcao)}
              aria-pressed={visao === opcao}
              className={`rounded-full px-3 py-1 ${visao === opcao ? 'bg-zinc-700 text-white' : 'text-zinc-400'}`}
            >
              {opcao === 'quadro' ? 'Quadro' : 'Calendário'}
            </button>
          ))}
        </div>
      </div>
      {visao === 'calendario' ? (
        <CalendarioTarefas tarefas={tarefasVisiveis} />
      ) : (
      <div className={`grid gap-4 ${colunas.length === 2 ? 'md:grid-cols-2' : 'md:grid-cols-3'}`}>
        {colunas.map((status) => {
          const itens = tarefasVisiveis.filter((t) => t.tp_status === status);
          return (
            <section key={status} aria-label={`Coluna ${status}`} className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-4 space-y-3">
              <h2 className="text-xs font-semibold uppercase text-zinc-300">{ROTULO_STATUS[status]} <span className="text-zinc-500">({itens.length})</span></h2>
              {itens.length === 0 && <p className="text-xs text-zinc-500">Nenhuma tarefa.</p>}
              {itens.map((tarefa) => (
                <article key={tarefa.id_tarefa} className="rounded-xl border border-zinc-800 bg-zinc-950 p-3 space-y-2">
                  <button type="button" onClick={() => setSelecionada(tarefa)} className="text-left text-sm text-white hover:underline">
                    {tarefa.titulo}
                  </button>
                  {(tarefa.responsaveis ?? []).length > 0 && (
                    <ul className="flex flex-wrap gap-2">
                      {(tarefa.responsaveis ?? []).map((r) => (
                        <li key={r.id_lideranca} className="flex items-center gap-1.5 rounded-full border border-zinc-800 px-2 py-0.5">
                          {r.ds_foto_url ? (
                            // eslint-disable-next-line @next/next/no-img-element
                            <img src={r.ds_foto_url} alt={r.nm_completo} className="w-5 h-5 rounded-full object-cover" />
                          ) : (
                            <span className="w-5 h-5 rounded-full bg-[color:var(--cor-destaque-10)] flex items-center justify-center text-[10px] text-[color:var(--cor-texto-destaque)]">
                              {r.nm_completo.charAt(0)}
                            </span>
                          )}
                          <span className="text-xs text-zinc-200">{r.nm_completo}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                  <p className="text-xs text-zinc-500">
                    {tarefa.id_projeto_lei ? 'Projeto de lei' : tarefa.id_emenda ? 'Emenda' : 'Geral'}
                    {(tarefa.responsaveis ?? []).length === 0 ? ' · sem responsável' : ''}
                    {tarefa.prazo ? ` · prazo ${new Date(`${tarefa.prazo}T00:00:00`).toLocaleDateString('pt-BR')}` : ''}
                  </p>
                  {podeEscrever && (
                    <div className="flex gap-2">
                      <button type="button" aria-label="Mover para a coluna anterior" disabled={status === STATUS_QUADRO[0]}
                        onClick={() => mover(tarefa, STATUS_QUADRO[STATUS_QUADRO.indexOf(status) - 1])}
                        className="p-1 rounded border border-zinc-700 disabled:opacity-30"><ChevronLeft className="w-3.5 h-3.5" /></button>
                      <button type="button" aria-label="Mover para a próxima coluna" disabled={status === STATUS_QUADRO[STATUS_QUADRO.length - 1]}
                        onClick={() => mover(tarefa, STATUS_QUADRO[STATUS_QUADRO.indexOf(status) + 1])}
                        className="p-1 rounded border border-zinc-700 disabled:opacity-30"><ChevronRight className="w-3.5 h-3.5" /></button>
                    </div>
                  )}
                </article>
              ))}
            </section>
          );
        })}
      </div>
      )}
      {selecionada && <PainelComentarios tarefa={selecionada} podeComentar={podeEscrever} listar={listarComentarios} comentar={comentar} onFechar={() => setSelecionada(null)} />}
    </div>
  );
}

function PainelComentarios({ tarefa, podeComentar, listar, comentar, onFechar }: {
  tarefa: TarefaQuadro;
  podeComentar: boolean;
  listar: (id: string) => Promise<ComentarioTarefa[]>;
  comentar: (id: string, texto: string) => Promise<ComentarioTarefa>;
  onFechar: () => void;
}) {
  const [comentarios, setComentarios] = useState<ComentarioTarefa[]>([]);
  const [texto, setTexto] = useState('');
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    let ativo = true;
    listar(tarefa.id_tarefa)
      .then((lista) => { if (ativo) setComentarios(lista); })
      .catch(() => { if (ativo) setErro('Não foi possível carregar os comentários.'); });
    return () => { ativo = false; };
  }, [tarefa.id_tarefa, listar]);

  const enviar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!texto.trim()) return;
    try {
      const novo = await comentar(tarefa.id_tarefa, texto.trim());
      setComentarios((atual) => [...atual, novo]);
      setTexto('');
    } catch {
      setErro('Não foi possível registrar o comentário.');
    }
  };

  return (
    <aside aria-label="Comentários da tarefa" className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5 space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2"><MessageSquare className="w-4 h-4" /> {tarefa.titulo}</h2>
        <button type="button" onClick={onFechar} className="text-xs text-zinc-400 underline">Fechar</button>
      </div>
      {erro && <p role="alert" className="text-xs text-red-400">{erro}</p>}
      {comentarios.length === 0 ? (
        <p className="text-xs text-zinc-500">Nenhum andamento registrado.</p>
      ) : (
        <ul className="space-y-2">
          {comentarios.map((c) => (
            <li key={c.id_comentario} className="text-sm text-zinc-200">
              <span className="text-xs text-zinc-500">{new Date(c.created_at).toLocaleString('pt-BR')} · {c.autor_email}</span>
              <p>{c.texto}</p>
            </li>
          ))}
        </ul>
      )}
      {podeComentar && (
        <form onSubmit={enviar} className="flex gap-2">
          <label className="sr-only" htmlFor="novo-comentario">Registrar andamento</label>
          <input id="novo-comentario" value={texto} onChange={(e) => setTexto(e.target.value)} maxLength={2000}
            placeholder="Registrar andamento…" className="flex-1 bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-white" />
          <button type="submit" className="px-3 py-2 rounded-lg bg-[color:var(--cor-primaria)] text-on-accent text-sm">Registrar</button>
        </form>
      )}
    </aside>
  );
}

export type { StatusTarefa };
