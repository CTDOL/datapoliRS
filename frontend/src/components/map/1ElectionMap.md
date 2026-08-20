'use client';

import React, { useEffect, useRef } from 'react';
import * as maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

interface ElectionMapProps {
  geoJsonData?: GeoJSON.FeatureCollection;
}

export default function ElectionMap({ geoJsonData }: ElectionMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);

  useEffect(() => {
    if (map.current || !mapContainer.current) return;

    // Initialize MapLibre instance with premium dark styling and 3D perspective
    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://demotiles.maplibre.org/style.json',
      center: [-51.2177, -30.0346], // Centered roughly on RS, Brazil
      zoom: 6.5,
      pitch: 55, // Inclinação 3D para o efeito de central de comando
      bearing: -15, // Rotação leve para gerar profundidade
    });

    const currentMap = map.current;

    // Fix for Next.js 14 WebGL container sizing bug
    setTimeout(() => {
      currentMap.resize();
    }, 500);

    currentMap.on('load', () => {
      currentMap.resize();
      // If we don't have real data yet, we can't draw the layer, but we setup the source
      if (!geoJsonData) return;

      currentMap.addSource('municipalities', {
        type: 'geojson',
        data: geoJsonData,
      });

      // The core 3D visualization layer: fill-extrusion
      currentMap.addLayer({
        id: 'municipalities-3d',
        type: 'fill-extrusion',
        source: 'municipalities',
        paint: {
          // Dynamic color scale based on vote density (mock property 'total_votes')
          // Interpolating from a deep tactical blue to neon cyan/purple
          'fill-extrusion-color': [
            'interpolate',
            ['linear'],
            ['get', 'total_votes'],
            0, '#0f172a',       // Slate 950
            1000, '#1e3a8a',    // Blue 900
            10000, '#3b82f6',   // Blue 500
            50000, '#8b5cf6',   // Violet 500
            100000, '#2dd4bf',  // Teal 400 (Neon pop for high density)
          ],
          
          // The height of the 3D polygons (also mapped to 'total_votes')
          'fill-extrusion-height': [
            'interpolate',
            ['linear'],
            ['get', 'total_votes'],
            0, 0,
            100000, 50000 // Scales height for dramatic 3D effect
          ],
          
          // Base height (0 so they start from the ground)
          'fill-extrusion-base': 0,
          
          // Subtle opacity to allow basemap underneath to show slightly
          'fill-extrusion-opacity': 0.85,
        },
      });

      // Optional: Add a neon glow effect underneath the extruded polygons
      currentMap.addLayer({
        id: 'municipalities-glow',
        type: 'line',
        source: 'municipalities',
        paint: {
          'line-color': '#2dd4bf',
          'line-width': 1,
          'line-opacity': 0.3,
        }
      });
    });

    // Cleanup on unmount
    return () => {
      currentMap.remove();
      map.current = null;
    };
  }, [geoJsonData]);

  return (
    <div className="relative w-full h-full rounded-2xl overflow-hidden shadow-[0_0_40px_rgba(0,0,0,0.5)] border border-slate-800/50">
      <div 
        ref={mapContainer} 
        className="absolute inset-0"
      />
      {/* Premium UI Overlay Elements (e.g. Map Controls / Legend placeholder) */}
      <div className="absolute bottom-6 left-6 z-10 backdrop-blur-md bg-slate-950/60 border border-slate-700/50 p-4 rounded-xl">
        <h3 className="text-white text-sm font-bold tracking-widest uppercase mb-2">
          Densidade Eleitoral
        </h3>
        <div className="flex items-center gap-2">
          <div className="w-32 h-2 rounded-full bg-gradient-to-r from-slate-950 via-blue-500 to-teal-400" />
          <span className="text-xs text-slate-400 font-mono">HIGH</span>
        </div>
      </div>
    </div>
  );
}
