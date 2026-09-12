'use client';

import { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

export interface LiderancaPoint {
  id_lideranca: string;
  nm_completo: string;
  tp_influencia: string;
  nm_municipio?: string;
  longitude?: number;
  latitude?: number;
}

export type MapViewMode = 'liderancas' | 'votacao' | 'cruzada';

interface ElectionMapProps {
  liderancas?: LiderancaPoint[];
  viewMode?: MapViewMode;
  /** cd_ibge_7 -> quantidade de votos nominais do candidato selecionado */
  votosPorMunicipio?: Record<string, number>;
}

const MUNICIPIOS_GEOJSON_URL = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/geo/municipios`;

// Mesma abordagem (Leaflet + L.geoJson) já comprovadamente funcional no
// portal público (app/static/script.js) — o MapLibre GL (WebGL) não estava
// renderizando camadas de polígono neste ambiente por um motivo ainda não
// isolado; Leaflet usa SVG/Canvas 2D e funciona de forma confirmada no
// mesmo navegador.
//
// Tiles raster: Esri Canvas (gratuito, sem API key). O CARTO passou a
// exigir API key nos endpoints basemaps.cartocdn.com/{dark,light}_all —
// substituído para não depender de credencial paga em ambiente local.
const TILE_URLS: Record<'dark' | 'light', string> = {
  dark: 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
  light: 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}',
};

function getChoroplethColor(votos: number, maxVotos: number): string {
  if (!votos) return 'rgba(148, 163, 184, 0.06)';
  const fraction = votos / maxVotos;
  if (fraction > 0.75) return '#4c1d95';
  if (fraction > 0.5) return '#6d28d9';
  if (fraction > 0.25) return '#7c3aed';
  if (fraction > 0.1) return '#a78bfa';
  if (fraction > 0.02) return '#c4b5fd';
  return '#ede9fe';
}

export default function ElectionMap({ liderancas = [], viewMode = 'liderancas', votosPorMunicipio = {} }: ElectionMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<L.Map | null>(null);
  const tileLayerRef = useRef<L.TileLayer | null>(null);
  const choroplethLayerRef = useRef<L.GeoJSON | null>(null);
  const markersRef = useRef<L.Marker[]>([]);

  const [mapTheme, setMapTheme] = useState<'dark' | 'light'>('dark');

  // Refs sempre atualizados em efeito (não durante o render) para os callbacks
  // de estilo do Leaflet (registrados uma vez) lerem o valor mais recente.
  const viewModeRef = useRef(viewMode);
  const votosRef = useRef(votosPorMunicipio);
  useEffect(() => {
    viewModeRef.current = viewMode;
    votosRef.current = votosPorMunicipio;
  });

  const applyChoroplethStyle = () => {
    const layer = choroplethLayerRef.current;
    if (!layer) return;
    const votos = votosRef.current;
    const values = Object.values(votos);
    const maxVotos = values.length > 0 ? Math.max(1, ...values) : 1;

    layer.setStyle((feature) => {
      const ibgeId = (feature?.properties as { id?: string } | undefined)?.id;
      const v = (ibgeId && votos[ibgeId]) || 0;
      return {
        fillColor: getChoroplethColor(v, maxVotos),
        weight: 0.5,
        color: 'rgba(255, 255, 255, 0.2)',
        opacity: 1,
        fillOpacity: 0.8,
      };
    });
  };

  const applyChoroplethVisibility = () => {
    const layer = choroplethLayerRef.current;
    const m = map.current;
    if (!layer || !m) return;
    const shouldShow = viewModeRef.current === 'votacao' || viewModeRef.current === 'cruzada';
    const isShown = m.hasLayer(layer);
    if (shouldShow && !isShown) layer.addTo(m);
    if (!shouldShow && isShown) m.removeLayer(layer);
  };

  // 1. Inicializa o mapa (Leaflet), os tiles base e a camada coroplética (oculta até o modo Votação/Cruzada)
  useEffect(() => {
    if (!mapContainer.current) return;

    const mapInstance = L.map(mapContainer.current, { zoomControl: true }).setView([-30.0346, -51.2177], 7);
    map.current = mapInstance;

    const tileLayer = L.tileLayer(TILE_URLS[mapTheme], {
      maxZoom: 16,
      attribution: '&copy; Esri, &copy; OpenStreetMap',
    }).addTo(mapInstance);
    tileLayerRef.current = tileLayer;

    fetch(MUNICIPIOS_GEOJSON_URL)
      .then((resp) => resp.json())
      .then((geojson: GeoJSON.FeatureCollection) => {
        const layer = L.geoJson(geojson, {
          style: () => ({
            fillColor: 'rgba(148, 163, 184, 0.06)',
            weight: 0.5,
            color: 'rgba(255, 255, 255, 0.2)',
            opacity: 1,
            fillOpacity: 0.8,
          }),
        });
        choroplethLayerRef.current = layer;
        applyChoroplethStyle();
        applyChoroplethVisibility();
      })
      .catch((err) => console.error('Falha ao carregar GeoJSON de municípios para o mapa coroplético:', err));

    return () => {
      mapInstance.remove();
      map.current = null;
      tileLayerRef.current = null;
      choroplethLayerRef.current = null;
    };
  }, []); // Inicialização roda apenas 1x. Tema e dados são atualizados por efeitos próprios.

  // Troca a camada de tiles ao alternar Dark/Light — pula a primeira execução
  // (o mapa já nasce com o tema inicial no efeito de inicialização acima).
  const isFirstThemeRender = useRef(true);
  useEffect(() => {
    if (isFirstThemeRender.current) {
      isFirstThemeRender.current = false;
      return;
    }
    const m = map.current;
    if (!m) return;
    if (tileLayerRef.current) m.removeLayer(tileLayerRef.current);
    tileLayerRef.current = L.tileLayer(TILE_URLS[mapTheme], {
      maxZoom: 16,
      attribution: '&copy; Esri, &copy; OpenStreetMap',
    }).addTo(m);
  }, [mapTheme]);

  // Reaplica cor/visibilidade da coropletia quando os votos ou o modo mudam
  useEffect(() => {
    applyChoroplethStyle();
    applyChoroplethVisibility();
  }, [votosPorMunicipio, viewMode]);

  // Limpa e recria os marcadores de lideranças sempre que a lista muda
  useEffect(() => {
    const m = map.current;
    if (!m) return;

    markersRef.current.forEach((marker) => m.removeLayer(marker));
    markersRef.current = [];

    // No modo "apenas votação", os pontos de lideranças ficam ocultos.
    if (viewMode === 'votacao') return;

    const validLiderancas = liderancas.filter((l) => l.longitude && l.latitude);

    validLiderancas.forEach((l, i) => {
      // Pequeno spiderify matemático
      const lng = Number(l.longitude) + Math.cos(i) * 0.0002;
      const lat = Number(l.latitude) + Math.sin(i) * 0.0002;

      // Elemento externo: é o que o Leaflet posiciona via transform inline.
      // Não pode receber a propriedade CSS `scale` (via hover:scale-*) aqui — no
      // Tailwind v4, `scale` é composto ENVOLVENDO o transform inline do Leaflet,
      // amplificando também o deslocamento, não só o tamanho.
      const icon = L.divIcon({
        className: '',
        html: `
          <div class="lideranca-marker w-4 h-4 cursor-pointer">
            <div class="w-full h-full bg-sky-500 border-2 border-white rounded-full shadow-[0_0_10px_rgba(14,165,233,0.8)] hover:scale-125 transition-transform"></div>
          </div>
        `,
        iconSize: [16, 16],
        iconAnchor: [8, 8],
      });

      const marker = L.marker([lat, lng], { icon }).addTo(m);
      marker.bindPopup(`
        <div style="color:#0f172a; padding:4px; font-family:sans-serif;">
          <strong style="color:#0284c7; font-size:14px;">${l.nm_completo}</strong><br/>
          <span style="font-size:12px;">Influência: <b>${l.tp_influencia}</b></span><br/>
          <span style="color:#64748b; font-size:11px;">${l.nm_municipio || ''}</span>
        </div>
      `);
      markersRef.current.push(marker);
    });
  }, [JSON.stringify(liderancas), viewMode]);

  // Ajusta o enquadramento do mapa pra caber todas as lideranças, em vez de um centro/zoom fixo
  useEffect(() => {
    const m = map.current;
    if (!m) return;

    const validLiderancas = liderancas.filter((l) => l.longitude && l.latitude);
    if (validLiderancas.length === 0) return;

    const bounds = L.latLngBounds(validLiderancas.map((l) => [Number(l.latitude), Number(l.longitude)] as [number, number]));
    m.fitBounds(bounds, { padding: [60, 60], maxZoom: 12 });
  }, [JSON.stringify(liderancas)]);

  return (
    <div className="w-full h-[600px] min-h-[600px] rounded-2xl overflow-hidden shadow-2xl border border-zinc-800 bg-zinc-950 relative">
      <div ref={mapContainer} className="w-full h-full" />

      {/* Controle de Mapa Base */}
      <div className="absolute top-4 right-4 z-[1000] flex bg-zinc-900/80 backdrop-blur-md rounded-xl p-1 border border-zinc-700/50 shadow-xl">
        <button
          onClick={() => setMapTheme('dark')}
          className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
            mapTheme === 'dark'
              ? 'bg-purple-600 text-white shadow-md shadow-purple-500/20'
              : 'text-zinc-400 hover:text-white hover:bg-zinc-800'
          }`}
        >
          Dark
        </button>
        <button
          onClick={() => setMapTheme('light')}
          className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
            mapTheme === 'light'
              ? 'bg-zinc-100 text-zinc-900 shadow-md'
              : 'text-zinc-400 hover:text-white hover:bg-zinc-800'
          }`}
        >
          Light
        </button>
      </div>
    </div>
  );
}
