import { Loader2, Edit2 } from 'lucide-react';
import { Lideranca } from './useLiderancas';

export function LiderancasTable({ liderancas, isLoading, onEdit }: { liderancas: Lideranca[], isLoading: boolean, onEdit?: (lideranca: Lideranca) => void }) {
  return (
    <div className="flex-1 bg-zinc-900/50 backdrop-blur-md border border-zinc-800 rounded-2xl overflow-hidden flex flex-col shadow-2xl">
      <div className="overflow-x-auto">
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
              <tr><td colSpan={5} className="px-6 py-12 text-center"><Loader2 className="w-8 h-8 text-purple-500 animate-spin mx-auto mb-4" /><p className="text-zinc-400">Carregando...</p></td></tr>
            ) : liderancas.length === 0 ? (
              <tr><td colSpan={5} className="px-6 py-12 text-center text-zinc-400">Nenhuma liderança cadastrada.</td></tr>
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
                    <button onClick={() => onEdit && onEdit(l)} className="text-zinc-400 hover:text-purple-400 p-2 transition-colors">
                      <Edit2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
