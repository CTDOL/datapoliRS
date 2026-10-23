import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useBuscaCandidato } from './useBuscaCandidato';
import { api } from '@/services/api';

vi.mock('@/services/api', () => ({
  api: { get: vi.fn() },
}));

const mockedGet = vi.mocked(api.get);
const NADINE = { sq_candidato: 1, nr_candidato: 55444, nm_urna_candidato: 'DELEGADA NADINE', sg_partido: 'PSD', ds_cargo: 'Deputado Estadual' };

describe('useBuscaCandidato', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('só consulta a API depois de 350ms sem digitar e com pelo menos 2 letras', async () => {
    mockedGet.mockResolvedValue({ data: [NADINE] });
    const { result } = renderHook(() => useBuscaCandidato());

    act(() => result.current.alterarTermo('N'));
    await act(async () => { await vi.advanceTimersByTimeAsync(400); });
    expect(mockedGet).not.toHaveBeenCalled();

    act(() => result.current.alterarTermo('Na'));
    act(() => result.current.alterarTermo('Nad'));
    await act(async () => { await vi.advanceTimersByTimeAsync(349); });
    expect(mockedGet).not.toHaveBeenCalled();

    await act(async () => { await vi.advanceTimersByTimeAsync(1); });
    expect(mockedGet).toHaveBeenCalledTimes(1);
    expect(mockedGet).toHaveBeenCalledWith('/api/v1/candidatos', { params: { termo: 'Nad', limite: 8 } });
    expect(result.current.resultadosBusca).toEqual([NADINE]);
  });

  it('ao selecionar, monta o mapa de votos por município e ignora município sem código', async () => {
    mockedGet.mockResolvedValue({
      data: { distribuicao_municipios: [
        { cd_ibge_7: '4314902', votos: 1200 },
        { cd_ibge_7: null, votos: 5 },
      ] },
    });
    const { result } = renderHook(() => useBuscaCandidato());

    await act(async () => { await result.current.selecionarCandidato(NADINE); });

    expect(mockedGet).toHaveBeenCalledWith('/api/v1/votacao/candidatos/1/municipios');
    expect(result.current.candidatoSelecionado).toEqual(NADINE);
    expect(result.current.votosPorMunicipio).toEqual({ '4314902': 1200 });

    act(() => result.current.limparCandidato());
    expect(result.current.candidatoSelecionado).toBeNull();
    expect(result.current.votosPorMunicipio).toEqual({});
  });
});
