'use client';

import { useEffect, useState } from 'react';
import { Loader2, Plus } from 'lucide-react';
import { api } from '@/services/api';
import { NovaTarefaQuadro } from './useQuadroTarefas';

interface Opcao {
  id: string;
  rotulo: string;
}

interface Props {
  /** Emenda já escolhida (vinda de /tarefas?emenda=<id>). Sem ela, a tarefa é solta ou de projeto. */
  emendaInicial?: string | null;
  onCriar: (dados: NovaTarefaQuadro) => Promise<boolean>;
  onFechar: () => void;
}

type Origem = 'solta' | 'emenda' | 'projeto';

/** Formulário de nova tarefa: solta, de emenda ou de projeto de lei, com vários responsáveis e prazo. */
export function NovaTarefaForm({ emendaInicial, onCriar, onFechar }: Props) {
  const [titulo, setTitulo] = useState('');
  const [prazo, setPrazo] = useState('');
  const [origem, setOrigem] = useState<Origem>(emendaInicial ? 'emenda' : 'solta');
  const [idEmenda, setIdEmenda] = useState(emendaInicial ?? '');
  const [idProjeto, setIdProjeto] = useState('');
  const [idsResponsaveis, setIdsResponsaveis] = useState<string[]>([]);
  const [liderancas, setLiderancas] = useState<Opcao[]>([]);
  const [emendas, setEmendas] = useState<Opcao[]>([]);
  const [projetos, setProjetos] = useState<Opcao[]>([]);
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    api.get('/api/v1/gabinete/liderancas', { params: { page_size: 200 } })
      .then((res) => setLiderancas(res.data.items.map((l: { id_lideranca: string; nm_completo: string }) => ({ id: l.id_lideranca, rotulo: l.nm_completo }))))
      .catch(() => setLiderancas([]));
    api.get('/api/v1/gabinete/emendas', { params: { page_size: 200 } })
      .then((res) => setEmendas(res.data.items.map((e: { id_emenda: string; ds_objeto: string; nr_emenda?: string | null }) => ({
        id: e.id_emenda,
        rotulo: e.nr_emenda ? `${e.nr_emenda} · ${e.ds_objeto}` : e.ds_objeto,
      }))))
      .catch(() => setEmendas([]));
    api.get('/api/v1/gabinete/projetos-lei', { params: { page_size: 200 } })
      .then((res) => setProjetos(res.data.items.map((p: { id_projeto_lei: string; numero?: string | null; ementa?: string | null }) => ({
        id: p.id_projeto_lei,
        rotulo: p.numero ? `${p.numero} · ${p.ementa ?? ''}` : (p.ementa ?? 'Projeto de lei'),
      }))))
      .catch(() => setProjetos([]));
  }, []);

  const alternarResponsavel = (id: string, marcado: boolean) => {
    setIdsResponsaveis((atual) => (marcado ? [...atual, id] : atual.filter((x) => x !== id)));
  };

  const enviar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (titulo.trim().length < 3) return;
    if (origem === 'emenda' && !idEmenda) return;
    if (origem === 'projeto' && !idProjeto) return;
    setEnviando(true);
    const ok = await onCriar({
      titulo: titulo.trim(),
      prazo: prazo || undefined,
      ids_responsaveis: idsResponsaveis,
      id_emenda: origem === 'emenda' ? idEmenda : undefined,
      id_projeto_lei: origem === 'projeto' ? idProjeto : undefined,
    });
    setEnviando(false);
    if (ok) {
      setTitulo('');
      setPrazo('');
      setIdsResponsaveis([]);
      onFechar();
    }
  };

  const campo = 'bg-zinc-950 border border-zinc-800 rounded-xl px-3 py-2 text-sm text-white outline-none focus:ring-2 focus:ring-[color:var(--cor-destaque-50)]';

  return (
    <form onSubmit={enviar} className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-4 space-y-3">
      <div className="flex flex-wrap gap-2">
        <input
          type="text"
          value={titulo}
          onChange={(e) => setTitulo(e.target.value)}
          placeholder="Título da tarefa"
          required
          minLength={3}
          className={`flex-1 min-w-[200px] ${campo}`}
        />
        <input type="date" value={prazo} onChange={(e) => setPrazo(e.target.value)} className={campo} aria-label="Prazo" />
      </div>

      <div className="flex flex-wrap gap-2 text-sm">
        <label className="flex items-center gap-1.5 text-zinc-300">
          Vínculo
          <select value={origem} onChange={(e) => setOrigem(e.target.value as Origem)} className={campo}>
            <option value="solta">Tarefa solta</option>
            <option value="emenda">Emenda</option>
            <option value="projeto">Projeto de lei</option>
          </select>
        </label>
        {origem === 'emenda' && (
          <select value={idEmenda} onChange={(e) => setIdEmenda(e.target.value)} className={`min-w-[220px] ${campo}`} aria-label="Emenda">
            <option value="">Escolha a emenda…</option>
            {emendas.map((o) => <option key={o.id} value={o.id}>{o.rotulo}</option>)}
          </select>
        )}
        {origem === 'projeto' && (
          <select value={idProjeto} onChange={(e) => setIdProjeto(e.target.value)} className={`min-w-[220px] ${campo}`} aria-label="Projeto de lei">
            <option value="">Escolha o projeto…</option>
            {projetos.map((o) => <option key={o.id} value={o.id}>{o.rotulo}</option>)}
          </select>
        )}
      </div>

      <fieldset className="space-y-1">
        <legend className="text-xs font-semibold uppercase text-zinc-400 mb-1">Responsáveis ({idsResponsaveis.length})</legend>
        {liderancas.length === 0 && <p className="text-xs text-zinc-500">Nenhuma liderança cadastrada.</p>}
        <div className="flex flex-wrap gap-2">
          {liderancas.map((l) => (
            <label key={l.id} className="flex items-center gap-1.5 rounded-full border border-zinc-700 px-2.5 py-1 text-xs text-zinc-200 cursor-pointer">
              <input
                type="checkbox"
                checked={idsResponsaveis.includes(l.id)}
                onChange={(e) => alternarResponsavel(l.id, e.target.checked)}
              />
              {l.rotulo}
            </label>
          ))}
        </div>
      </fieldset>

      <div className="flex justify-end gap-2">
        <button type="button" onClick={onFechar} className="px-3 py-2 rounded-xl text-sm text-zinc-300 hover:text-white">
          Cancelar
        </button>
        <button
          type="submit"
          disabled={enviando || titulo.trim().length < 3}
          className="bg-[color:var(--cor-primaria)] hover:bg-[color:var(--cor-primaria-hover)] text-on-accent px-4 py-2 rounded-xl text-sm font-medium flex items-center gap-1.5 disabled:opacity-50"
        >
          {enviando ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
          Criar tarefa
        </button>
      </div>
    </form>
  );
}
