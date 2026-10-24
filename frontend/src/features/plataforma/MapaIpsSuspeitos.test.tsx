import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, waitFor } from '@testing-library/react';
import { MapaIpsSuspeitos } from './MapaIpsSuspeitos';
import L from 'leaflet';

vi.mock('leaflet', () => {
  const marcador = { bindPopup: vi.fn().mockReturnThis(), addTo: vi.fn().mockReturnThis() };
  const mapa = { addTo: vi.fn(), remove: vi.fn(), fitBounds: vi.fn() };
  return {
    default: {
      map: vi.fn(() => ({ ...mapa, setView: vi.fn(() => mapa) })),
      tileLayer: vi.fn(() => ({ addTo: vi.fn() })),
      circleMarker: vi.fn(() => marcador),
      latLngBounds: vi.fn(() => ({})),
    },
  };
});

describe('MapaIpsSuspeitos', () => {
  beforeEach(() => vi.clearAllMocks());

  it('marca apenas os IPs com coordenadas e remove o mapa ao desmontar', async () => {
    const { unmount } = render(
      <MapaIpsSuspeitos
        pontos={[
          { ip: '8.8.8.8', motivos: ['6 senhas erradas'], localizacao: 'United States', coordenadas: [37.4, -122.1] },
          { ip: '1.1.1.1', motivos: ['6 senhas erradas'], localizacao: null, coordenadas: null },
        ]}
      />,
    );

    await waitFor(() => expect(L.circleMarker).toHaveBeenCalledTimes(1));
    expect(L.circleMarker).toHaveBeenCalledWith([37.4, -122.1], expect.anything());
    const mapa = vi.mocked(L.map).mock.results[0].value;
    unmount();
    expect(mapa.remove).toHaveBeenCalled();
  });
});
