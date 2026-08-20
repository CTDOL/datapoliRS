import { useState, useCallback, useEffect } from 'react';
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

export function useLiderancas() {
  const [liderancas, setLiderancas] = useState<Lideranca[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchLiderancas = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await api.get('/api/v1/gabinete/liderancas');
      setLiderancas(response.data);
    } catch (error) {
      console.error('Erro ao buscar lideranças', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    const initFetch = async () => {
      await fetchLiderancas();
    };
    initFetch();
  }, [fetchLiderancas]);

  const addLideranca = async (data: FormDataLideranca) => {
    setIsSubmitting(true);
    try {
      await api.post('/api/v1/gabinete/liderancas', { ...data, is_ativo: true });
      await fetchLiderancas(); // Re-fetch na mesma instância
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
      await fetchLiderancas(); // Re-fetch
      return true;
    } catch (error) {
      console.error('Erro ao atualizar liderança', error);
      return false;
    } finally {
      setIsSubmitting(false);
    }
  };

  return { liderancas, isLoading, isSubmitting, addLideranca, updateLideranca };
}
