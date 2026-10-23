import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, waitFor } from '@testing-library/react';
import ElectionMap from './ElectionMap';
import type { LiderancaPoint } from './ElectionMap';

const NOVO_HAMBURGO = { cd_ibge_7: '4313409', nm_municipio: 'Novo Hamburgo', latitude: -29.68, longitude: -51.13 };
const PORTO_ALEGRE = { cd_ibge_7: '4314902', nm_municipio: 'Porto Alegre', latitude: -30.03, longitude: -51.23 };

function lideranca(id: string, nome: string, municipios: typeof NOVO_HAMBURGO[]): LiderancaPoint {
  return { id_lideranca: id, nm_completo: nome, tp_influencia: 'Comunitária', municipios };
}

describe('ElectionMap', () => {
  beforeEach(() => {
    // Sem GeoJSON: a camada coroplética não é o foco destes testes.
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 500, json: async () => ({}) }));
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it('monta e desmonta o Leaflet sem erro, mesmo sem ResizeObserver no ambiente', () => {
    expect(typeof ResizeObserver).toBe('undefined');

    const { container, unmount } = render(<ElectionMap />);

    expect(container.querySelector('.leaflet-container')).not.toBeNull();
    expect(() => unmount()).not.toThrow();
  });

  it('duas lideranças no mesmo município viram um único pino com contador "2"', async () => {
    const { container } = render(
      <ElectionMap
        liderancas={[
          lideranca('1', 'Jonas', [NOVO_HAMBURGO]),
          lideranca('2', 'STIVE', [NOVO_HAMBURGO]),
        ]}
      />
    );

    await waitFor(() => expect(container.querySelectorAll('.lideranca-marker')).toHaveLength(1));
    expect(container.querySelector('.lideranca-marker')?.textContent).toContain('2');
  });

  it('lideranças em municípios diferentes geram um pino por município', async () => {
    const { container } = render(
      <ElectionMap
        liderancas={[
          lideranca('1', 'Jonas', [NOVO_HAMBURGO]),
          lideranca('2', 'STIVE', [PORTO_ALEGRE]),
        ]}
      />
    );

    await waitFor(() => expect(container.querySelectorAll('.lideranca-marker')).toHaveLength(2));
  });
});
