import { useState, useCallback, useEffect, useRef } from 'react';
import { api } from '@/services/api';

export interface ProposicaoExterna {
  fonte: string;
  identificador_externo: string;
  tipo?: string | null;
  numero?: string | null;
  ano?: number | null;
  ementa?: string | null;
  situacao?: string | null;
  autor?: string | null;
  url_fonte?: string | null;
  data_apresentacao?: string | null;
  ja_importado: boolean;
  id_projeto_lei?: string | null;
}

export interface ProjetoLei {
  id_projeto_lei: string;
  fonte: string;
  identificador_externo: string;
  tipo?: string | null;
  numero?: string | null;
  ano?: number | null;
  ementa: string;
  situacao?: string | null;
  autor?: string | null;
  url_fonte?: string | null;
  data_apresentacao?: string | null;
  created_at: string;
}

const PAGE_SIZE = 20;
const DEBOUNCE_MS = 400;

export function useProjetosLei() {
  const [nomeBusca, setNomeBusca] = useState('');
  const [resultadosExternos, setResultadosExternos] = useState<ProposicaoExterna[]>([]);
  const [isBuscando, setIsBuscando] = useState(false);
  const [importandoChave, setImportandoChave] = useState<string | null>(null);
  const buscaDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const [projetosLei, setProjetosLei] = useState<ProjetoLei[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [termo, setTermo] = useState('');
  const [fonte, setFonte] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const listaDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchProjetosLei = useCallback(async (paginaAlvo: number, filtros: { termo: string; fonte: string }) => {
    try {
      setIsLoading(true);
      const response = await api.get('/api/v1/gabinete/projetos-lei', {
        params: {
          page: paginaAlvo,
          page_size: PAGE_SIZE,
          termo: filtros.termo.trim() || undefined,
          fonte: filtros.fonte || undefined,
        },
      });
      setProjetosLei(response.data.items);
      setTotalPages(response.data.total_pages || 1);
      setTotal(response.data.total || 0);
    } catch (error) {
      console.error('Erro ao buscar projetos de lei', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (listaDebounceRef.current) clearTimeout(listaDebounceRef.current);
    listaDebounceRef.current = setTimeout(() => {
      setPage(1);
      fetchProjetosLei(1, { termo, fonte });
    }, DEBOUNCE_MS);
    return () => {
      if (listaDebounceRef.current) clearTimeout(listaDebounceRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [termo, fonte]);

  useEffect(() => {
    if (page === 1) return;
    const timer = setTimeout(() => fetchProjetosLei(page, { termo, fonte }), 0);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  const refetchProjetosLei = useCallback(
    () => fetchProjetosLei(page, { termo, fonte }),
    [fetchProjetosLei, page, termo, fonte]
  );

  // Busca externa (ALRS + Câmara + Senado) com debounce — só dispara com 3+ caracteres.
  useEffect(() => {
    if (buscaDebounceRef.current) clearTimeout(buscaDebounceRef.current);
    if (nomeBusca.trim().length < 3) {
      buscaDebounceRef.current = setTimeout(() => setResultadosExternos([]), 0);
      return () => {
        if (buscaDebounceRef.current) clearTimeout(buscaDebounceRef.current);
      };
    }
    buscaDebounceRef.current = setTimeout(async () => {
      setIsBuscando(true);
      try {
        const response = await api.get('/api/v1/gabinete/projetos-lei/buscar-externo', {
          params: { nome: nomeBusca.trim() },
        });
        setResultadosExternos(response.data);
      } catch (error) {
        console.error('Erro ao buscar proposições nas fontes oficiais', error);
        setResultadosExternos([]);
      } finally {
        setIsBuscando(false);
      }
    }, DEBOUNCE_MS);
    return () => {
      if (buscaDebounceRef.current) clearTimeout(buscaDebounceRef.current);
    };
  }, [nomeBusca]);

  const importar = async (proposicao: ProposicaoExterna) => {
    const chave = `${proposicao.fonte}:${proposicao.identificador_externo}`;
    setImportandoChave(chave);
    try {
      await api.post('/api/v1/gabinete/projetos-lei', {
        fonte: proposicao.fonte,
        identificador_externo: proposicao.identificador_externo,
        tipo: proposicao.tipo,
        numero: proposicao.numero,
        ano: proposicao.ano,
        autor: proposicao.autor,
      });
      setResultadosExternos((atual) =>
        atual.map((r) =>
          r.fonte === proposicao.fonte && r.identificador_externo === proposicao.identificador_externo
            ? { ...r, ja_importado: true }
            : r
        )
      );
      await refetchProjetosLei();
      return true;
    } catch (error) {
      console.error('Erro ao importar projeto de lei', error);
      return false;
    } finally {
      setImportandoChave(null);
    }
  };

  const deleteProjetoLei = async (id: string) => {
    try {
      await api.delete(`/api/v1/gabinete/projetos-lei/${id}`);
      await refetchProjetosLei();
      return true;
    } catch (error) {
      console.error('Erro ao excluir projeto de lei', error);
      return false;
    }
  };

  return {
    nomeBusca,
    setNomeBusca,
    resultadosExternos,
    isBuscando,
    importandoChave,
    importar,
    projetosLei,
    isLoading,
    termo,
    setTermo,
    fonte,
    setFonte,
    page,
    setPage,
    totalPages,
    total,
    deleteProjetoLei,
  };
}
