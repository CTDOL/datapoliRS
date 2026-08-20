'use client';

import { useEffect, useRef } from 'react';
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

export default function ElectionMap({ liderancas = [] }: ElectionMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const markersRef = useRef<maplibregl.Marker[]>([]);

  // 1. Inicializa o Mapa
  useEffect(() => {
    if (!mapContainer.current) return;

    const mapInstance = new maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8,
        sources: {
          'carto-dark': {
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
            id: 'carto-dark-layer',
            type: 'raster',
            source: 'carto-dark',
          },
        ],
      },
      center: [-51.2177, -30.0346], // RS / POA
      zoom: 7,
    });

    mapInstance.on('load', () => {
      mapInstance.resize();
    });

    map.current = mapInstance;

    return () => {
      markersRef.current.forEach((m) => m.remove());
      mapInstance.remove();
      map.current = null;
    };
  }, []);

  // 2. Renderiza e Atualiza os Marcadores de Liderança (Protegido por Deep Compare)
  const liderancasKey = JSON.stringify(liderancas);

  useEffect(() => {
    if (!map.current) return;

    console.log('📍 Renderizando Lideranças no Mapa');

    // Remove marcadores anteriores
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];

    // Se a lista estiver vazia, injeta um ponto de fallback de teste em Novo Hamburgo
    const listaParaPlotar = liderancas.length > 0 ? liderancas : [
      {
        id_lideranca: 'fallback',
        nm_completo: 'Liderança Teste (Novo Hamburgo)',
        tp_influencia: 'Comunitária',
        nm_municipio: 'Novo Hamburgo',
        longitude: -51.1444,
        latitude: -29.6868,
      }
    ];

    listaParaPlotar.forEach((l) => {
      if (l.longitude === undefined || l.latitude === undefined) return;

      // Criação do Elemento HTML Neon Personalizado
      const el = document.createElement('div');
      el.className = 'cursor-pointer flex items-center justify-center';
      el.style.width = '24px';
      el.style.height = '24px';
      el.innerHTML = `
        <div style="
          position: absolute;
          width: 22px;
          height: 22px;
          border-radius: 50%;
          background: rgba(56, 189, 248, 0.4);
          animation: ping 2s cubic-bezier(0, 0, 0.2, 1) infinite;
        "></div>
        <div style="
          position: relative;
          width: 12px;
          height: 12px;
          border-radius: 50%;
          background: #38bdf8;
          border: 2px solid #ffffff;
          box-shadow: 0 0 10px #0284c7;
        "></div>
      `;

      // Popup ao clicar
      const popup = new maplibregl.Popup({ offset: 15 }).setHTML(`
        <div style="color: #0f172a; padding: 6px; font-family: sans-serif; font-size: 12px;">
          <strong style="font-size: 14px; color: #0284c7;">${l.nm_completo}</strong><br/>
          <span style="color: #475569;">Influência: <b>${l.tp_influencia}</b></span><br/>
          <span style="color: #64748b;">Município: ${l.nm_municipio || 'Não informado'}</span>
        </div>
      `);

      // Anexa o marcador ao mapa
      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([Number(l.longitude), Number(l.latitude)])
        .setPopup(popup)
        .addTo(map.current!);

      markersRef.current.push(marker);
    });
  }, [liderancasKey]); // O MapLibre só re-renderizará se os dados mudarem fisicamente

  return (
    <div className="w-full h-[600px] min-h-[600px] rounded-2xl overflow-hidden shadow-2xl border border-slate-800 bg-slate-950 relative">
      <div ref={mapContainer} className="w-full h-full" />
    </div>
  );
}