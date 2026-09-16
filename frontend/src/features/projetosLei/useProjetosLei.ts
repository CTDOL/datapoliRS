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
  // Quando a situação foi conferida pela última vez na fonte oficial.
  ultima_sincronizacao?: string | null;
}

export interface ProjetoLeiSyncResponse {
  projeto: ProjetoLei;
  situacao_anterior?: string | null;
  situacao_alterada: boolean;
}

export interface SyncFeedback {
  id_projeto_lei: string;
  tipo: 'inalterada' | 'alterada' | 'erro';
  mensagem: string;
}

// "hoje", "há 1 dia", "há 12 dias" — o gabinete precisa saber quão velha é a
// situação que está vendo, não a data exata.
export function descreverConferencia(iso?: string | null, agora: Date = new Date()): string {
  if (!iso) return 'nunca conferida';
  const dias = Math.floor((agora.getTime() - new Date(iso).getTime()) / 86_400_000);
  if (dias <= 0) return 'conferida hoje';
  if (dias === 1) return 'conferida há 1 dia';
  return `conferida há ${dias} dias`;
}

export interface BuscaExternaResponse {
  resultados: ProposicaoExterna[];
  // Fontes que não responderam nesta consulta (timeout/5xx). Lista de
  // resultados vazia só significa "nada encontrado" quando isto também está vazio.
  fontes_com_erro: string[];
}

export const FONTES_EXTERNAS = ['ALRS', 'CAMARA', 'SENADO'];

const PAGE_SIZE = 20;
const DEBOUNCE_MS = 400;

export function useProjetosLei() {
  const [nomeBusca, setNomeBusca] = useState('');
  const [resultadosExternos, setResultadosExternos] = useState<ProposicaoExterna[]>([]);
  const [fontesComErro, setFontesComErro] = useState<string[]>([]);
  const [isBuscando, setIsBuscando] = useState(false);
  const [importandoChave, setImportandoChave] = useState<string | null>(null);
  const buscaDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  // A ALRS pode levar 25s pra responder: a resposta de "nad" chegaria depois
  // da de "nadine" e sobrescreveria a lista — só a consulta mais recente vale.
  const buscaSequenciaRef = useRef(0);

  const [projetosLei, setProjetosLei] = useState<ProjetoLei[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [termo, setTermo] = useState('');
  const [fonte, setFonte] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const listaDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isFirstRender = useRef(true);

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
      return response.data;
    } catch (error) {
      console.error('Erro ao buscar projetos de lei', error);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      fetchProjetosLei(1, { termo, fonte });
      return;
    }
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
      buscaSequenciaRef.current += 1;
      buscaDebounceRef.current = setTimeout(() => {
        setResultadosExternos([]);
        setFontesComErro([]);
        setIsBuscando(false);
      }, 0);
      return () => {
        if (buscaDebounceRef.current) clearTimeout(buscaDebounceRef.current);
      };
    }
    buscaDebounceRef.current = setTimeout(async () => {
      const sequencia = ++buscaSequenciaRef.current;
      setIsBuscando(true);
      try {
        const response = await api.get<BuscaExternaResponse>('/api/v1/gabinete/projetos-lei/buscar-externo', {
          params: { nome: nomeBusca.trim() },
        });
        if (sequencia !== buscaSequenciaRef.current) return;
        setResultadosExternos(response.data.resultados);
        setFontesComErro(response.data.fontes_com_erro);
      } catch (error) {
        if (sequencia !== buscaSequenciaRef.current) return;
        console.error('Erro ao buscar proposições nas fontes oficiais', error);
        // A requisição inteira falhou (rede, 5xx, proxy): nenhuma fonte respondeu.
        setResultadosExternos([]);
        setFontesComErro(FONTES_EXTERNAS);
      } finally {
        if (sequencia === buscaSequenciaRef.current) setIsBuscando(false);
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

  const [sincronizandoId, setSincronizandoId] = useState<string | null>(null);
  const [syncFeedback, setSyncFeedback] = useState<SyncFeedback | null>(null);

  // Reconsulta a fonte oficial para UM projeto já importado. Só o registro
  // daquela linha é trocado — observadores, tarefas e a paginação ficam como estão.
  const sincronizar = async (id: string) => {
    setSincronizandoId(id);
    setSyncFeedback(null);
    try {
      const response = await api.post<ProjetoLeiSyncResponse>(`/api/v1/gabinete/projetos-lei/${id}/sincronizar`);
      const { projeto, situacao_alterada, situacao_anterior } = response.data;
      setProjetosLei((atual) => atual.map((pl) => (pl.id_projeto_lei === id ? projeto : pl)));
      setSyncFeedback({
        id_projeto_lei: id,
        tipo: situacao_alterada ? 'alterada' : 'inalterada',
        mensagem: situacao_alterada
          ? `Situação mudou: ${situacao_anterior || '—'} → ${projeto.situacao || '—'}`
          : 'Situação confirmada na fonte oficial',
      });
      return projeto;
    } catch (error: unknown) {
      const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setSyncFeedback({
        id_projeto_lei: id,
        tipo: 'erro',
        mensagem: detail || 'Fonte oficial não respondeu. A situação guardada foi mantida.',
      });
      console.error('Erro ao sincronizar projeto de lei', error);
      return null;
    } finally {
      setSincronizandoId(null);
    }
  };

  const deleteProjetoLei = async (id: string) => {
    try {
      await api.delete(`/api/v1/gabinete/projetos-lei/${id}`);
      const resultado = await fetchProjetosLei(page, { termo, fonte });
      if (resultado && resultado.items.length === 0 && page > 1) {
        const paginaAnterior = page - 1;
        setPage(paginaAnterior);
        await fetchProjetosLei(paginaAnterior, { termo, fonte });
      }
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
    fontesComErro,
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
    sincronizar,
    sincronizandoId,
    syncFeedback,
  };
}
