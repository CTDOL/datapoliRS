'use client';

import { useEffect, useState } from 'react';
import { ChevronLeft, ChevronRight, Loader2, MessageSquare } from 'lucide-react';
import { usePermissoes } from '@/stores/usePermissoes';
import { STATUS_QUADRO, StatusTarefa, TarefaQuadro, ComentarioTarefa, useQuadroTarefas } from './useQuadroTarefas';

/** Quadro de execução das tarefas do gabinete. Todos leem; admin e operador movem e comentam. */
export function QuadroTarefas() {
  const { podeEscrever } = usePermissoes();
  const { tarefas, carregando, erro, mover, listarComentarios, comentar } = useQuadroTarefas();
  const [selecionada, setSelecionada] = useState<TarefaQuadro | null>(null);

  if (carregando) {
    return <div className="flex items-center gap-2 text-zinc-400 text-sm"><Loader2 className="w-4 h-4 animate-spin" /> Carregando tarefas…</div>;
  }

  return (
    <div className="space-y-4">
      {erro && <p role="alert" className="text-sm text-red-400">{erro}</p>}
      <div className="grid gap-4 md:grid-cols-3">
        {STATUS_QUADRO.map((status) => {
          const itens = tarefas.filter((t) => t.tp_status === status);
          return (
            <section key={status} aria-label={`Coluna ${status}`} className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-4 space-y-3">
              <h2 className="text-xs font-semibold uppercase text-zinc-300">{status} <span className="text-zinc-500">({itens.length})</span></h2>
              {itens.length === 0 && <p className="text-xs text-zinc-500">Nenhuma tarefa.</p>}
              {itens.map((tarefa) => (
                <article key={tarefa.id_tarefa} className="rounded-xl border border-zinc-800 bg-zinc-950 p-3 space-y-2">
                  <button type="button" onClick={() => setSelecionada(tarefa)} className="text-left text-sm text-white hover:underline">
                    {tarefa.titulo}
                  </button>
                  <p className="text-xs text-zinc-500">
                    {tarefa.id_projeto_lei ? 'Projeto de lei' : tarefa.id_emenda ? 'Emenda' : 'Geral'}
                    {tarefa.nm_lideranca_responsavel ? ` · ${tarefa.nm_lideranca_responsavel}` : ' · sem responsável'}
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
          <button type="submit" className="px-3 py-2 rounded-lg bg-purple-600 text-white text-sm">Registrar</button>
        </form>
      )}
    </aside>
  );
}

export type { StatusTarefa };
