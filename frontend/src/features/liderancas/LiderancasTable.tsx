import { useState } from 'react';
import { Loader2, Edit2, Trash2, Search, ChevronLeft, ChevronRight } from 'lucide-react';
import { Lideranca } from './useLiderancas';

interface LiderancasTableProps {
  liderancas: Lideranca[];
  isLoading: boolean;
  onEdit?: (lideranca: Lideranca) => void;
  onDelete?: (lideranca: Lideranca) => void;
  canDelete?: boolean;
  termo: string;
  onTermoChange: (termo: string) => void;
  page: number;
  totalPages: number;
  total: number;
  onPageChange: (page: number) => void;
}

export function LiderancasTable({
  liderancas,
  isLoading,
  onEdit,
  onDelete,
  canDelete = false,
  termo,
  onTermoChange,
  page,
  totalPages,
  total,
  onPageChange,
}: LiderancasTableProps) {
  const [confirmandoId, setConfirmandoId] = useState<string | null>(null);

  return (
    <div className="flex-1 bg-zinc-900/50 backdrop-blur-md border border-zinc-800 rounded-2xl overflow-hidden flex flex-col shadow-2xl">
      <div className="p-4 border-b border-zinc-800">
        <div className="relative max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
          <input
            type="text"
            value={termo}
            onChange={(e) => onTermoChange(e.target.value)}
            placeholder="Buscar por nome..."
            className="w-full bg-zinc-950/60 border border-zinc-700/50 rounded-xl pl-9 pr-4 py-2 text-sm text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
          />
        </div>
      </div>

      <div className="overflow-x-auto flex-1">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-zinc-950/50 border-b border-zinc-800 text-zinc-400 text-xs uppercase tracking-wider">
              <th className="px-6 py-4 font-semibold">Nome Completo</th>
              <th className="px-6 py-4 font-semibold">Telefone</th>
              <th className="px-6 py-4 font-semibold">Cód. IBGE</th>
              <th className="px-6 py-4 font-semibold">Tipo</th>
              <th className="px-6 py-4 font-semibold">Status</th>
              <th className="px-6 py-4 font-semibold text-right">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/50 text-sm">
            {isLoading ? (
              <tr><td colSpan={6} className="px-6 py-12 text-center"><Loader2 className="w-8 h-8 text-purple-500 animate-spin mx-auto mb-4" /><p className="text-zinc-400">Carregando...</p></td></tr>
            ) : liderancas.length === 0 ? (
              <tr><td colSpan={6} className="px-6 py-12 text-center text-zinc-400">Nenhuma liderança encontrada.</td></tr>
            ) : (
              liderancas.map((l) => (
                <tr key={l.id_lideranca} className="hover:bg-zinc-800/30 transition-colors duration-200">
                  <td className="px-6 py-4 font-medium text-white flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-purple-500/10 flex items-center justify-center text-purple-400">{l.nm_completo.charAt(0)}</div>
                    {l.nm_completo}
                  </td>
                  <td className="px-6 py-4 text-zinc-300">{l.nr_telefone}</td>
                  <td className="px-6 py-4 text-zinc-300">{l.nm_municipio || l.cd_ibge_7 || 'N/I'}</td>
                  <td className="px-6 py-4"><span className="px-3 py-1 rounded-full text-xs font-medium bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">{l.tp_influencia}</span></td>
                  <td className="px-6 py-4"><span className={`flex items-center gap-2 ${l.is_ativo ? 'text-teal-400' : 'text-zinc-500'}`}><span className={`w-2 h-2 rounded-full ${l.is_ativo ? 'bg-teal-400' : 'bg-zinc-500'}`} />{l.is_ativo ? 'Ativo' : 'Inativo'}</span></td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <button onClick={() => onEdit && onEdit(l)} className="text-zinc-400 hover:text-purple-400 p-2 transition-colors">
                        <Edit2 className="w-4 h-4" />
                      </button>
                      {canDelete && (
                        confirmandoId === l.id_lideranca ? (
                          <div className="flex items-center gap-1">
                            <button
                              onClick={() => {
                                setConfirmandoId(null);
                                if (onDelete) onDelete(l);
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
                          <button onClick={() => setConfirmandoId(l.id_lideranca)} className="text-zinc-400 hover:text-red-400 p-2 transition-colors">
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
        <span>{total} liderança{total === 1 ? '' : 's'} no total</span>
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
