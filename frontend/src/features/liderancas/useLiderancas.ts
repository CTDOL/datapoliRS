import { useState, useCallback, useEffect, useRef } from 'react';
import { api } from '@/services/api';

export interface MunicipioAtuacao {
  cd_ibge_7: string;
  nm_municipio?: string;
  latitude?: number;
  longitude?: number;
}

export interface Lideranca {
  id_lideranca: string;
  nm_completo: string;
  nr_telefone: string;
  municipios: MunicipioAtuacao[];
  tp_influencia: string;
  ds_foto_url?: string | null;
  is_ativo: boolean;
}

/** Payload de criação/edição: municípios como lista de códigos IBGE (não o objeto resolvido da resposta). */
export type FormDataLideranca = {
  nm_completo: string;
  nr_telefone: string;
  tp_influencia: string;
  municipios: string[];
};

const PAGE_SIZE = 20;
const DEBOUNCE_MS = 350;

export function useLiderancas() {
  const [liderancas, setLiderancas] = useState<Lideranca[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [termo, setTermo] = useState('');
  const [filtroCidade, setFiltroCidade] = useState('');
  const [filtroTipo, setFiltroTipo] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isFirstRender = useRef(true);

  const fetchLiderancas = useCallback(
    async (paginaAlvo: number, termoAlvo: string, cidadeAlvo: string, tipoAlvo: string) => {
      try {
        setIsLoading(true);
        const response = await api.get('/api/v1/gabinete/liderancas', {
          params: {
            page: paginaAlvo,
            page_size: PAGE_SIZE,
            termo: termoAlvo.trim() || undefined,
            cd_ibge_7: cidadeAlvo || undefined,
            tp_influencia: tipoAlvo || undefined,
          },
        });
        setLiderancas(response.data.items);
        setTotalPages(response.data.total_pages || 1);
        setTotal(response.data.total || 0);
        return response.data;
      } catch (error) {
        console.error('Erro ao buscar lideranças', error);
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  // Primeira carga dispara na hora; mudanças de termo/filtros depois disso usam debounce.
  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      fetchLiderancas(1, termo, filtroCidade, filtroTipo);
      return;
    }
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setPage(1);
      fetchLiderancas(1, termo, filtroCidade, filtroTipo);
    }, DEBOUNCE_MS);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [termo, filtroCidade, filtroTipo]);

  useEffect(() => {
    if (page === 1) return; // já coberto pelo efeito de busca acima
    const timer = setTimeout(() => fetchLiderancas(page, termo, filtroCidade, filtroTipo), 0);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  const refetch = useCallback(
    () => fetchLiderancas(page, termo, filtroCidade, filtroTipo),
    [fetchLiderancas, page, termo, filtroCidade, filtroTipo]
  );

  /** Retorna o id_lideranca em caso de sucesso (para permitir upload de foto em seguida), ou null em caso de falha. */
  const addLideranca = async (data: FormDataLideranca): Promise<string | null> => {
    setIsSubmitting(true);
    try {
      const response = await api.post('/api/v1/gabinete/liderancas', { ...data, is_ativo: true });
      await refetch();
      return response.data.id_lideranca as string;
    } catch (error) {
      console.error('Erro ao criar liderança', error);
      return null;
    } finally {
      setIsSubmitting(false);
    }
  };

  const updateLideranca = async (id: string, data: FormDataLideranca): Promise<string | null> => {
    setIsSubmitting(true);
    try {
      await api.put(`/api/v1/gabinete/liderancas/${id}`, data);
      await refetch();
      return id;
    } catch (error) {
      console.error('Erro ao atualizar liderança', error);
      return null;
    } finally {
      setIsSubmitting(false);
    }
  };

  const uploadFoto = async (id: string, arquivo: File) => {
    setIsSubmitting(true);
    try {
      // Sem Content-Type manual: o navegador precisa gerar o boundary do
      // multipart sozinho ao ver um FormData — fixar o header aqui quebraria o parse no backend.
      const formData = new FormData();
      formData.append('arquivo', arquivo);
      await api.post(`/api/v1/gabinete/liderancas/${id}/foto`, formData);
      await refetch();
      return true;
    } catch (error) {
      console.error('Erro ao enviar foto da liderança', error);
      return false;
    } finally {
      setIsSubmitting(false);
    }
  };

  const deleteLideranca = async (id: string) => {
    setIsSubmitting(true);
    try {
      await api.delete(`/api/v1/gabinete/liderancas/${id}`);
      const resultado = await fetchLiderancas(page, termo, filtroCidade, filtroTipo);
      if (resultado && resultado.items.length === 0 && page > 1) {
        const paginaAnterior = page - 1;
        setPage(paginaAnterior);
        await fetchLiderancas(paginaAnterior, termo, filtroCidade, filtroTipo);
      }
      return true;
    } catch (error) {
      console.error('Erro ao excluir liderança', error);
      return false;
    } finally {
      setIsSubmitting(false);
    }
  };

  return {
    liderancas,
    isLoading,
    isSubmitting,
    termo,
    setTermo,
    filtroCidade,
    setFiltroCidade,
    filtroTipo,
    setFiltroTipo,
    page,
    setPage,
    totalPages,
    total,
    addLideranca,
    updateLideranca,
    uploadFoto,
    deleteLideranca,
  };
}
