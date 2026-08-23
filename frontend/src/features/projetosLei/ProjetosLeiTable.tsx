import { Loader2, ExternalLink, Trash2, ChevronLeft, ChevronRight, Users } from 'lucide-react';
import { useState } from 'react';
import { ProjetoLei } from './useProjetosLei';

const FONTE_LABEL: Record<string, string> = {
  ALRS: 'Assembleia RS',
  CAMARA: 'Câmara dos Deputados',
  SENADO: 'Senado Federal',
};

interface ProjetosLeiTableProps {
  projetosLei: ProjetoLei[];
  isLoading: boolean;
  onAbrir: (projetoLei: ProjetoLei) => void;
  onDelete?: (projetoLei: ProjetoLei) => void;
  canDelete?: boolean;
  termo: string;
  onTermoChange: (termo: string) => void;
  fonte: string;
  onFonteChange: (fonte: string) => void;
  page: number;
  totalPages: number;
  total: number;
  onPageChange: (page: number) => void;
}

export function ProjetosLeiTable({
  projetosLei,
  isLoading,
  onAbrir,
  onDelete,
  canDelete = false,
  termo,
  onTermoChange,
  fonte,
  onFonteChange,
  page,
  totalPages,
  total,
  onPageChange,
}: ProjetosLeiTableProps) {
  const [confirmandoId, setConfirmandoId] = useState<string | null>(null);

  return (
    <div className="flex-1 bg-zinc-900/50 backdrop-blur-md border border-zinc-800 rounded-2xl overflow-hidden flex flex-col shadow-2xl">
      <div className="p-4 border-b border-zinc-800 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-sm font-semibold text-white uppercase tracking-wide">Projetos de lei acompanhados</h2>
        <div className="flex flex-wrap items-center gap-3">
          <input
            type="text"
            value={termo}
            onChange={(e) => onTermoChange(e.target.value)}
            placeholder="Buscar por ementa/autor/número..."
            className="w-64 bg-zinc-950/60 border border-zinc-700/50 rounded-xl px-3 py-2 text-sm text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
          />
          <select
            value={fonte}
            onChange={(e) => onFonteChange(e.target.value)}
            className="bg-zinc-950/60 border border-zinc-700/50 rounded-xl px-3 py-2 text-sm text-white outline-none appearance-none focus:ring-2 focus:ring-purple-500/50"
          >
            <option value="">Todas as fontes</option>
            <option value="ALRS">Assembleia RS</option>
            <option value="CAMARA">Câmara dos Deputados</option>
            <option value="SENADO">Senado Federal</option>
          </select>
        </div>
      </div>

      <div className="overflow-x-auto flex-1">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-zinc-950/50 border-b border-zinc-800 text-zinc-400 text-xs uppercase tracking-wider">
              <th className="px-6 py-4 font-semibold">Proposição</th>
              <th className="px-6 py-4 font-semibold">Ementa</th>
              <th className="px-6 py-4 font-semibold">Fonte</th>
              <th className="px-6 py-4 font-semibold">Situação</th>
              <th className="px-6 py-4 font-semibold text-right">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/50 text-sm">
            {isLoading ? (
              <tr><td colSpan={5} className="px-6 py-12 text-center"><Loader2 className="w-8 h-8 text-purple-500 animate-spin mx-auto mb-4" /><p className="text-zinc-400">Carregando...</p></td></tr>
            ) : projetosLei.length === 0 ? (
              <tr><td colSpan={5} className="px-6 py-12 text-center text-zinc-400">Nenhum projeto de lei importado ainda.</td></tr>
            ) : (
              projetosLei.map((pl) => (
                <tr key={pl.id_projeto_lei} className="hover:bg-zinc-800/30 transition-colors duration-200 cursor-pointer" onClick={() => onAbrir(pl)}>
                  <td className="px-6 py-4 font-medium text-white whitespace-nowrap">{pl.tipo} {pl.numero}/{pl.ano}</td>
                  <td className="px-6 py-4 text-zinc-300 max-w-sm"><p className="truncate" title={pl.ementa}>{pl.ementa}</p></td>
                  <td className="px-6 py-4 text-zinc-400 text-xs">{FONTE_LABEL[pl.fonte] || pl.fonte}</td>
                  <td className="px-6 py-4 text-zinc-300">{pl.situacao || '—'}</td>
                  <td className="px-6 py-4 text-right" onClick={(e) => e.stopPropagation()}>
                    <div className="flex items-center justify-end gap-1">
                      <button onClick={() => onAbrir(pl)} className="text-zinc-400 hover:text-purple-400 p-2 transition-colors" title="Observadores e tarefas">
                        <Users className="w-4 h-4" />
                      </button>
                      {pl.url_fonte && (
                        <a href={pl.url_fonte} target="_blank" rel="noopener noreferrer" className="text-zinc-400 hover:text-white p-2 transition-colors inline-block" title="Ver na fonte oficial">
                          <ExternalLink className="w-4 h-4" />
                        </a>
                      )}
                      {canDelete && (
                        confirmandoId === pl.id_projeto_lei ? (
                          <div className="flex items-center gap-1">
                            <button
                              onClick={() => { setConfirmandoId(null); if (onDelete) onDelete(pl); }}
                              className="text-xs font-semibold text-red-400 hover:text-red-300 px-2 py-1 rounded-lg border border-red-500/30 hover:bg-red-500/10"
                            >
                              Confirmar
                            </button>
                            <button onClick={() => setConfirmandoId(null)} className="text-xs text-zinc-400 hover:text-white px-2 py-1">
                              Cancelar
                            </button>
                          </div>
                        ) : (
                          <button onClick={() => setConfirmandoId(pl.id_projeto_lei)} className="text-zinc-400 hover:text-red-400 p-2 transition-colors">
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between px-6 py-4 border-t border-zinc-800 text-sm text-zinc-400">
        <span>{total} projeto{total === 1 ? '' : 's'} de lei acompanhado{total === 1 ? '' : 's'}</span>
        <div className="flex items-center gap-3">
          <button onClick={() => onPageChange(Math.max(1, page - 1))} disabled={page <= 1} className="p-1.5 rounded-lg border border-zinc-700/50 text-zinc-400 hover:text-white hover:bg-zinc-800 disabled:opacity-30 disabled:pointer-events-none">
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span>Página {page} de {totalPages}</span>
          <button onClick={() => onPageChange(Math.min(totalPages, page + 1))} disabled={page >= totalPages} className="p-1.5 rounded-lg border border-zinc-700/50 text-zinc-400 hover:text-white hover:bg-zinc-800 disabled:opacity-30 disabled:pointer-events-none">
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
