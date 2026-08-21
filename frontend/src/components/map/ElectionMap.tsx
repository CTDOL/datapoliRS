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

  // Atualiza o tema do mapa
  useEffect(() => {
    if (map.current) {
      map.current.setStyle(BASE_STYLES[mapTheme] as maplibregl.StyleSpecification);
    }
  }, [mapTheme]);

  // Limpa e recria os markers sempre que a liderança muda
  useEffect(() => {
    if (!map.current) return;
    const m = map.current;

    // Remove marcadores antigos (usamos uma classe css customizada para rastreá-los)
    const existingMarkers = document.querySelectorAll('.lideranca-marker');
    existingMarkers.forEach(node => node.remove());

    const validLiderancas = liderancas.filter(l => l.longitude && l.latitude);

    validLiderancas.forEach((l, i) => {
      // Pequeno spiderify matemático
      const lng = Number(l.longitude) + Math.cos(i) * 0.0002;
      const lat = Number(l.latitude) + Math.sin(i) * 0.0002;

      // Elemento externo: é o que o MapLibre posiciona via transform inline (translate em px).
      // Não pode receber a propriedade CSS `scale` (via hover:scale-*) aqui — no Tailwind v4,
      // `scale` é uma propriedade separada de `transform` e o navegador a compõe ENVOLVENDO
      // o transform inline do MapLibre, amplificando também o deslocamento (não só o tamanho),
      // o que faz o ponto "pular" pra longe da posição real ao passar o mouse.
      const el = document.createElement('div');
      el.className = 'lideranca-marker w-4 h-4 cursor-pointer';

      // Elemento interno: recebe a aparência visual e o efeito de hover, isolado do posicionamento.
      const dot = document.createElement('div');
      dot.className = 'w-full h-full bg-sky-500 border-2 border-white rounded-full shadow-[0_0_10px_rgba(14,165,233,0.8)] hover:scale-125 transition-transform';
      el.appendChild(dot);

      // Configura o popup
      const popup = new maplibregl.Popup({ offset: 15, closeButton: true }).setHTML(`
        <div style="color:#0f172a; padding:4px; font-family:sans-serif;">
          <strong style="color:#0284c7; font-size:14px;">${l.nm_completo}</strong><br/>
          <span style="font-size:12px;">Influência: <b>${l.tp_influencia}</b></span><br/>
          <span style="color:#64748b; font-size:11px;">${l.nm_municipio || ''}</span>
        </div>
      `);

      // Adiciona o marker no mapa
      new maplibregl.Marker({ element: el })
        .setLngLat([lng, lat])
        .setPopup(popup)
        .addTo(m);
    });

  }, [JSON.stringify(liderancas), mapTheme]); // Refaz ao mudar dados ou tema (segurança extra)

  // Ajusta o enquadramento do mapa pra caber todas as lideranças, em vez de um centro/zoom fixo
  // (com centro fixo em POA, pontos distantes como Uruguaiana ficavam fora da área visível).
  // Depende só de `liderancas` (não do tema) pra não resetar o zoom/pan ao trocar Dark/Light.
  useEffect(() => {
    if (!map.current) return;

    const validLiderancas = liderancas.filter(l => l.longitude && l.latitude);
    if (validLiderancas.length === 0) return;

    const bounds = new maplibregl.LngLatBounds();
    validLiderancas.forEach(l => bounds.extend([Number(l.longitude), Number(l.latitude)]));

    map.current.fitBounds(bounds, {
      padding: 60,
      maxZoom: 12, // evita zoom exagerado quando há só 1 liderança
      duration: 0,
    });
  }, [JSON.stringify(liderancas)]);

  return (
    <div className="w-full h-[600px] min-h-[600px] rounded-2xl overflow-hidden shadow-2xl border border-zinc-800 bg-zinc-950 relative">
      <div ref={mapContainer} className="w-full h-full" />
      
      {/* Controle de Mapa Base */}
      <div className="absolute top-4 right-4 z-10 flex bg-zinc-900/80 backdrop-blur-md rounded-xl p-1 border border-zinc-700/50 shadow-xl">
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