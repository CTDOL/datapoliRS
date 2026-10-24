'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ExternalLink, UserPlus, Trash2, Plus, Loader2, CheckCircle2, Circle, Clock } from 'lucide-react';
import { usePermissoes } from '@/stores/usePermissoes';
import { api } from '@/services/api';
import { ProjetoLei, descreverConferencia } from './useProjetosLei';
import { useProjetoLeiDetalhe } from './useProjetoLeiDetalhe';

interface LiderancaOption {
  id_lideranca: string;
  nm_completo: string;
}

const STATUS_ORDEM = ['Pendente', 'Em Andamento', 'Concluída'];
const STATUS_ICON: Record<string, typeof Circle> = {
  'Pendente': Circle,
  'Em Andamento': Clock,
  'Concluída': CheckCircle2,
};

interface ProjetoLeiDetailModalProps {
  projetoLei: ProjetoLei | null;
  onClose: () => void;
}

export function ProjetoLeiDetailModal({ projetoLei, onClose }: ProjetoLeiDetailModalProps) {
  const idProjetoLei = projetoLei?.id_projeto_lei || null;
  const {
    observadores, tarefas, isSubmitting,
    addObservador, removeObservador, createTarefa, updateTarefaStatus, deleteTarefa,
  } = useProjetoLeiDetalhe(idProjetoLei);
  const { podeEscrever, podeExcluir } = usePermissoes();

  const [liderancas, setLiderancas] = useState<LiderancaOption[]>([]);
  const [observadorSelecionado, setObservadorSelecionado] = useState('');
  const [novaTarefa, setNovaTarefa] = useState({ titulo: '', prazo: '', ids_responsaveis: [] as string[] });

  useEffect(() => {
    if (!projetoLei) return;
    api.get('/api/v1/gabinete/liderancas', { params: { page_size: 200 } })
      .then((res) => setLiderancas(res.data.items))
      .catch((err) => console.error(err));
    const timer = setTimeout(() => {
      setNovaTarefa({ titulo: '', prazo: '', ids_responsaveis: [] });
      setObservadorSelecionado('');
    }, 0);
    return () => clearTimeout(timer);
  }, [projetoLei]);

  const idsObservadores = new Set(observadores.map((o) => o.id_lideranca));
  const liderancasDisponiveis = liderancas.filter((l) => !idsObservadores.has(l.id_lideranca));

  const handleAddObservador = async () => {
    if (!observadorSelecionado) return;
    const ok = await addObservador(observadorSelecionado);
    if (ok) setObservadorSelecionado('');
  };

  const handleCreateTarefa = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!novaTarefa.titulo.trim()) return;
    const ok = await createTarefa({
      titulo: novaTarefa.titulo.trim(),
      prazo: novaTarefa.prazo || undefined,
      ids_responsaveis: novaTarefa.ids_responsaveis,
    });
    if (ok) setNovaTarefa({ titulo: '', prazo: '', ids_responsaveis: [] });
  };

  const cicloStatus = (atual: string) => {
    const idx = STATUS_ORDEM.indexOf(atual);
    return STATUS_ORDEM[(idx + 1) % STATUS_ORDEM.length];
  };

  return (
    <AnimatePresence>
      {projetoLei && (
        <>
          <motion.div
            key="backdrop"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-zinc-950/80 backdrop-blur-sm z-40"
          />
          <motion.div
            key="modal"
            initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-2xl bg-zinc-900 border border-zinc-700/50 rounded-3xl shadow-2xl z-50 overflow-hidden max-h-[90vh] overflow-y-auto"
          >
            <div className="p-6 border-b border-zinc-800 flex justify-between items-start sticky top-0 bg-zinc-900 z-10">
              <div>
                <h2 className="text-xl font-bold text-white">{projetoLei.tipo} {projetoLei.numero}/{projetoLei.ano}</h2>
                <p className="text-sm text-zinc-400 mt-1">{projetoLei.ementa}</p>
                <div className="flex items-center gap-3 mt-2 text-xs text-zinc-500">
                  {projetoLei.situacao && <span>Situação: {projetoLei.situacao}</span>}
                  <span title="Última conferência na fonte oficial">({descreverConferencia(projetoLei.ultima_sincronizacao)})</span>
                  {projetoLei.url_fonte && (
                    <a href={projetoLei.url_fonte} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-[color:var(--cor-texto-destaque)] hover:text-[color:var(--cor-texto-destaque)]">
                      Fonte oficial <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
              </div>
              <button onClick={onClose} className="text-zinc-400 hover:text-white transition-colors shrink-0">
                <X className="w-6 h-6" />
              </button>
            </div>

            <div className="p-6 space-y-6">
              {/* Observadores */}
              <div>
                <h3 className="text-xs font-semibold text-zinc-300 uppercase mb-3">Lideranças observadoras</h3>
                <div className="flex flex-wrap gap-2 mb-3">
                  {observadores.length === 0 && <p className="text-sm text-zinc-500">Nenhuma liderança vinculada ainda.</p>}
                  {observadores.map((o) => (
                    <span key={o.id_lideranca} className="flex items-center gap-1.5 bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 rounded-full pl-3 pr-1.5 py-1 text-xs">
                      {o.nm_completo}
                      {podeEscrever && (
                        <button onClick={() => removeObservador(o.id_lideranca)} className="hover:text-white p-0.5">
                          <X className="w-3 h-3" />
                        </button>
                      )}
                    </span>
                  ))}
                </div>
                {podeEscrever && (
                <div className="flex gap-2">
                  <select
                    value={observadorSelecionado}
                    onChange={(e) => setObservadorSelecionado(e.target.value)}
                    className="flex-1 bg-zinc-950 border border-zinc-800 rounded-xl px-3 py-2 text-sm text-white outline-none appearance-none focus:ring-2 focus:ring-[color:var(--cor-destaque-50)]"
                  >
                    <option value="">Selecionar liderança...</option>
                    {liderancasDisponiveis.map((l) => (
                      <option key={l.id_lideranca} value={l.id_lideranca}>{l.nm_completo}</option>
                    ))}
                  </select>
                  <button
                    onClick={handleAddObservador}
                    disabled={!observadorSelecionado || isSubmitting}
                    className="bg-[color:var(--cor-primaria)] hover:bg-[color:var(--cor-primaria-hover)] text-on-accent px-3 py-2 rounded-xl disabled:opacity-50 flex items-center gap-1.5 text-sm font-medium"
                  >
                    <UserPlus className="w-4 h-4" /> Vincular
                  </button>
                </div>
                )}
              </div>

              {/* Tarefas */}
              <div>
                <h3 className="text-xs font-semibold text-zinc-300 uppercase mb-3">Tarefas</h3>
                <div className="space-y-2 mb-3">
                  {tarefas.length === 0 && <p className="text-sm text-zinc-500">Nenhuma tarefa registrada.</p>}
                  {tarefas.map((t) => {
                    const Icon = STATUS_ICON[t.tp_status] || Circle;
                    return (
                      <div key={t.id_tarefa} className="flex items-center justify-between gap-3 bg-zinc-950/60 border border-zinc-800 rounded-xl px-3.5 py-2.5">
                        <button onClick={() => updateTarefaStatus(t.id_tarefa, cicloStatus(t.tp_status))} disabled={!podeEscrever} className="flex items-center gap-2 text-left min-w-0 flex-1 disabled:cursor-default">
                          <Icon className={`w-4 h-4 shrink-0 ${t.tp_status === 'Concluída' ? 'text-teal-400' : t.tp_status === 'Em Andamento' ? 'text-amber-400' : 'text-zinc-500'}`} />
                          <div className="min-w-0">
                            <p className={`text-sm truncate ${t.tp_status === 'Concluída' ? 'text-zinc-500 line-through' : 'text-white'}`}>{t.titulo}</p>
                            <p className="text-[11px] text-zinc-500">
                              {t.nm_lideranca_responsavel ? `${t.nm_lideranca_responsavel} · ` : ''}
                              {t.prazo ? `prazo ${t.prazo}` : 'sem prazo'} · {t.tp_status}
                            </p>
                          </div>
                        </button>
                        {podeExcluir && (
                          <button onClick={() => deleteTarefa(t.id_tarefa)} className="text-zinc-500 hover:text-red-400 p-1 shrink-0">
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    );
                  })}
                </div>
                {podeEscrever && (
                <form onSubmit={handleCreateTarefa} className="flex flex-wrap gap-2">
                  <input
                    type="text"
                    value={novaTarefa.titulo}
                    onChange={(e) => setNovaTarefa({ ...novaTarefa, titulo: e.target.value })}
                    placeholder="Nova tarefa..."
                    className="flex-1 min-w-[160px] bg-zinc-950 border border-zinc-800 rounded-xl px-3 py-2 text-sm text-white placeholder-zinc-500 outline-none focus:ring-2 focus:ring-[color:var(--cor-destaque-50)]"
                  />
                  <input
                    type="date"
                    value={novaTarefa.prazo}
                    onChange={(e) => setNovaTarefa({ ...novaTarefa, prazo: e.target.value })}
                    className="bg-zinc-950 border border-zinc-800 rounded-xl px-3 py-2 text-sm text-white outline-none focus:ring-2 focus:ring-[color:var(--cor-destaque-50)]"
                  />
                  <details className="relative">
                    <summary className="cursor-pointer list-none bg-zinc-950 border border-zinc-800 rounded-xl px-3 py-2 text-sm text-white">
                      Responsáveis ({novaTarefa.ids_responsaveis.length})
                    </summary>
                    <div className="absolute z-10 mt-1 w-64 max-h-60 overflow-y-auto rounded-xl border border-zinc-700 bg-zinc-900 p-2 space-y-1 shadow-xl">
                      {liderancas.length === 0 && <p className="text-xs text-zinc-500 px-1">Nenhuma liderança cadastrada.</p>}
                      {liderancas.map((l) => (
                        <label key={l.id_lideranca} className="flex items-center gap-2 px-1 py-1 text-sm text-zinc-200 hover:bg-zinc-800 rounded-lg cursor-pointer">
                          <input
                            type="checkbox"
                            checked={novaTarefa.ids_responsaveis.includes(l.id_lideranca)}
                            onChange={(e) => setNovaTarefa({
                              ...novaTarefa,
                              ids_responsaveis: e.target.checked
                                ? [...novaTarefa.ids_responsaveis, l.id_lideranca]
                                : novaTarefa.ids_responsaveis.filter((id) => id !== l.id_lideranca),
                            })}
                          />
                          {l.nm_completo}
                        </label>
                      ))}
                    </div>
                  </details>
                  <button
                    type="submit"
                    disabled={!novaTarefa.titulo.trim() || isSubmitting}
                    className="bg-[color:var(--cor-primaria)] hover:bg-[color:var(--cor-primaria-hover)] text-on-accent px-3 py-2 rounded-xl disabled:opacity-50 flex items-center gap-1.5 text-sm font-medium"
                  >
                    {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                  </button>
                </form>
                )}
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
