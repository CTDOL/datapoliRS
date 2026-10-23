import { useEffect, useState } from 'react';

// Caminho relativo: o navegador sempre fala com o próprio host que serviu a
// página, e o rewrite same-origin (next.config.ts) encaminha pra API real —
// nunca monte URL absoluta com NEXT_PUBLIC_API_URL aqui (ADR_026_datapolirs).
const MUNICIPIOS_GEOJSON_URL = '/api/v1/geo/municipios';

/**
 * Polígonos dos municípios do RS para a camada coroplética.
 * `fetch` em vez do cliente axios para o navegador aproveitar o Cache-Control
 * de longa duração da rota (ADR 029).
 */
export function useMunicipiosGeoJson(): GeoJSON.FeatureCollection | null {
  const [geojson, setGeojson] = useState<GeoJSON.FeatureCollection | null>(null);

  useEffect(() => {
    let cancelado = false;
    fetch(MUNICIPIOS_GEOJSON_URL)
      .then((resp) => {
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        return resp.json();
      })
      .then((dados: GeoJSON.FeatureCollection) => {
        if (!cancelado) setGeojson(dados);
      })
      .catch((err) => console.error('Falha ao carregar GeoJSON de municípios para o mapa coroplético:', err));
    return () => {
      cancelado = true;
    };
  }, []);

  return geojson;
}
