import { useState, useCallback, useEffect } from 'react';
import { api } from '@/services/api';

export interface Observador {
  id_lideranca: string;
  nm_completo: string;
}

export interface Tarefa {
  id_tarefa: string;
  id_projeto_lei?: string | null;
  id_emenda?: string | null;
  id_lideranca_responsavel?: string | null;
  nm_lideranca_responsavel?: string | null;
  titulo: string;
  descricao?: string | null;
  prazo?: string | null;
  tp_status: string;
  created_at: string;
}

export interface NovaTarefa {
  titulo: string;
  descricao?: string;
  prazo?: string;
  id_lideranca_responsavel?: string;
}

export function useProjetoLeiDetalhe(idProjetoLei: string | null) {
  const [observadores, setObservadores] = useState<Observador[]>([]);
  const [tarefas, setTarefas] = useState<Tarefa[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const carregar = useCallback(async () => {
    if (!idProjetoLei) return;
    setIsLoading(true);
    try {
      const [obsRes, tarefasRes] = await Promise.all([
        api.get(`/api/v1/gabinete/projetos-lei/${idProjetoLei}/observadores`),
        api.get('/api/v1/gabinete/tarefas', { params: { id_projeto_lei: idProjetoLei } }),
      ]);
      setObservadores(obsRes.data);
      setTarefas(tarefasRes.data);
    } catch (error) {
      console.error('Erro ao carregar detalhes do projeto de lei', error);
    } finally {
      setIsLoading(false);
    }
  }, [idProjetoLei]);

  useEffect(() => {
    const timer = setTimeout(() => carregar(), 0);
    return () => clearTimeout(timer);
  }, [carregar]);

  const addObservador = async (idLideranca: string) => {
    if (!idProjetoLei) return false;
    setIsSubmitting(true);
    try {
      const res = await api.post(`/api/v1/gabinete/projetos-lei/${idProjetoLei}/observadores`, { id_lideranca: idLideranca });
      setObservadores(res.data);
      return true;
    } catch (error) {
      console.error('Erro ao adicionar observador', error);
      return false;
    } finally {
      setIsSubmitting(false);
    }
  };

  const removeObservador = async (idLideranca: string) => {
    if (!idProjetoLei) return false;
    try {
      const res = await api.delete(`/api/v1/gabinete/projetos-lei/${idProjetoLei}/observadores/${idLideranca}`);
      setObservadores(res.data);
      return true;
    } catch (error) {
      console.error('Erro ao remover observador', error);
      return false;
    }
  };

  const createTarefa = async (dados: NovaTarefa) => {
    if (!idProjetoLei) return false;
    setIsSubmitting(true);
    try {
      await api.post('/api/v1/gabinete/tarefas', { ...dados, id_projeto_lei: idProjetoLei });
      await carregar();
      return true;
    } catch (error) {
      console.error('Erro ao criar tarefa', error);
      return false;
    } finally {
      setIsSubmitting(false);
    }
  };

  const updateTarefaStatus = async (idTarefa: string, tp_status: string) => {
    try {
      await api.put(`/api/v1/gabinete/tarefas/${idTarefa}`, { tp_status });
      await carregar();
      return true;
    } catch (error) {
      console.error('Erro ao atualizar tarefa', error);
      return false;
    }
  };

  const deleteTarefa = async (idTarefa: string) => {
    try {
      await api.delete(`/api/v1/gabinete/tarefas/${idTarefa}`);
      await carregar();
      return true;
    } catch (error) {
      console.error('Erro ao excluir tarefa', error);
      return false;
    }
  };

  return {
    observadores,
    tarefas,
    isLoading,
    isSubmitting,
    addObservador,
    removeObservador,
    createTarefa,
    updateTarefaStatus,
    deleteTarefa,
  };
}
