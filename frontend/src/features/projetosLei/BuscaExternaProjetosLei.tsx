import { Loader2, Search, ExternalLink, Check, Plus } from 'lucide-react';
import { ProposicaoExterna } from './useProjetosLei';

const FONTE_LABEL: Record<string, string> = {
  ALRS: 'Assembleia RS',
  CAMARA: 'Câmara dos Deputados',
  SENADO: 'Senado Federal',
};

const FONTE_STYLES: Record<string, string> = {
  ALRS: 'bg-teal-500/10 text-teal-400 border-teal-500/20',
  CAMARA: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  SENADO: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
};

interface BuscaExternaProps {
  nomeBusca: string;
  onNomeBuscaChange: (nome: string) => void;
  resultados: ProposicaoExterna[];
  isBuscando: boolean;
  importandoChave: string | null;
  onImportar: (proposicao: ProposicaoExterna) => void;
}

export function BuscaExternaProjetosLei({
  nomeBusca,
  onNomeBuscaChange,
  resultados,
  isBuscando,
  importandoChave,
  onImportar,
}: BuscaExternaProps) {
  return (
    <div className="bg-zinc-900/50 backdrop-blur-md border border-zinc-800 rounded-2xl p-5 shadow-xl">
      <h2 className="text-sm font-semibold text-white uppercase tracking-wide mb-3">Buscar nas fontes oficiais</h2>
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
        <input
          type="text"
          value={nomeBusca}
          onChange={(e) => onNomeBuscaChange(e.target.value)}
          placeholder="Nome do parlamentar (ex: Delegada Nadine)"
          className="w-full bg-zinc-950/60 border border-zinc-700/50 rounded-xl pl-9 pr-4 py-2.5 text-sm text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
        />
      </div>

      {isBuscando && (
        <div className="flex items-center gap-2 text-zinc-400 text-sm mt-4">
          <Loader2 className="w-4 h-4 animate-spin" />
          Consultando ALRS, Câmara e Senado...
        </div>
      )}

      {!isBuscando && nomeBusca.trim().length >= 3 && resultados.length === 0 && (
        <p className="text-zinc-500 text-sm mt-4">Nenhuma proposição encontrada para esse nome nas fontes oficiais.</p>
      )}

      {resultados.length > 0 && (
        <div className="mt-4 space-y-2 max-h-96 overflow-y-auto pr-1">
          {resultados.map((r) => {
            const chave = `${r.fonte}:${r.identificador_externo}`;
            const importando = importandoChave === chave;
            return (
              <div
                key={chave}
                className="flex items-start justify-between gap-4 bg-zinc-950/60 border border-zinc-800 rounded-xl p-3.5"
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${FONTE_STYLES[r.fonte] || 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20'}`}>
                      {FONTE_LABEL[r.fonte] || r.fonte}
                    </span>
                    <span className="text-sm font-medium text-white">{r.tipo} {r.numero}/{r.ano}</span>
                    {r.situacao && <span className="text-xs text-zinc-400">· {r.situacao}</span>}
                  </div>
                  {r.ementa && <p className="text-xs text-zinc-400 truncate" title={r.ementa}>{r.ementa}</p>}
                  {r.url_fonte && (
                    <a href={r.url_fonte} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-[11px] text-purple-400 hover:text-purple-300 mt-1">
                      Ver na fonte oficial <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
                <button
                  onClick={() => onImportar(r)}
                  disabled={r.ja_importado || importando}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold shrink-0 transition-colors ${
                    r.ja_importado
                      ? 'bg-teal-500/10 text-teal-400 border border-teal-500/20 cursor-default'
                      : 'bg-purple-600 hover:bg-purple-500 text-white disabled:opacity-60'
                  }`}
                >
                  {importando ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : r.ja_importado ? (
                    <Check className="w-3.5 h-3.5" />
                  ) : (
                    <Plus className="w-3.5 h-3.5" />
                  )}
                  {r.ja_importado ? 'Importado' : 'Importar'}
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
