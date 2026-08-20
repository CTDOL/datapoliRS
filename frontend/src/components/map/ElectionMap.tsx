'use client';

import { useEffect, useRef, useState } from 'react';
import * as maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

export interface LiderancaPoint {
  id_lideranca: string;
  nm_completo: string;
  tp_influencia: string;
  nm_municipio?: string;
  longitude?: number;
  latitude?: number;
}

interface ElectionMapProps {
  liderancas?: LiderancaPoint[];
}

const BASE_STYLES = {
  dark: {
    version: 8 as const,
    glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
    sources: {
      'carto-base': {
        type: 'raster',
        tiles: [
          'https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png',
          'https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png',
        ],
        tileSize: 256,
        attribution: '© CARTO, © OpenStreetMap',
      },
    },
    layers: [
      {
        id: 'carto-base-layer',
        type: 'raster',
        source: 'carto-base',
      },
    ],
  },
  light: {
    version: 8 as const,
    glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
    sources: {
      'carto-base': {
        type: 'raster',
        tiles: [
          'https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png',
          'https://b.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png',
        ],
        tileSize: 256,
        attribution: '© CARTO, © OpenStreetMap',
      },
    },
    layers: [
      {
        id: 'carto-base-layer',
        type: 'raster',
        source: 'carto-base',
      },
    ],
  }
};

export default function ElectionMap({ liderancas = [] }: ElectionMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  
  const [mapTheme, setMapTheme] = useState<'dark' | 'light'>('dark');

  // 1. Inicializa o Mapa
  useEffect(() => {
    if (!mapContainer.current) return;

    const mapInstance = new maplibregl.Map({
      container: mapContainer.current,
      style: BASE_STYLES[mapTheme] as maplibregl.StyleSpecification,
      center: [-51.2177, -30.0346], // RS / POA
      zoom: 7,
    });

    mapInstance.on('load', () => {
      mapInstance.resize();
    });

    map.current = mapInstance;

    return () => {
      mapInstance.remove();
      map.current = null;
    };
  }, []); // A inicialização roda apenas 1x. O tema será atualizado via setStyle()

  // Atualiza o tema do mapa sem recriar o Canvas
  useEffect(() => {
    if (map.current) {
      map.current.setStyle(BASE_STYLES[mapTheme] as maplibregl.StyleSpecification);
    }
  }, [mapTheme]);

  // 2. Engine Nativa do MapLibre: GeoJSON com Clustering e Dispersão
  const liderancasKey = JSON.stringify(liderancas);

  useEffect(() => {
    if (!map.current) return;
    const m = map.current;

    const lista = liderancas.length > 0 ? liderancas : [
      { id_lideranca: 'fallback', nm_completo: 'Teste (NH)', tp_influencia: 'Comunitária', nm_municipio: 'Novo Hamburgo', longitude: -51.1444, latitude: -29.6868 }
    ];

    const geoJsonData: GeoJSON.FeatureCollection = {
      type: 'FeatureCollection',
      features: lista.filter(l => l.longitude && l.latitude).map((l, i) => ({
        type: 'Feature',
        properties: { ...l },
        geometry: {
          type: 'Point',
          // Spiderify Matemático: Deslocamento radial (aprox. 20m) para impedir sobreposição exata
          coordinates: [Number(l.longitude) + Math.cos(i) * 0.0002, Number(l.latitude) + Math.sin(i) * 0.0002]
        }
      }))
    };

    const loadData = () => {
      const src = m.getSource('liderancas-src') as maplibregl.GeoJSONSource;
      if (src) {
        src.setData(geoJsonData);
      } else {
        m.addSource('liderancas-src', { type: 'geojson', data: geoJsonData, cluster: true, clusterMaxZoom: 14, clusterRadius: 50 });
        
        m.addLayer({ id: 'clusters', type: 'circle', source: 'liderancas-src', filter: ['has', 'point_count'], paint: { 'circle-color': '#0284c7', 'circle-radius': ['step', ['get', 'point_count'], 20, 10, 30, 50, 40], 'circle-stroke-width': 2, 'circle-stroke-color': '#fff' }});
        m.addLayer({ id: 'cluster-count', type: 'symbol', source: 'liderancas-src', filter: ['has', 'point_count'], layout: { 'text-field': '{point_count_abbreviated}', 'text-size': 14 }, paint: { 'text-color': '#ffffff' }});
        m.addLayer({ id: 'unclustered-point', type: 'circle', source: 'liderancas-src', filter: ['!', ['has', 'point_count']], paint: { 'circle-color': '#38bdf8', 'circle-radius': 8, 'circle-stroke-width': 2, 'circle-stroke-color': '#fff' }});

        // Popup interativo
        m.on('click', 'unclustered-point', (e) => {
          const props = e.features?.[0].properties as LiderancaPoint;
          const geometry = e.features?.[0].geometry as GeoJSON.Point;
          const coords = geometry.coordinates.slice() as [number, number];
          new maplibregl.Popup({ offset: 15 }).setLngLat(coords).setHTML(`
            <div style="color:#0f172a; padding:6px; font-family:sans-serif;">
              <strong style="color:#0284c7;">${props.nm_completo}</strong><br/>
              <span>Influência: <b>${props.tp_influencia}</b></span><br/>
              <span style="color:#64748b;">${props.nm_municipio || ''}</span>
            </div>
          `).addTo(m);
        });

        m.on('mouseenter', 'unclustered-point', () => m.getCanvas().style.cursor = 'pointer');
        m.on('mouseleave', 'unclustered-point', () => m.getCanvas().style.cursor = '');
      }
    };

    if (m.isStyleLoaded()) loadData();
    else m.once('styledata', loadData);

  }, [liderancasKey, mapTheme, liderancas]);

  return (
    <div className="w-full h-[600px] min-h-[600px] rounded-2xl overflow-hidden shadow-2xl border border-slate-800 bg-slate-950 relative">
      <div ref={mapContainer} className="w-full h-full" />
      
      {/* Controle de Mapa Base */}
      <div className="absolute top-4 right-4 bg-slate-900/80 backdrop-blur-md p-1 rounded-lg border border-slate-700/50 flex space-x-1 z-10 shadow-lg">
        <button
          onClick={() => setMapTheme('dark')}
          className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
            mapTheme === 'dark' 
              ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20' 
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          Dark
        </button>
        <button
          onClick={() => setMapTheme('light')}
          className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
            mapTheme === 'light' 
              ? 'bg-slate-100 text-slate-900 shadow-md' 
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          Light
        </button>
      </div>
    </div>
  );
}