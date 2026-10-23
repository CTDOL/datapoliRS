import { useEffect, useState } from 'react';
import { api } from '@/services/api';
import type { MapViewMode } from '@/components/map/ElectionMap';
import { getMapaPadrao } from '@/utils/tacticalPreferences';

/** Modo de visualização do Mapa Tático e o ano do pleito ativo que rotula o modo Votação. */
export function useModoMapa() {
  const [viewMode, setViewMode] = useState<MapViewMode>('liderancas');
  const [anoAtivo, setAnoAtivo] = useState<number | null>(null);

  useEffect(() => {
    api
      .get<{ ano_eleicao: number }>('/api/v1/eleicao-ativa')
      .then((res) => setAnoAtivo(res.data.ano_eleicao))
      .catch(() => setAnoAtivo(null));
  }, []);

  // Lido em um efeito (não no useState inicial) para não divergir entre a
  // renderização do servidor (sem localStorage) e a hidratação no cliente.
  // Sem setTimeout: um clique do usuário no seletor de modo, entre o mount e
  // o timeout, era sobrescrito por este efeito restaurando o valor salvo.
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- hidratação única de preferência client-only (localStorage), sem equivalente no SSR
    setViewMode(getMapaPadrao());
  }, []);

  return {
    viewMode,
    setViewMode,
    anoAtivo,
    mostrarBuscaCandidato: viewMode === 'votacao' || viewMode === 'cruzada',
    mostrarFiltrosLideranca: viewMode === 'liderancas' || viewMode === 'cruzada',
  };
}
