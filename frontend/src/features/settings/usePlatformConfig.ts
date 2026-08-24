import { useState, useCallback, useEffect } from 'react';
import { api } from '@/services/api';

export interface ConfiguracaoItem {
  chave: string;
  valor: string;
  tipo: 'int' | 'string';
  categoria: 'eleitoral' | 'rate_limit' | 'cache';
  descricao: string;
  updated_at: string;
}

export function usePlatformConfig(isAdmin: boolean) {
  const [configuracoes, setConfiguracoes] = useState<ConfiguracaoItem[]>([]);
  const [isLoading, setIsLoading] = useState(isAdmin);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchConfiguracoes = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await api.get('/api/v1/admin/configuracoes');
      setConfiguracoes(response.data);
    } catch (error) {
      console.error('Erro ao buscar configurações da plataforma', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    setTimeout(() => {
      if (isAdmin) fetchConfiguracoes();
    }, 0);
  }, [isAdmin, fetchConfiguracoes]);

  const salvarConfiguracoes = useCallback(async (valores: Record<string, string>): Promise<{ ok: true } | { ok: false; message: string }> => {
    setIsSubmitting(true);
    try {
      const response = await api.put('/api/v1/admin/configuracoes', { valores });
      setConfiguracoes(response.data);
      return { ok: true };
    } catch (error: unknown) {
      const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      return { ok: false, message: detail || 'Não foi possível salvar as configurações.' };
    } finally {
      setIsSubmitting(false);
    }
  }, []);

  return { configuracoes, isLoading, isSubmitting, salvarConfiguracoes };
}
