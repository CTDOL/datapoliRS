import { useEffect, useRef, useState } from 'react';
import { api } from '@/services/api';
import type { LiderancaPoint } from '@/components/map/ElectionMap';

const DEBOUNCE_MS = 350;
// O mapa mostra todas as lideranças de uma vez, sem paginação na tela.
const LIMITE_NO_MAPA = 200;

/** Lideranças plotadas no Mapa Tático, com filtros de nome, município e tipo de influência. */
export function useLiderancasDoMapa() {
  const [liderancas, setLiderancas] = useState<LiderancaPoint[]>([]);
  const [filtroCidade, setFiltroCidade] = useState('');
  const [filtroTipo, setFiltroTipo] = useState('');
  const [filtroNome, setFiltroNome] = useState('');
  const [filtroNomeDebounced, setFiltroNomeDebounced] = useState('');
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // O nome tem debounce próprio (campo de texto); cidade e tipo são <select> e
  // disparam a busca na hora.
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setFiltroNomeDebounced(filtroNome);
    }, DEBOUNCE_MS);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [filtroNome]);

  useEffect(() => {
    let cancelado = false;
    api
      .get('/api/v1/gabinete/liderancas', {
        params: {
          page_size: LIMITE_NO_MAPA,
          cd_ibge_7: filtroCidade || undefined,
          tp_influencia: filtroTipo || undefined,
          termo: filtroNomeDebounced.trim() || undefined,
        },
      })
      .then((res) => {
        // Resposta de um filtro antigo que chega depois da atual não sobrescreve o mapa.
        if (!cancelado) setLiderancas(res.data.items);
      })
      .catch((err) => console.error('Erro ao buscar lideranças:', err));
    return () => {
      cancelado = true;
    };
  }, [filtroCidade, filtroTipo, filtroNomeDebounced]);

  return {
    liderancas,
    filtroNome,
    setFiltroNome,
    filtroCidade,
    setFiltroCidade,
    filtroTipo,
    setFiltroTipo,
  };
}
