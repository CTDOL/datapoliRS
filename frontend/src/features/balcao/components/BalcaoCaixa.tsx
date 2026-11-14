'use client';

import { useState } from 'react';
import { Inbox, KeyRound, Network, AlertTriangle } from 'lucide-react';
import { usePermissoes } from '@/stores/usePermissoes';
import { useBalcaoCaixa, type FiltroStatus } from '../hooks/useBalcaoCaixa';
import { BalcaoGrafoPanel } from './BalcaoGrafoPanel';
import { PortaisAdminPanel } from './PortaisAdminPanel';
import { TriagemDetalhe } from './TriagemDetalhe';

type AbaBalcao = 'caixa' | 'grafo' | 'portais';

const FILTROS: Array<{ valor: FiltroStatus; rotulo: string }> = [
  { valor: 'PENDENTE', rotulo: 'Pendentes' },
  { valor: 'EFETIVADA', rotulo: 'Efetivadas' },
  { valor: 'DESCARTADA', rotulo: 'Descartadas' },
  { valor: 'TODAS', rotulo: 'Todas' },
];

export function BalcaoCaixa() {
  const [aba, setAba] = useState<AbaBalcao>('caixa');
  const { podeEscrever, podeExcluir } = usePermissoes();
  const {
    filtroStatus,
    setFiltroStatus,
    entradas,
    entradaSelecionada,
    efetivacaoRecente,
    timeline,
    carregandoLista,
    carregandoDetalhe,
    processandoAcao,
    erro,
    selecionarEntrada,
    analisar,
    efetivar,
    descartar,
    anexarAoAtendimento,
    resolverAtendimento,
  } = useBalcaoCaixa('PENDENTE');

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-2 border-b border-zinc-800 pb-3">
        <button
          type="button"
          onClick={() => setAba('caixa')}
          className={`inline-flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold transition ${
            aba === 'caixa'
              ? 'bg-purple-600 text-white'
              : 'border border-zinc-800 bg-zinc-900/60 text-zinc-300 hover:bg-zinc-800'
          }`}
        >
          <Inbox className="h-4 w-4" />
          <span>Caixa de Entrada</span>
        </button>

        <button
          type="button"
          onClick={() => setAba('grafo')}
          className={`inline-flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold transition ${
            aba === 'grafo'
              ? 'bg-purple-600 text-white'
              : 'border border-zinc-800 bg-zinc-900/60 text-zinc-300 hover:bg-zinc-800'
          }`}
        >
          <Network className="h-4 w-4" />
          <span>Grafo de Correlações</span>
        </button>

        {podeExcluir && (
          <button
            type="button"
            onClick={() => setAba('portais')}
            className={`inline-flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold transition ${
              aba === 'portais'
                ? 'bg-purple-600 text-white'
                : 'border border-zinc-800 bg-zinc-900/60 text-zinc-300 hover:bg-zinc-800'
            }`}
          >
            <KeyRound className="h-4 w-4" />
            <span>Portais Públicos</span>
          </button>
        )}
      </div>

      {erro && (
        <div
          role="alert"
          className="flex items-center gap-2 rounded-xl border border-rose-300 bg-rose-50 p-3 text-sm text-rose-900"
        >
          <AlertTriangle className="h-4 w-4 shrink-0 text-rose-600" />
          <span>{erro}</span>
        </div>
      )}

      {aba === 'caixa' && (
        <div className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {FILTROS.map((f) => (
              <button
                key={f.valor}
                type="button"
                onClick={() => setFiltroStatus(f.valor)}
                className={`rounded-lg px-3 py-1.5 text-xs font-medium transition ${
                  filtroStatus === f.valor
                    ? 'border border-purple-600 bg-purple-600 text-white'
                    : 'border border-zinc-300 bg-zinc-100 text-zinc-700 hover:bg-zinc-200'
                }`}
              >
                {f.rotulo}
              </button>
            ))}
          </div>

          <div className="grid grid-cols-1 gap-5 lg:grid-cols-12">
            <div className="space-y-2.5 lg:col-span-5">
              {carregandoLista ? (
                <p className="text-xs text-zinc-400">Carregando entradas...</p>
              ) : entradas.length === 0 ? (
                <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6 text-center text-xs text-zinc-400">
                  Nenhuma entrada encontrada para este filtro.
                </div>
              ) : (
                entradas.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => selecionarEntrada(item.id)}
                    className={`w-full rounded-xl border p-3.5 text-left transition ${
                      entradaSelecionada?.id === item.id
                        ? 'border-purple-500 bg-purple-500/10'
                        : 'border-zinc-800 bg-zinc-900/60 hover:border-zinc-700'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2 text-[11px] text-zinc-400">
                      <span className="font-semibold text-zinc-200">{item.status}</span>
                      <span>{new Date(item.criado_em).toLocaleDateString('pt-BR')}</span>
                    </div>
                    <p className="mt-1.5 line-clamp-2 text-xs text-zinc-300">
                      {item.texto_original || '(sem texto)'}
                    </p>
                  </button>
                ))
              )}
            </div>

            <div className="lg:col-span-7">
              {carregandoDetalhe ? (
                <p className="text-xs text-zinc-400">Carregando detalhes...</p>
              ) : entradaSelecionada ? (
                <TriagemDetalhe
                  key={entradaSelecionada.id}
                  entrada={entradaSelecionada}
                  efetivacaoRecente={efetivacaoRecente}
                  timeline={timeline}
                  podeEscrever={podeEscrever}
                  processando={processandoAcao}
                  onAnalisar={analisar}
                  onEfetivar={efetivar}
                  onDescartar={descartar}
                  onAnexar={anexarAoAtendimento}
                  onResolver={resolverAtendimento}
                />
              ) : (
                <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-8 text-center text-xs text-zinc-400">
                  Selecione uma entrada à esquerda para iniciar a triagem.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {aba === 'grafo' && <BalcaoGrafoPanel />}
      {aba === 'portais' && podeExcluir && <PortaisAdminPanel />}
    </div>
  );
}

