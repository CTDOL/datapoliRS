import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useMunicipiosGeoJson } from './useMunicipiosGeoJson';

const GEOJSON = { type: 'FeatureCollection', features: [] };

function respostaJson(status: number, corpo: unknown) {
  return { ok: status >= 200 && status < 300, status, json: async () => corpo } as Response;
}

describe('useMunicipiosGeoJson', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it('devolve o GeoJSON quando a resposta é válida', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(respostaJson(200, GEOJSON));

    const { result } = renderHook(() => useMunicipiosGeoJson());

    await waitFor(() => expect(result.current).toEqual(GEOJSON));
    expect(fetch).toHaveBeenCalledWith('/api/v1/geo/municipios');
  });

  it('erro HTTP não quebra o mapa: fica null e registra o erro no console', async () => {
    const erro = vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.mocked(fetch).mockResolvedValueOnce(respostaJson(500, {}));

    const { result } = renderHook(() => useMunicipiosGeoJson());

    await waitFor(() => expect(erro).toHaveBeenCalled());
    expect(result.current).toBeNull();
  });
});
