import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useMunicipios, limparCacheMunicipios } from './useMunicipios';
import { api } from '@/services/api';

vi.mock('@/services/api', () => ({
  api: { get: vi.fn() },
}));

const mockedGet = vi.mocked(api.get);
const LISTA = [{ cd_ibge_7: '4314902', nm_municipio: 'Porto Alegre' }];

describe('useMunicipios', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    limparCacheMunicipios();
    mockedGet.mockResolvedValue({ data: LISTA });
  });

  it('várias telas montadas compartilham uma única requisição', async () => {
    const mapa = renderHook(() => useMunicipios());
    const tabela = renderHook(() => useMunicipios());

    await waitFor(() => expect(mapa.result.current.municipios).toEqual(LISTA));
    await waitFor(() => expect(tabela.result.current.municipios).toEqual(LISTA));
    expect(mockedGet).toHaveBeenCalledTimes(1);
    expect(mapa.result.current.isLoading).toBe(false);
  });

  it('não busca enquanto inativo (modal fechado)', async () => {
    const { result } = renderHook(() => useMunicipios(false));

    expect(result.current.isLoading).toBe(false);
    expect(mockedGet).not.toHaveBeenCalled();
  });

  it('uma falha não fica em cache: a próxima tela tenta de novo', async () => {
    vi.spyOn(console, 'error').mockImplementation(() => {});
    mockedGet.mockRejectedValueOnce(new Error('rede'));

    const primeira = renderHook(() => useMunicipios());
    await waitFor(() => expect(primeira.result.current.isLoading).toBe(false));
    expect(primeira.result.current.municipios).toEqual([]);

    const segunda = renderHook(() => useMunicipios());
    await waitFor(() => expect(segunda.result.current.municipios).toEqual(LISTA));
    expect(mockedGet).toHaveBeenCalledTimes(2);
  });
});
