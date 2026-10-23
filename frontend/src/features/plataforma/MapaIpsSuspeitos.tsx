'use client';

import { useEffect, useRef } from 'react';
import 'leaflet/dist/leaflet.css';

export interface PontoIp {
  ip: string;
  motivos: string[];
  localizacao: string | null;
  coordenadas: [number, number] | null;
}

/** Mapa dos IPs suspeitos da última hora (ADR 040). Só mostra IPs com localização da base local. */
export function MapaIpsSuspeitos({ pontos }: { pontos: PontoIp[] }) {
  const container = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let mapa: L.Map | null = null;
    let ativo = true;
    // Leaflet usa window: carregado só no navegador, nunca na renderização do servidor.
    import('leaflet').then((modulo) => {
      if (!ativo || !container.current) return;
      const L = modulo.default;
      mapa = L.map(container.current, { zoomControl: true }).setView([-14.2, -51.9], 3);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap',
      }).addTo(mapa);

      const marcados = pontos.filter((p) => p.coordenadas !== null);
      marcados.forEach((p) => {
        L.circleMarker(p.coordenadas as [number, number], { radius: 8, color: '#f87171', fillOpacity: 0.7 })
          .bindPopup(`<strong>${p.ip}</strong><br/>${p.localizacao ?? ''}<br/>${p.motivos.join(' · ')}`)
          .addTo(mapa!);
      });
      if (marcados.length > 0) {
        mapa.fitBounds(L.latLngBounds(marcados.map((p) => p.coordenadas as [number, number])), { maxZoom: 5, padding: [30, 30] });
      }
    });

    return () => {
      ativo = false;
      mapa?.remove();
    };
  }, [pontos]);

  return <div ref={container} className="mt-4 h-72 w-full overflow-hidden rounded-xl border border-zinc-800" aria-label="Mapa de IPs suspeitos" />;
}
