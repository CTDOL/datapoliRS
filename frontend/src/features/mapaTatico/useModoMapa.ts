import { useEffect, useState } from 'react';
import { api } from '@/services/api';
import type { MapViewMode } from '@/components/map/ElectionMap';
import { useAuthStore } from '@/stores/useAuthStore';

/** Modo de visualização do Mapa Tático e o ano do pleito ativo que rotula o modo Votação. */
export function useModoMapa() {
  // O modo padrão vem da preferência do usuário, carregada no login. Um clique no
  // seletor de modo vence a preferência até a próxima carga da tela.
  const mapaPadrao = useAuthStore((estado) => estado.user?.preferencias?.mapa_padrao);
  const [modoEscolhido, setModoEscolhido] = useState<MapViewMode | null>(null);
  const [anoAtivo, setAnoAtivo] = useState<number | null>(null);
  const viewMode: MapViewMode = modoEscolhido ?? mapaPadrao ?? 'liderancas';

  useEffect(() => {
    api
      .get<{ ano_eleicao: number }>('/api/v1/eleicao-ativa')
      .then((res) => setAnoAtivo(res.data.ano_eleicao))
      .catch(() => setAnoAtivo(null));
  }, []);

  return {
    viewMode,
    setViewMode: setModoEscolhido,
    anoAtivo,
    mostrarBuscaCandidato: viewMode === 'votacao' || viewMode === 'cruzada',
    mostrarFiltrosLideranca: viewMode === 'liderancas' || viewMode === 'cruzada',
  };
}
