'use client';

import { useCallback, useEffect, useState } from 'react';
import { balcaoService } from '../services/balcaoService';
import {
  extrairMensagemErroApi,
  type DescartarRequest,
  type EfetivarRequest,
  type EfetivarResponse,
  type EntradaDetalhe,
  type EntradaResumo,
  type EventoTimeline,
  type ResolverRequest,
  type ResolverResponse,
  type StatusEntrada,
} from '../types';

export type FiltroStatus = StatusEntrada | 'TODAS';

export function useBalcaoCaixa(statusInicial: FiltroStatus = 'PENDENTE') {
  const [filtroStatus, setFiltroStatus] = useState<FiltroStatus>(statusInicial);
  const [entradas, setEntradas] = useState<EntradaResumo[]>([]);
  const [entradaSelecionada, setEntradaSelecionada] = useState<EntradaDetalhe | null>(null);
  const [efetivacaoRecente, setEfetivacaoRecente] = useState<EfetivarResponse | null>(null);
  const [timeline, setTimeline] = useState<EventoTimeline[]>([]);
  const [carregandoLista, setCarregandoLista] = useState(true);
  const [carregandoDetalhe, setCarregandoDetalhe] = useState(false);
  const [processandoAcao, setProcessandoAcao] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  const carregarLista = useCallback(async (status: FiltroStatus) => {
    setCarregandoLista(true);
    setErro(null);
    try {
      const dados = await balcaoService.listarEntradas(status === 'TODAS' ? undefined : status);
      setEntradas(dados);
    } catch (err) {
      setErro(extrairMensagemErroApi(err, 'Não foi possível carregar a caixa de entrada.'));
    } finally {
      setCarregandoLista(false);
    }
  }, []);

  useEffect(() => {
    let cancelado = false;
    balcaoService
      .listarEntradas(filtroStatus === 'TODAS' ? undefined : filtroStatus)
      .then((dados) => {
        if (!cancelado) {
          setEntradas(dados);
          setErro(null);
        }
      })
      .catch((err) => {
        if (!cancelado) {
          setErro(extrairMensagemErroApi(err, 'Não foi possível carregar a caixa de entrada.'));
        }
      })
      .finally(() => {
        if (!cancelado) setCarregandoLista(false);
      });
    return () => {
      cancelado = true;
    };
  }, [filtroStatus]);

  const alterarFiltroStatus = useCallback((novoStatus: FiltroStatus) => {
    setCarregandoLista(true);
    setFiltroStatus(novoStatus);
  }, []);

  const selecionarEntrada = useCallback(async (idEntrada: string) => {
    setCarregandoDetalhe(true);
    setErro(null);
    setEfetivacaoRecente(null);
    setTimeline([]);
    try {
      const detalhe = await balcaoService.obterEntrada(idEntrada);
      setEntradaSelecionada(detalhe);
    } catch (err) {
      setErro(extrairMensagemErroApi(err, 'Não foi possível carregar os detalhes da entrada.'));
    } finally {
      setCarregandoDetalhe(false);
    }
  }, []);

  const carregarTimeline = useCallback(async (idAtendido: string) => {
    try {
      const eventos = await balcaoService.obterTimelineAtendido(idAtendido);
      setTimeline(eventos);
    } catch (err) {
      setErro(extrairMensagemErroApi(err, 'Não foi possível carregar a timeline do atendido.'));
    }
  }, []);

  const efetivar = useCallback(
    async (idEntrada: string, payload: EfetivarRequest): Promise<EfetivarResponse | null> => {
      setProcessandoAcao(true);
      setErro(null);
      try {
        const res = await balcaoService.efetivarEntrada(idEntrada, payload);
        setEfetivacaoRecente(res);
        await Promise.all([
          carregarLista(filtroStatus),
          carregarTimeline(res.atendido_id),
        ]);
        const detalheAtualizado = await balcaoService.obterEntrada(idEntrada);
        setEntradaSelecionada(detalheAtualizado);
        return res;
      } catch (err) {
        setErro(extrairMensagemErroApi(err, 'Não foi possível efetivar a entrada.'));
        return null;
      } finally {
        setProcessandoAcao(false);
      }
    },
    [filtroStatus, carregarLista, carregarTimeline]
  );

  const descartar = useCallback(
    async (idEntrada: string, payload: DescartarRequest): Promise<boolean> => {
      setProcessandoAcao(true);
      setErro(null);
      try {
        await balcaoService.descartarEntrada(idEntrada, payload);
        await carregarLista(filtroStatus);
        const detalheAtualizado = await balcaoService.obterEntrada(idEntrada);
        setEntradaSelecionada(detalheAtualizado);
        return true;
      } catch (err) {
        setErro(extrairMensagemErroApi(err, 'Não foi possível descartar a entrada.'));
        return false;
      } finally {
        setProcessandoAcao(false);
      }
    },
    [filtroStatus, carregarLista]
  );

  const anexarAoAtendimento = useCallback(
    async (idAtendimento: string, arquivo: File) => {
      setProcessandoAcao(true);
      setErro(null);
      try {
        return await balcaoService.anexarAoAtendimento(idAtendimento, arquivo);
      } catch (err) {
        setErro(extrairMensagemErroApi(err, 'Não foi possível enviar o anexo de evidência.'));
        return null;
      } finally {
        setProcessandoAcao(false);
      }
    },
    []
  );

  const resolverAtendimento = useCallback(
    async (
      idAtendimento: string,
      idAtendido: string,
      payload: ResolverRequest
    ): Promise<ResolverResponse | null> => {
      setProcessandoAcao(true);
      setErro(null);
      try {
        const res = await balcaoService.resolverAtendimento(idAtendimento, payload);
        await carregarTimeline(idAtendido);
        return res;
      } catch (err) {
        setErro(extrairMensagemErroApi(err, 'Não foi possível resolver o atendimento.'));
        return null;
      } finally {
        setProcessandoAcao(false);
      }
    },
    [carregarTimeline]
  );

  const analisar = useCallback(async (idEntrada: string): Promise<EntradaDetalhe | null> => {
    setProcessandoAcao(true);
    setErro(null);
    try {
      const atualizada = await balcaoService.analisarEntrada(idEntrada);
      setEntradaSelecionada(atualizada);
      return atualizada;
    } catch (err) {
      setErro(extrairMensagemErroApi(err, 'Não foi possível analisar a entrada.'));
      return null;
    } finally {
      setProcessandoAcao(false);
    }
  }, []);

  return {
    filtroStatus,
    setFiltroStatus: alterarFiltroStatus,
    entradas,
    entradaSelecionada,
    efetivacaoRecente,
    timeline,
    carregandoLista,
    carregandoDetalhe,
    processandoAcao,
    erro,
    setErro,
    recarregar: () => carregarLista(filtroStatus),
    selecionarEntrada,
    carregarTimeline,
    analisar,
    efetivar,
    descartar,
    anexarAoAtendimento,
    resolverAtendimento,
  };
}

