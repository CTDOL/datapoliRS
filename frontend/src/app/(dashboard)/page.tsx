'use client';

import { useEffect, useRef, useState } from 'react';
import dynamic from 'next/dynamic';
import { api } from '@/services/api';
import { Map as MapIcon, Users, Vote, Layers, Search, X } from 'lucide-react';

const ElectionMap = dynamic(() => import('@/components/map/ElectionMap'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-[420px] sm:h-[600px] rounded-2xl border border-zinc-800 bg-zinc-950 flex items-center justify-center text-zinc-500">
      Carregando mapa tático...
    </div>
  ),
});

import { LiderancaPoint, MapViewMode } from '@/components/map/ElectionMap';
import { getMapaPadrao } from '@/utils/tacticalPreferences';

interface CandidatoBusca {
  sq_candidato: number;
  nr_candidato: number;
  nm_urna_candidato: string;
  sg_partido: string;
  ds_cargo: string;
}

interface MunicipioVotacaoItem {
  cd_ibge_7: string | null;
  votos: number;
}

interface MunicipioItem {
  cd_ibge_7: string;
  nm_municipio: string;
}

const TIPOS_INFLUENCIA = ['Comunitária', 'Religiosa', 'Empresarial', 'Política'];

const VIEW_MODES: { value: MapViewMode; label: string; icon: typeof MapIcon }[] = [
  { value: 'liderancas', label: 'Lideranças', icon: Users },
  { value: 'votacao', label: 'Votação', icon: Vote },
  { value: 'cruzada', label: 'Visão Cruzada', icon: Layers },
];

export default function DashboardPage() {
  const [liderancas, setLiderancas] = useState<LiderancaPoint[]>([]);
  const [viewMode, setViewMode] = useState<MapViewMode>('liderancas');

  // Lido em um efeito (não no useState inicial) para não divergir entre a
  // renderização do servidor (sem localStorage) e a hidratação no cliente.
  // Sem setTimeout: um clique do usuário no seletor de modo, entre o mount e
  // o timeout, era sobrescrito por este efeito restaurando o valor salvo.
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- hidratação única de preferência client-only (localStorage), sem equivalente no SSR
    setViewMode(getMapaPadrao());
  }, []);

  const [termoBusca, setTermoBusca] = useState('');
  const [resultadosBusca, setResultadosBusca] = useState<CandidatoBusca[]>([]);
  const [candidatoSelecionado, setCandidatoSelecionado] = useState<CandidatoBusca | null>(null);
  const [votosPorMunicipio, setVotosPorMunicipio] = useState<Record<string, number>>({});
  const [isBuscando, setIsBuscando] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const [filtroCidadeMapa, setFiltroCidadeMapa] = useState('');
  const [filtroTipoMapa, setFiltroTipoMapa] = useState('');
  const [filtroNomeLideranca, setFiltroNomeLideranca] = useState('');
  const [filtroNomeLiderancaDebounced, setFiltroNomeLiderancaDebounced] = useState('');
  const [municipiosParaFiltro, setMunicipiosParaFiltro] = useState<MunicipioItem[]>([]);
  const debounceNomeLiderancaRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    api.get('/api/v1/geo/municipios/lista').then((res) => setMunicipiosParaFiltro(res.data)).catch(() => {});
  }, []);

  // Filtro por nome da liderança tem seu próprio debounce (input de texto) —
  // cidade/tipo são <select>, disparam a busca na hora.
  useEffect(() => {
    if (debounceNomeLiderancaRef.current) clearTimeout(debounceNomeLiderancaRef.current);
    debounceNomeLiderancaRef.current = setTimeout(() => {
      setFiltroNomeLiderancaDebounced(filtroNomeLideranca);
    }, 350);
    return () => {
      if (debounceNomeLiderancaRef.current) clearTimeout(debounceNomeLiderancaRef.current);
    };
  }, [filtroNomeLideranca]);

  useEffect(() => {
    async function loadLiderancas() {
      try {
        const res = await api.get('/api/v1/gabinete/liderancas', {
          params: {
            page_size: 200,
            cd_ibge_7: filtroCidadeMapa || undefined,
            tp_influencia: filtroTipoMapa || undefined,
            termo: filtroNomeLiderancaDebounced.trim() || undefined,
          },
        });
        setLiderancas(res.data.items);
      } catch (err) {
        console.error('Erro ao buscar lideranças:', err);
      }
    }
    loadLiderancas();
  }, [filtroCidadeMapa, filtroTipoMapa, filtroNomeLiderancaDebounced]);

  // Busca de candidatos com debounce — só dispara a API depois de 350ms sem digitar
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (!termoBusca.trim() || termoBusca.trim().length < 2) {
      return;
    }

    debounceRef.current = setTimeout(async () => {
      setIsBuscando(true);
      try {
        const res = await api.get('/api/v1/candidatos', {
          params: { termo: termoBusca.trim(), limite: 8 },
        });
        setResultadosBusca(res.data);
      } catch (err) {
        console.error('Erro ao buscar candidatos:', err);
      } finally {
        setIsBuscando(false);
      }
    }, 350);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [termoBusca]);

  async function selecionarCandidato(candidato: CandidatoBusca) {
    setCandidatoSelecionado(candidato);
    setTermoBusca('');
    setResultadosBusca([]);
    try {
      const res = await api.get(`/api/v1/votacao/candidatos/${candidato.sq_candidato}/municipios`);
      const distribuicao: MunicipioVotacaoItem[] = res.data.distribuicao_municipios || [];
      const mapa: Record<string, number> = {};
      for (const item of distribuicao) {
        if (item.cd_ibge_7) mapa[item.cd_ibge_7] = item.votos;
      }
      setVotosPorMunicipio(mapa);
    } catch (err) {
      console.error('Erro ao buscar votação do candidato:', err);
      setVotosPorMunicipio({});
    }
  }

  function limparCandidato() {
    setCandidatoSelecionado(null);
    setVotosPorMunicipio({});
  }

  function handleTermoChange(value: string) {
    setTermoBusca(value);
    // Limpa os resultados no próprio handler (não no efeito de debounce) para
    // não disparar setState síncrono dentro de um efeito.
    if (value.trim().length < 2) {
      setResultadosBusca([]);
    }
  }

  const mostrarBuscaCandidato = viewMode === 'votacao' || viewMode === 'cruzada';
  const mostrarFiltrosLideranca = viewMode === 'liderancas' || viewMode === 'cruzada';

  return (
    <div className="w-full h-full p-4 sm:p-8 space-y-6 overflow-y-auto">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight">Mapa Tático</h1>
          <p className="text-zinc-400 text-sm">Geolocalização de lideranças e distribuição de votação eleitoral.</p>
        </div>

        {/* Seletor de modo de visualização — rola na horizontal quando não cabe */}
        <div className="flex max-w-full overflow-x-auto bg-zinc-900/60 backdrop-blur-md rounded-xl p-1 border border-zinc-700/50">
          {VIEW_MODES.map(({ value, label, icon: Icon }) => (
            <button
              key={value}
              onClick={() => setViewMode(value)}
              className={`flex shrink-0 items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold whitespace-nowrap transition-all ${
                viewMode === value
                  ? 'bg-purple-600 text-white shadow-md shadow-purple-500/20'
                  : 'text-zinc-400 hover:text-white hover:bg-zinc-800'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Sempre renderizado (posição estável na árvore) para o ElectionMap logo
          abaixo nunca ser desmontado/remontado por reconciliação de posição —
          um `{cond && <div>}` antes dele empurraria seu índice de filho e
          faria o React recriar o mapa do zero, perdendo a camada coroplética. */}
      <div className={mostrarBuscaCandidato ? 'relative max-w-md' : 'hidden'}>
        {mostrarBuscaCandidato && (
          <>
          {candidatoSelecionado ? (
            <div className="flex items-center justify-between bg-zinc-900/60 border border-purple-500/30 rounded-xl px-4 py-2.5">
              <div>
                <p className="text-sm font-semibold text-white">{candidatoSelecionado.nm_urna_candidato}</p>
                <p className="text-xs text-zinc-400">
                  {candidatoSelecionado.sg_partido} · Nº {candidatoSelecionado.nr_candidato} · {candidatoSelecionado.ds_cargo}
                </p>
              </div>
              <button onClick={limparCandidato} className="text-zinc-400 hover:text-white p-1">
                <X className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                <input
                  type="text"
                  value={termoBusca}
                  onChange={(e) => handleTermoChange(e.target.value)}
                  placeholder="Buscar candidato para ver a votação no mapa..."
                  className="w-full bg-zinc-900/60 border border-zinc-700/50 rounded-xl pl-9 pr-4 py-2.5 text-sm text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                />
              </div>
              {(resultadosBusca.length > 0 || isBuscando) && (
                <div className="absolute z-[1100] mt-1 w-full bg-zinc-900 border border-zinc-700/50 rounded-xl shadow-2xl overflow-hidden max-h-64 overflow-y-auto">
                  {isBuscando && (
                    <p className="px-4 py-3 text-xs text-zinc-500">Buscando...</p>
                  )}
                  {resultadosBusca.map((candidato) => (
                    <button
                      key={candidato.sq_candidato}
                      onClick={() => selecionarCandidato(candidato)}
                      className="w-full text-left px-4 py-2.5 hover:bg-zinc-800 transition-colors border-b border-zinc-800/50 last:border-0"
                    >
                      <p className="text-sm text-white">{candidato.nm_urna_candidato}</p>
                      <p className="text-xs text-zinc-400">
                        {candidato.sg_partido} · Nº {candidato.nr_candidato} · {candidato.ds_cargo}
                      </p>
                    </button>
                  ))}
                </div>
              )}
            </>
          )}
          </>
        )}
      </div>

      <div className={mostrarFiltrosLideranca ? 'flex flex-wrap gap-3' : 'hidden'}>
        {mostrarFiltrosLideranca && (
          <>
            <div className="relative w-full sm:w-56">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-zinc-500" />
              <input
                type="text"
                value={filtroNomeLideranca}
                onChange={(e) => setFiltroNomeLideranca(e.target.value)}
                placeholder="Buscar liderança por nome..."
                className="w-full bg-zinc-900/60 border border-zinc-700/50 rounded-xl pl-8 pr-3 py-2 text-sm text-white placeholder-zinc-500 outline-none focus:ring-2 focus:ring-purple-500/50"
              />
            </div>
            <select
              value={filtroCidadeMapa}
              onChange={(e) => setFiltroCidadeMapa(e.target.value)}
              className="w-full sm:w-auto sm:flex-1 sm:min-w-[12rem] sm:max-w-xs bg-zinc-900/60 border border-zinc-700/50 rounded-xl px-3 py-2 text-sm text-white outline-none focus:ring-2 focus:ring-purple-500/50 appearance-none"
            >
              <option value="">Todos os municípios</option>
              {municipiosParaFiltro.map((m) => (
                <option key={m.cd_ibge_7} value={m.cd_ibge_7}>{m.nm_municipio}</option>
              ))}
            </select>
            <select
              value={filtroTipoMapa}
              onChange={(e) => setFiltroTipoMapa(e.target.value)}
              className="w-full sm:w-auto sm:min-w-[10rem] bg-zinc-900/60 border border-zinc-700/50 rounded-xl px-3 py-2 text-sm text-white outline-none focus:ring-2 focus:ring-purple-500/50 appearance-none"
            >
              <option value="">Todos os tipos</option>
              {TIPOS_INFLUENCIA.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </>
        )}
      </div>

      <ElectionMap
        liderancas={liderancas}
        viewMode={viewMode}
        votosPorMunicipio={votosPorMunicipio}
      />
    </div>
  );
}
