import { useState } from 'react';
import { Loader2, Edit2, Trash2, Search, ChevronLeft, ChevronRight } from 'lucide-react';
import { Emenda } from './useEmendas';

const SITUACAO_STYLES: Record<string, string> = {
  Indicada: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  Empenhada: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  Paga: 'bg-teal-500/10 text-teal-400 border-teal-500/20',
  Cancelada: 'bg-red-500/10 text-red-400 border-red-500/20',
};

function formatMoney(value: string | number) {
  return Number(value).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

interface EmendasTableProps {
  emendas: Emenda[];
  isLoading: boolean;
  onEdit?: (emenda: Emenda) => void;
  onDelete?: (emenda: Emenda) => void;
  canDelete?: boolean;
  termo: string;
  onTermoChange: (termo: string) => void;
  anoExercicio: number | '';
  onAnoChange: (ano: number | '') => void;
  tpSituacao: string;
  onSituacaoChange: (situacao: string) => void;
  page: number;
  totalPages: number;
  total: number;
  onPageChange: (page: number) => void;
}

export function EmendasTable({
  emendas,
  isLoading,
  onEdit,
  onDelete,
  canDelete = false,
  termo,
  onTermoChange,
  anoExercicio,
  onAnoChange,
  tpSituacao,
  onSituacaoChange,
  page,
  totalPages,
  total,
  onPageChange,
}: EmendasTableProps) {
  const [confirmandoId, setConfirmandoId] = useState<string | null>(null);

  return (
    <div className="flex-1 bg-zinc-900/50 backdrop-blur-md border border-zinc-800 rounded-2xl overflow-hidden flex flex-col shadow-2xl">
      <div className="p-4 border-b border-zinc-800 flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[220px] max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
          <input
            type="text"
            value={termo}
            onChange={(e) => onTermoChange(e.target.value)}
            placeholder="Buscar por objeto ou número..."
            className="w-full bg-zinc-950/60 border border-zinc-700/50 rounded-xl pl-9 pr-4 py-2 text-sm text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
          />
        </div>
        <input
          type="number"
          value={anoExercicio}
          onChange={(e) => onAnoChange(e.target.value ? Number(e.target.value) : '')}
          placeholder="Ano"
          className="w-24 bg-zinc-950/60 border border-zinc-700/50 rounded-xl px-3 py-2 text-sm text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
        />
        <select
          value={tpSituacao}
          onChange={(e) => onSituacaoChange(e.target.value)}
          className="bg-zinc-950/60 border border-zinc-700/50 rounded-xl px-3 py-2 text-sm text-white outline-none appearance-none focus:ring-2 focus:ring-purple-500/50"
        >
          <option value="">Todas as situações</option>
          <option value="Indicada">Indicada</option>
          <option value="Empenhada">Empenhada</option>
          <option value="Paga">Paga</option>
          <option value="Cancelada">Cancelada</option>
        </select>
      </div>

      <div className="overflow-x-auto flex-1">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-zinc-950/50 border-b border-zinc-800 text-zinc-400 text-xs uppercase tracking-wider">
              <th className="px-6 py-4 font-semibold">Objeto</th>
              <th className="px-6 py-4 font-semibold">Município</th>
              <th className="px-6 py-4 font-semibold">Ano</th>
              <th className="px-6 py-4 font-semibold">Indicado</th>
              <th className="px-6 py-4 font-semibold">Empenhado</th>
              <th className="px-6 py-4 font-semibold">Pago</th>
              <th className="px-6 py-4 font-semibold">Situação</th>
              <th className="px-6 py-4 font-semibold text-right">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/50 text-sm">
            {isLoading ? (
              <tr><td colSpan={8} className="px-6 py-12 text-center"><Loader2 className="w-8 h-8 text-purple-500 animate-spin mx-auto mb-4" /><p className="text-zinc-400">Carregando...</p></td></tr>
            ) : emendas.length === 0 ? (
              <tr><td colSpan={8} className="px-6 py-12 text-center text-zinc-400">Nenhuma emenda encontrada.</td></tr>
            ) : (
              emendas.map((e) => (
                <tr key={e.id_emenda} className="hover:bg-zinc-800/30 transition-colors duration-200">
                  <td className="px-6 py-4 font-medium text-white max-w-xs">
                    <p className="truncate" title={e.ds_objeto}>{e.ds_objeto}</p>
                    {e.nr_emenda && <p className="text-xs text-zinc-500">Nº {e.nr_emenda}</p>}
                  </td>
                  <td className="px-6 py-4 text-zinc-300">{e.nm_municipio || e.cd_ibge_7 || 'N/I'}</td>
                  <td className="px-6 py-4 text-zinc-300">{e.ano_exercicio}</td>
                  <td className="px-6 py-4 text-zinc-300">{formatMoney(e.vl_indicado)}</td>
                  <td className="px-6 py-4 text-zinc-300">{formatMoney(e.vl_empenhado)}</td>
                  <td className="px-6 py-4 text-zinc-300">{formatMoney(e.vl_pago)}</td>
                  <td className="px-6 py-4">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium border ${SITUACAO_STYLES[e.tp_situacao] || 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20'}`}>
                      {e.tp_situacao}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <button onClick={() => onEdit && onEdit(e)} className="text-zinc-400 hover:text-purple-400 p-2 transition-colors">
                        <Edit2 className="w-4 h-4" />
                      </button>
                      {canDelete && (
                        confirmandoId === e.id_emenda ? (
                          <div className="flex items-center gap-1">
                            <button
                              onClick={() => {
                                setConfirmandoId(null);
                                if (onDelete) onDelete(e);
                              }}
                              className="text-xs font-semibold text-red-400 hover:text-red-300 px-2 py-1 rounded-lg border border-red-500/30 hover:bg-red-500/10"
                            >
                              Confirmar
                            </button>
                            <button
                              onClick={() => setConfirmandoId(null)}
                              className="text-xs text-zinc-400 hover:text-white px-2 py-1"
                            >
                              Cancelar
                            </button>
                          </div>
                        ) : (
                          <button onClick={() => setConfirmandoId(e.id_emenda)} className="text-zinc-400 hover:text-red-400 p-2 transition-colors">
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
        <span>{total} emenda{total === 1 ? '' : 's'} no total</span>
        <div className="flex items-center gap-3">
          <button
            onClick={() => onPageChange(Math.max(1, page - 1))}
            disabled={page <= 1}
            className="p-1.5 rounded-lg border border-zinc-700/50 text-zinc-400 hover:text-white hover:bg-zinc-800 disabled:opacity-30 disabled:pointer-events-none"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span>Página {page} de {totalPages}</span>
          <button
            onClick={() => onPageChange(Math.min(totalPages, page + 1))}
            disabled={page >= totalPages}
            className="p-1.5 rounded-lg border border-zinc-700/50 text-zinc-400 hover:text-white hover:bg-zinc-800 disabled:opacity-30 disabled:pointer-events-none"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
