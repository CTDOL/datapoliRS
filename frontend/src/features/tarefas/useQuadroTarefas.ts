import { useCallback, useEffect, useState } from 'react';
import { api } from '@/services/api';

export const STATUS_QUADRO = ['Pendente', 'Em Andamento', 'Concluída'] as const;
export type StatusTarefa = (typeof STATUS_QUADRO)[number];

export interface TarefaQuadro {
  id_tarefa: string;
  titulo: string;
  descricao?: string | null;
  prazo?: string | null;
  tp_status: StatusTarefa;
  id_projeto_lei?: string | null;
  id_emenda?: string | null;
  nm_lideranca_responsavel?: string | null;
}

export interface ComentarioTarefa {
  id_comentario: string;
  autor_email: string;
  texto: string;
  created_at: string;
}

export function useQuadroTarefas() {
  const [tarefas, setTarefas] = useState<TarefaQuadro[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  const buscar = useCallback(() => {
    return api.get<TarefaQuadro[]>('/api/v1/gabinete/tarefas')
      .then((res) => {
        setTarefas(res.data);
        setErro(null);
      })
      .catch(() => setErro('Não foi possível carregar as tarefas.'))
      .finally(() => setCarregando(false));
  }, []);

  useEffect(() => {
    buscar();
  }, [buscar]);

  const mover = async (tarefa: TarefaQuadro, novoStatus: StatusTarefa) => {
    setTarefas((atual) => atual.map((t) => (t.id_tarefa === tarefa.id_tarefa ? { ...t, tp_status: novoStatus } : t)));
    try {
      await api.put(`/api/v1/gabinete/tarefas/${tarefa.id_tarefa}`, { tp_status: novoStatus });
    } catch {
      setErro('Não foi possível mover a tarefa. Atualize a tela.');
      await buscar();
    }
  };

  const listarComentarios = (idTarefa: string) =>
    api.get<ComentarioTarefa[]>(`/api/v1/gabinete/tarefas/${idTarefa}/comentarios`).then((res) => res.data);

  const comentar = (idTarefa: string, texto: string) =>
    api.post<ComentarioTarefa>(`/api/v1/gabinete/tarefas/${idTarefa}/comentarios`, { texto }).then((res) => res.data);

  return { tarefas, carregando, erro, mover, listarComentarios, comentar };
}
