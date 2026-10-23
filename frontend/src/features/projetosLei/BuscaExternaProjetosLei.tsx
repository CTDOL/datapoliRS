import { Loader2, Search, ExternalLink, Check, Plus, AlertTriangle } from 'lucide-react';
import { ProposicaoExterna } from './useProjetosLei';

const FONTE_LABEL: Record<string, string> = {
  ALRS: 'Assembleia Legislativa do RS (ALRS)',
  CAMARA: 'Câmara dos Deputados',
  SENADO: 'Senado Federal',
};

const FONTE_STYLES: Record<string, string> = {
  ALRS: 'bg-teal-500/10 text-teal-400 border-teal-500/20',
  CAMARA: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  SENADO: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
};

/** Explica a falha de uma fonte sem sugerir que o problema passa sozinho: a fonte pode estar fora do ar de vez. */
export function mensagemFontesComErro(fontesComErro: string[], temResultados: boolean): string {
  const nomes = fontesComErro.map((f) => FONTE_LABEL[f] || f).join(' e ');
  const verbo = fontesComErro.length > 1 ? 'não responderam' : 'não respondeu';
  if (temResultados) {
    return `${nomes} ${verbo}. A lista abaixo mostra só as fontes que responderam e pode estar incompleta.`;
  }
  return `${nomes} ${verbo}, então a busca não consultou essa fonte. Nenhum resultado não quer dizer que não existam projetos nela.`;
}

interface BuscaExternaProps {
  nomeBusca: string;
  onNomeBuscaChange: (nome: string) => void;
  resultados: ProposicaoExterna[];
  fontesComErro: string[];
  isBuscando: boolean;
  importandoChave: string | null;
  /** Ausente para quem só consulta: o botão de importar não aparece. */
  onImportar?: (proposicao: ProposicaoExterna) => void;
}

export function BuscaExternaProjetosLei({
  nomeBusca,
  onNomeBuscaChange,
  resultados,
  fontesComErro,
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

      {!isBuscando && fontesComErro.length > 0 && (
        <div
          role="alert"
          className="flex items-start gap-2 mt-4 px-3.5 py-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-sm"
        >
          <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
          <span>{mensagemFontesComErro(fontesComErro, resultados.length > 0)}</span>
        </div>
      )}

      {!isBuscando && nomeBusca.trim().length >= 3 && resultados.length === 0 && fontesComErro.length === 0 && (
        <p className="text-zinc-500 text-sm mt-4">Nenhuma proposição encontrada para esse nome nas fontes oficiais.</p>
      )}

      {resultados.length > 0 && (
        <p className="mt-4 text-xs text-zinc-400" aria-live="polite">
          {resultados.length} resultado(s) para <strong className="text-zinc-200">&laquo;{nomeBusca.trim()}&raquo;</strong>
        </p>
      )}

      {resultados.length > 0 && (
        <div className="mt-2 space-y-2 max-h-96 overflow-y-auto pr-1">
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
                  {r.ementa && <p className="text-xs text-zinc-300 leading-relaxed mt-1">{r.ementa}</p>}
                  <dl className="flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-zinc-500 mt-1.5">
                    {r.autor && <div><dt className="inline">Autor: </dt><dd className="inline text-zinc-300">{r.autor}</dd></div>}
                    {r.data_apresentacao && (
                      <div>
                        <dt className="inline">Apresentado em: </dt>
                        <dd className="inline text-zinc-300">{new Date(`${r.data_apresentacao}T00:00:00`).toLocaleDateString('pt-BR')}</dd>
                      </div>
                    )}
                  </dl>
                  {r.url_fonte && (
                    <a href={r.url_fonte} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-[11px] text-purple-400 hover:text-purple-300 mt-1">
                      Ver na fonte oficial <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
                {onImportar && (
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
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
