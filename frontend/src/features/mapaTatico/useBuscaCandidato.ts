import { useEffect, useRef, useState } from 'react';
import { api } from '@/services/api';

export interface CandidatoBusca {
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

const DEBOUNCE_MS = 350;
const TERMO_MINIMO = 2;

/** Busca de candidato e distribuição dos votos dele por município (modos Votação e Cruzada). */
export function useBuscaCandidato() {
  const [termoBusca, setTermoBusca] = useState('');
  const [resultadosBusca, setResultadosBusca] = useState<CandidatoBusca[]>([]);
  const [candidatoSelecionado, setCandidatoSelecionado] = useState<CandidatoBusca | null>(null);
  const [votosPorMunicipio, setVotosPorMunicipio] = useState<Record<string, number>>({});
  const [isBuscando, setIsBuscando] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Só dispara a API depois de 350ms sem digitar
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (termoBusca.trim().length < TERMO_MINIMO) {
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
    }, DEBOUNCE_MS);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [termoBusca]);

  function alterarTermo(value: string) {
    setTermoBusca(value);
    // Limpa os resultados no próprio handler (não no efeito de debounce) para
    // não disparar setState síncrono dentro de um efeito.
    if (value.trim().length < TERMO_MINIMO) {
      setResultadosBusca([]);
    }
  }

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

  return {
    termoBusca,
    alterarTermo,
    resultadosBusca,
    isBuscando,
    candidatoSelecionado,
    selecionarCandidato,
    limparCandidato,
    votosPorMunicipio,
  };
}
