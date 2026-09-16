import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useProjetosLei, FONTES_EXTERNAS, descreverConferencia } from './useProjetosLei';
import { api } from '@/services/api';
import type { AxiosRequestConfig } from 'axios';

vi.mock('@/services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

const mockedGet = vi.mocked(api.get);
const BUSCAR_EXTERNO = '/api/v1/gabinete/projetos-lei/buscar-externo';
const LISTA_VAZIA = { data: { items: [], total: 0, total_pages: 1 } };

const proposicaoAlrs = {
  fonte: 'ALRS',
  identificador_externo: '5bd6cb01',
  tipo: 'REQ',
  numero: '2',
  ano: 2025,
  ementa: 'Reanálise - PLC 288/2024',
  autor: 'Delegada Nadine',
  ja_importado: false,
};

function respostaPara(url: string, resposta: unknown) {
  mockedGet.mockImplementation(async (chamada: string) => {
    if (chamada === url) return resposta as never;
    return LISTA_VAZIA as never;
  });
}

describe('useProjetosLei — busca nas fontes oficiais', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedGet.mockResolvedValue(LISTA_VAZIA as never);
  });

  it('lê resultados e fontes_com_erro do payload agregado', async () => {
    respostaPara(BUSCAR_EXTERNO, { data: { resultados: [proposicaoAlrs], fontes_com_erro: ['CAMARA'] } });
    const { result } = renderHook(() => useProjetosLei());

    act(() => result.current.setNomeBusca('nadine'));

    await waitFor(() =>
      expect(mockedGet).toHaveBeenCalledWith(BUSCAR_EXTERNO, { params: { nome: 'nadine' } })
    );
    await waitFor(() => expect(result.current.resultadosExternos).toEqual([proposicaoAlrs]));
    expect(result.current.fontesComErro).toEqual(['CAMARA']);
    expect(result.current.isBuscando).toBe(false);
  });

  it('falha total da requisição marca todas as fontes como sem resposta, não como "nada encontrado"', async () => {
    mockedGet.mockImplementation(async (chamada: string) => {
      if (chamada === BUSCAR_EXTERNO) throw new Error('504 Gateway Timeout');
      return LISTA_VAZIA as never;
    });
    const { result } = renderHook(() => useProjetosLei());

    act(() => result.current.setNomeBusca('nadine'));

    await waitFor(() => expect(result.current.fontesComErro).toEqual(FONTES_EXTERNAS));
    expect(result.current.resultadosExternos).toEqual([]);
    expect(result.current.isBuscando).toBe(false);
  });

  it('ignora a resposta atrasada de uma busca anterior (ALRS lenta não sobrescreve a busca atual)', async () => {
    let resolverAntiga: (valor: unknown) => void = () => {};
    const respostaAntiga = new Promise((resolve) => { resolverAntiga = resolve; });
    mockedGet.mockImplementation(async (chamada: string, config?: AxiosRequestConfig) => {
      if (chamada !== BUSCAR_EXTERNO) return LISTA_VAZIA as never;
      if ((config?.params as { nome?: string } | undefined)?.nome === 'nad') return respostaAntiga as never;
      return { data: { resultados: [proposicaoAlrs], fontes_com_erro: [] } } as never;
    });
    const { result } = renderHook(() => useProjetosLei());

    act(() => result.current.setNomeBusca('nad'));
    await waitFor(() => expect(mockedGet).toHaveBeenCalledWith(BUSCAR_EXTERNO, { params: { nome: 'nad' } }));

    act(() => result.current.setNomeBusca('nadine'));
    await waitFor(() => expect(result.current.resultadosExternos).toEqual([proposicaoAlrs]));

    await act(async () => {
      resolverAntiga({ data: { resultados: [], fontes_com_erro: ['ALRS'] } });
    });

    expect(result.current.resultadosExternos).toEqual([proposicaoAlrs]);
    expect(result.current.fontesComErro).toEqual([]);
    expect(result.current.isBuscando).toBe(false);
  });

  it('limpa resultados e avisos ao apagar o termo para menos de 3 caracteres', async () => {
    respostaPara(BUSCAR_EXTERNO, { data: { resultados: [proposicaoAlrs], fontes_com_erro: ['ALRS'] } });
    const { result } = renderHook(() => useProjetosLei());

    act(() => result.current.setNomeBusca('nadine'));
    await waitFor(() => expect(result.current.resultadosExternos).toHaveLength(1));

    act(() => result.current.setNomeBusca('na'));

    await waitFor(() => expect(result.current.resultadosExternos).toEqual([]));
    expect(result.current.fontesComErro).toEqual([]);
  });
});

describe('descreverConferencia — idade da situação guardada', () => {
  const agora = new Date('2026-09-16T15:00:00Z');

  it('sem carimbo diz que nunca foi conferida', () => {
    expect(descreverConferencia(null, agora)).toBe('nunca conferida');
  });

  it('hoje, 1 dia e N dias', () => {
    expect(descreverConferencia('2026-09-16T09:00:00Z', agora)).toBe('conferida hoje');
    expect(descreverConferencia('2026-09-15T09:00:00Z', agora)).toBe('conferida há 1 dia');
    expect(descreverConferencia('2026-09-04T09:00:00Z', agora)).toBe('conferida há 12 dias');
  });
});

describe('useProjetosLei — sincronizar com a fonte oficial', () => {
  const mockedPost = vi.mocked(api.post);
  const projetoGuardado = {
    id_projeto_lei: 'pl-1', fonte: 'ALRS', identificador_externo: 'bc22b5f7', tipo: 'PL', numero: '5', ano: 2026,
    ementa: 'Dispõe sobre fisioterapeutas nas maternidades', situacao: 'Para Parecer', created_at: '2026-09-16T12:00:00Z',
    ultima_sincronizacao: '2026-09-16T12:00:00Z',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockedGet.mockResolvedValue({ data: { items: [projetoGuardado], total: 1, total_pages: 1 } } as never);
  });

  it('troca só a linha sincronizada e anuncia a mudança de situação', async () => {
    mockedPost.mockResolvedValue({
      data: {
        projeto: { ...projetoGuardado, situacao: 'Aprovado em Plenário', ultima_sincronizacao: '2026-09-16T15:00:00Z' },
        situacao_anterior: 'Para Parecer',
        situacao_alterada: true,
      },
    } as never);
    const { result } = renderHook(() => useProjetosLei());
    await waitFor(() => expect(result.current.projetosLei).toHaveLength(1));

    let retorno: unknown;
    await act(async () => { retorno = await result.current.sincronizar('pl-1'); });

    expect(mockedPost).toHaveBeenCalledWith('/api/v1/gabinete/projetos-lei/pl-1/sincronizar');
    expect(result.current.projetosLei[0].situacao).toBe('Aprovado em Plenário');
    expect(result.current.syncFeedback).toEqual({
      id_projeto_lei: 'pl-1', tipo: 'alterada', mensagem: 'Situação mudou: Para Parecer → Aprovado em Plenário',
    });
    expect(result.current.sincronizandoId).toBeNull();
    expect(retorno).toMatchObject({ situacao: 'Aprovado em Plenário' });
  });

  it('fonte fora do ar: mantém a linha e mostra o motivo vindo da API', async () => {
    mockedPost.mockRejectedValue({ response: { status: 503, data: { detail: 'ALRS não respondeu agora. A situação guardada foi mantida; tente de novo em instantes.' } } });
    const { result } = renderHook(() => useProjetosLei());
    await waitFor(() => expect(result.current.projetosLei).toHaveLength(1));

    await act(async () => { await result.current.sincronizar('pl-1'); });

    expect(result.current.projetosLei[0].situacao).toBe('Para Parecer');
    expect(result.current.syncFeedback?.tipo).toBe('erro');
    expect(result.current.syncFeedback?.mensagem).toContain('mantida');
  });
});
