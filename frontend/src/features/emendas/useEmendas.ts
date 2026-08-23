import { useState, useCallback, useEffect, useRef } from 'react';
import { api } from '@/services/api';

export interface Emenda {
  id_emenda: string;
  cd_ibge_7?: string | null;
  nm_municipio?: string | null;
  nr_emenda?: string | null;
  ano_exercicio: number;
  tp_emenda?: string | null;
  ds_area?: string | null;
  ds_objeto: string;
  vl_indicado: string;
  vl_empenhado: string;
  vl_pago: string;
  tp_situacao: string;
  ds_observacoes?: string | null;
}

export interface EmendaKpis {
  total_emendas: number;
  vl_total_indicado: string;
  vl_total_empenhado: string;
  vl_total_pago: string;
  por_situacao: Record<string, number>;
}

export type FormDataEmenda = Omit<Emenda, 'id_emenda' | 'nm_municipio'>;

const PAGE_SIZE = 20;
const DEBOUNCE_MS = 350;

export function useEmendas() {
  const [emendas, setEmendas] = useState<Emenda[]>([]);
  const [kpis, setKpis] = useState<EmendaKpis | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [termo, setTermo] = useState('');
  const [anoExercicio, setAnoExercicio] = useState<number | ''>('');
  const [tpSituacao, setTpSituacao] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isFirstRender = useRef(true);

  const fetchKpis = useCallback(async (ano: number | '') => {
    try {
      const response = await api.get('/api/v1/gabinete/emendas/kpis', {
        params: { ano_exercicio: ano || undefined },
      });
      setKpis(response.data);
    } catch (error) {
      console.error('Erro ao buscar KPIs de emendas', error);
    }
  }, []);

  const fetchEmendas = useCallback(async (paginaAlvo: number, filtros: { termo: string; ano: number | ''; situacao: string }) => {
    try {
      setIsLoading(true);
      const response = await api.get('/api/v1/gabinete/emendas', {
        params: {
          page: paginaAlvo,
          page_size: PAGE_SIZE,
          termo: filtros.termo.trim() || undefined,
          ano_exercicio: filtros.ano || undefined,
          tp_situacao: filtros.situacao || undefined,
        },
      });
      setEmendas(response.data.items);
      setTotalPages(response.data.total_pages || 1);
      setTotal(response.data.total || 0);
      return response.data;
    } catch (error) {
      console.error('Erro ao buscar emendas', error);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Primeira carga dispara na hora; mudanças de filtro depois disso usam debounce.
  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      fetchEmendas(1, { termo, ano: anoExercicio, situacao: tpSituacao });
      fetchKpis(anoExercicio);
      return;
    }
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setPage(1);
      fetchEmendas(1, { termo, ano: anoExercicio, situacao: tpSituacao });
      fetchKpis(anoExercicio);
    }, DEBOUNCE_MS);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [termo, anoExercicio, tpSituacao]);

  useEffect(() => {
    if (page === 1) return; // já coberto pelo efeito de filtros acima
    const timer = setTimeout(() => fetchEmendas(page, { termo, ano: anoExercicio, situacao: tpSituacao }), 0);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  const refetch = useCallback(() => {
    fetchEmendas(page, { termo, ano: anoExercicio, situacao: tpSituacao });
    fetchKpis(anoExercicio);
  }, [fetchEmendas, fetchKpis, page, termo, anoExercicio, tpSituacao]);

  const addEmenda = async (data: FormDataEmenda) => {
    setIsSubmitting(true);
    try {
      await api.post('/api/v1/gabinete/emendas', data);
      await refetch();
      return true;
    } catch (error) {
      console.error('Erro ao criar emenda', error);
      return false;
    } finally {
      setIsSubmitting(false);
    }
  };

  const updateEmenda = async (id: string, data: FormDataEmenda) => {
    setIsSubmitting(true);
    try {
      await api.put(`/api/v1/gabinete/emendas/${id}`, data);
      await refetch();
      return true;
    } catch (error) {
      console.error('Erro ao atualizar emenda', error);
      return false;
    } finally {
      setIsSubmitting(false);
    }
  };

  const deleteEmenda = async (id: string) => {
    setIsSubmitting(true);
    try {
      await api.delete(`/api/v1/gabinete/emendas/${id}`);
      const resultado = await fetchEmendas(page, { termo, ano: anoExercicio, situacao: tpSituacao });
      if (resultado && resultado.items.length === 0 && page > 1) {
        const paginaAnterior = page - 1;
        setPage(paginaAnterior);
        await fetchEmendas(paginaAnterior, { termo, ano: anoExercicio, situacao: tpSituacao });
      }
      await fetchKpis(anoExercicio);
      return true;
    } catch (error) {
      console.error('Erro ao excluir emenda', error);
      return false;
    } finally {
      setIsSubmitting(false);
    }
  };

  return {
    emendas,
    kpis,
    isLoading,
    isSubmitting,
    termo,
    setTermo,
    anoExercicio,
    setAnoExercicio,
    tpSituacao,
    setTpSituacao,
    page,
    setPage,
    totalPages,
    total,
    addEmenda,
    updateEmenda,
    deleteEmenda,
  };
}
