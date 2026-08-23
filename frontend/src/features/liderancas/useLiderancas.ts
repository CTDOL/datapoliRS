import { useState, useCallback, useEffect, useRef } from 'react';
import { api } from '@/services/api';

export interface Lideranca {
  id_lideranca: string;
  nm_completo: string;
  nr_telefone: string;
  nm_municipio?: string;
  cd_ibge_7?: string;
  tp_influencia: string;
  is_ativo: boolean;
}

export type FormDataLideranca = Omit<Lideranca, 'id_lideranca' | 'is_ativo'>;

const PAGE_SIZE = 20;
const DEBOUNCE_MS = 350;

export function useLiderancas() {
  const [liderancas, setLiderancas] = useState<Lideranca[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [termo, setTermo] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchLiderancas = useCallback(async (paginaAlvo: number, termoAlvo: string) => {
    try {
      setIsLoading(true);
      const response = await api.get('/api/v1/gabinete/liderancas', {
        params: { page: paginaAlvo, page_size: PAGE_SIZE, termo: termoAlvo.trim() || undefined },
      });
      setLiderancas(response.data.items);
      setTotalPages(response.data.total_pages || 1);
      setTotal(response.data.total || 0);
    } catch (error) {
      console.error('Erro ao buscar lideranças', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Busca com debounce: volta pra página 1 a cada mudança de termo.
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setPage(1);
      fetchLiderancas(1, termo);
    }, DEBOUNCE_MS);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [termo]);

  useEffect(() => {
    if (page === 1) return; // já coberto pelo efeito de busca acima
    const timer = setTimeout(() => fetchLiderancas(page, termo), 0);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  const refetch = useCallback(() => fetchLiderancas(page, termo), [fetchLiderancas, page, termo]);

  const addLideranca = async (data: FormDataLideranca) => {
    setIsSubmitting(true);
    try {
      await api.post('/api/v1/gabinete/liderancas', { ...data, is_ativo: true });
      await refetch();
      return true;
    } catch (error) {
      console.error('Erro ao criar liderança', error);
      return false;
    } finally {
      setIsSubmitting(false);
    }
  };

  const updateLideranca = async (id: string, data: FormDataLideranca) => {
    setIsSubmitting(true);
    try {
      await api.put(`/api/v1/gabinete/liderancas/${id}`, data);
      await refetch();
      return true;
    } catch (error) {
      console.error('Erro ao atualizar liderança', error);
      return false;
    } finally {
      setIsSubmitting(false);
    }
  };

  const deleteLideranca = async (id: string) => {
    setIsSubmitting(true);
    try {
      await api.delete(`/api/v1/gabinete/liderancas/${id}`);
      await refetch();
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
    page,
    setPage,
    totalPages,
    total,
    addLideranca,
    updateLideranca,
    deleteLideranca,
  };
}
