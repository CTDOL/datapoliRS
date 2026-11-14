'use client';

import { useEffect, useState } from 'react';
import { Network, RefreshCw, AlertTriangle } from 'lucide-react';
import { balcaoService } from '../services/balcaoService';
import { extrairMensagemErroApi, type GrafoNo, type GrafoResposta } from '../types';

const CORES_POR_TIPO: Record<string, string> = {
  ATENDIDO: 'border-sky-300 bg-sky-50 text-sky-900',
  ATENDIMENTO: 'border-purple-300 bg-purple-50 text-purple-900',
  MUNICIPIO: 'border-emerald-300 bg-emerald-50 text-emerald-900',
};

export function BalcaoGrafoPanel() {
  const [grafo, setGrafo] = useState<GrafoResposta | null>(null);
  const [noSelecionado, setNoSelecionado] = useState<GrafoNo | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  const carregar = async () => {
    setCarregando(true);
    setErro(null);
    try {
      const dados = await balcaoService.obterGrafo();
      setGrafo(dados);
    } catch (err) {
      setErro(extrairMensagemErroApi(err, 'Não foi possível carregar o grafo de correlações.'));
    } finally {
      setCarregando(false);
    }
  };

  useEffect(() => {
    let cancelado = false;
    balcaoService
      .obterGrafo()
      .then((dados) => {
        if (!cancelado) setGrafo(dados);
      })
      .catch((err) => {
        if (!cancelado) {
          setErro(extrairMensagemErroApi(err, 'Não foi possível carregar o grafo de correlações.'));
        }
      })
      .finally(() => {
        if (!cancelado) setCarregando(false);
      });
    return () => {
      cancelado = true;
    };
  }, []);

  const conexoesDoNo =
    grafo && noSelecionado
      ? grafo.arestas.filter(
          (a) => a.origem === noSelecionado.id || a.destino === noSelecionado.id
        )
      : [];

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-sm text-zinc-300">
          <Network className="h-4 w-4 text-purple-400" />
          <span>
            {grafo
              ? `${grafo.nos.length} nós · ${grafo.arestas.length} conexões`
              : 'Grafo de correlações do gabinete'}
          </span>
        </div>
        <button
          type="button"
          onClick={carregar}
          disabled={carregando}
          className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-1.5 text-xs font-medium text-zinc-200 hover:bg-zinc-700"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${carregando ? 'animate-spin' : ''}`} />
          <span>Atualizar</span>
        </button>
      </div>

      {erro && (
        <div
          role="alert"
          className="flex items-center gap-2 rounded-xl border border-rose-300 bg-rose-50 p-3 text-sm text-rose-900"
        >
          <AlertTriangle className="h-4 w-4 text-rose-400" />
          <span>{erro}</span>
        </div>
      )}

      {!carregando && grafo && grafo.nos.length === 0 && (
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-8 text-center text-sm text-zinc-400">
          Nenhuma correlação registrada ainda. Efetive entradas do portal para gerar o grafo.
        </div>
      )}

      {grafo && grafo.nos.length > 0 && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <div className="lg:col-span-2 rounded-2xl border border-zinc-800 bg-zinc-900/60 p-4">
            <div className="flex flex-wrap gap-2">
              {grafo.nos.map((no) => (
                <button
                  key={no.id}
                  type="button"
                  onClick={() => setNoSelecionado(no)}
                  className={`rounded-xl border px-3 py-2 text-left text-xs transition ${
                    CORES_POR_TIPO[no.tipo] ?? 'border-zinc-700 bg-zinc-800 text-zinc-200'
                  } ${noSelecionado?.id === no.id ? 'ring-2 ring-white/50' : ''}`}
                >
                  <span className="block text-[10px] uppercase opacity-75">{no.tipo}</span>
                  <span className="font-semibold">{no.rotulo}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-4">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
              Conexões do Nó
            </h3>
            {!noSelecionado ? (
              <p className="mt-2 text-xs text-zinc-500">
                Selecione um nó ao lado para inspecionar suas relações.
              </p>
            ) : (
              <div className="mt-3 space-y-2">
                <p className="text-sm font-semibold text-white">{noSelecionado.rotulo}</p>
                <p className="text-xs text-zinc-400">Tipo: {noSelecionado.tipo}</p>
                <ul className="mt-2 space-y-1.5">
                  {conexoesDoNo.map((aresta, idx) => (
                    <li
                      key={`${aresta.origem}-${aresta.destino}-${idx}`}
                      className="rounded-lg border border-zinc-800 bg-zinc-950/70 px-2.5 py-1.5 text-xs text-zinc-300"
                    >
                      <span className="font-mono text-purple-300">{aresta.tipo}</span>:{' '}
                      {aresta.origem} → {aresta.destino}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

