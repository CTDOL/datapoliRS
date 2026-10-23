import { useEffect, useState } from 'react';
import { api } from '@/services/api';

export interface MunicipioItem {
  cd_ibge_7: string;
  nm_municipio: string;
}

// A lista dos municípios do RS não muda durante a sessão. Mapa Tático, tabela de
// lideranças e os formulários de liderança e emenda compartilham uma única
// requisição em vez de cada tela baixar a sua.
let cache: Promise<MunicipioItem[]> | null = null;

function carregarMunicipios(): Promise<MunicipioItem[]> {
  if (!cache) {
    cache = api
      .get<MunicipioItem[]>('/api/v1/geo/municipios/lista')
      .then((res) => res.data)
      .catch((err) => {
        cache = null; // falha não fica guardada: a próxima tela tenta de novo
        throw err;
      });
  }
  return cache;
}

/** Só para testes: esquece a lista carregada. */
export function limparCacheMunicipios() {
  cache = null;
}

/**
 * Lista de municípios para selects e filtros.
 * `ativo = false` adia a carga (ex.: formulário em modal ainda fechado).
 */
export function useMunicipios(ativo = true) {
  const [municipios, setMunicipios] = useState<MunicipioItem[]>([]);
  const [carregado, setCarregado] = useState(false);

  useEffect(() => {
    if (!ativo) return;
    let cancelado = false;
    carregarMunicipios()
      .then((lista) => {
        if (!cancelado) setMunicipios(lista);
      })
      .catch((err) => console.error('Erro ao carregar a lista de municípios:', err))
      .finally(() => {
        if (!cancelado) setCarregado(true);
      });
    return () => {
      cancelado = true;
    };
  }, [ativo]);

  return { municipios, isLoading: ativo && !carregado };
}
