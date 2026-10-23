'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import {
  MapTheme,
  adicionarCamadasBase,
  aplicarEstiloCoropletico,
  ajustarVisibilidadeCoropletica,
  agruparPorMunicipio,
  iconeLideranca,
  pontosDasLiderancas,
  popupLideranca,
  popupMunicipio,
} from './mapLayers';
import { useMunicipiosGeoJson } from './useMunicipiosGeoJson';

export interface MunicipioAtuacaoPoint {
  cd_ibge_7: string;
  nm_municipio?: string;
  latitude?: number;
  longitude?: number;
}

export interface LiderancaPoint {
  id_lideranca: string;
  nm_completo: string;
  tp_influencia: string;
  nr_telefone?: string;
  ds_foto_url?: string | null;
  /** Uma liderança pode atuar em vários municípios — um marcador é plotado por município. */
  municipios: MunicipioAtuacaoPoint[];
}

export type MapViewMode = 'liderancas' | 'votacao' | 'cruzada';

interface ElectionMapProps {
  liderancas?: LiderancaPoint[];
  viewMode?: MapViewMode;
  /** cd_ibge_7 -> quantidade de votos nominais do candidato selecionado */
  votosPorMunicipio?: Record<string, number>;
}

// Constantes de módulo: um default `= []` criaria array novo a cada render.
const SEM_LIDERANCAS: LiderancaPoint[] = [];
const SEM_VOTOS: Record<string, number> = {};

// Mesma abordagem (Leaflet + L.geoJson) já comprovadamente funcional no
// portal público (app/static/script.js) — o MapLibre GL (WebGL) não estava
// renderizando camadas de polígono neste ambiente por um motivo ainda não
// isolado; Leaflet usa SVG/Canvas 2D e funciona de forma confirmada no
// mesmo navegador.
export default function ElectionMap({
  liderancas = SEM_LIDERANCAS,
  viewMode = 'liderancas',
  votosPorMunicipio = SEM_VOTOS,
}: ElectionMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<L.Map | null>(null);
  const markersRef = useRef<L.Marker[]>([]);
  const [mapTheme, setMapTheme] = useState<MapTheme>('dark');

  const geojson = useMunicipiosGeoJson();
  // Só cria a camada; quem a coloca no mapa é o efeito de visibilidade.
  const camadaCoropletica = useMemo(() => (geojson ? L.geoJson(geojson) : null), [geojson]);

  // A página entrega um array novo a cada busca, mesmo com o mesmo conteúdo
  // (ex.: filtro digitado e apagado). Comparar pelo conteúdo evita redesenhar os
  // marcadores e reenquadrar o mapa à toa.
  const chaveLiderancas = JSON.stringify(liderancas);
  const liderancasEstaveis = useMemo<LiderancaPoint[]>(() => JSON.parse(chaveLiderancas), [chaveLiderancas]);

  // 1. Cria o mapa uma única vez. Tema, camadas e marcadores têm efeitos próprios.
  useEffect(() => {
    if (!mapContainer.current) return;

    // keyboard:false — o Leaflet foca o próprio container do mapa ao clicar em
    // qualquer camada interativa (marcador, popup); como o <main> do dashboard
    // é overflow-hidden sem barra de rolagem visível, o navegador faz
    // scroll-into-view programático nele mesmo assim, empurrando o cabeçalho
    // para fora da viewport. Zoom (mouse/touch/botões) e cliques continuam
    // normais — só a navegação por setas do teclado no mapa é removida.
    const mapInstance = L.map(mapContainer.current, { zoomControl: true, keyboard: false }).setView([-30.0346, -51.2177], 7);
    map.current = mapInstance;

    // Quando a barra lateral recolhe ou expande, o container muda de largura sem
    // recarregar a página: o Leaflet precisa recalcular o tamanho para não deixar área cinza.
    const observer = typeof ResizeObserver !== 'undefined'
      ? new ResizeObserver(() => mapInstance.invalidateSize())
      : null;
    observer?.observe(mapContainer.current);

    return () => {
      observer?.disconnect();
      mapInstance.remove();
      map.current = null;
      markersRef.current = [];
    };
  }, []);

  // 2. Camadas de tiles do tema (também na montagem, logo após criar o mapa)
  useEffect(() => {
    const m = map.current;
    if (!m) return;
    const camadas = adicionarCamadasBase(m, mapTheme);
    return () => {
      camadas.forEach((camada) => camada.remove());
    };
  }, [mapTheme]);

  // 3. Cor da coropletia: votos do candidato e borda conforme o tema
  useEffect(() => {
    if (camadaCoropletica) aplicarEstiloCoropletico(camadaCoropletica, votosPorMunicipio, mapTheme);
  }, [camadaCoropletica, votosPorMunicipio, mapTheme]);

  // 4. Coropletia visível só nos modos Votação e Cruzada
  useEffect(() => {
    const m = map.current;
    if (m && camadaCoropletica) ajustarVisibilidadeCoropletica(m, camadaCoropletica, viewMode);
  }, [camadaCoropletica, viewMode]);

  // 5. Marcadores das lideranças, recriados quando a lista ou o modo mudam
  useEffect(() => {
    const m = map.current;
    if (!m) return;

    markersRef.current.forEach((marker) => m.removeLayer(marker));
    markersRef.current = [];

    // No modo "apenas votação", os pontos de lideranças ficam ocultos.
    if (viewMode === 'votacao') return;

    // Um pino por município, com contador quando há mais de uma liderança.
    // Antes, cada liderança recebia um deslocamento de ~20 m: no zoom do estado
    // esses pinos ficavam sobrepostos e pareciam um só.
    agruparPorMunicipio(liderancasEstaveis).forEach(({ mun, liderancas }) => {
      // keyboard:false — sem isso o Leaflet torna o marcador focável (tabindex)
      // e chama .focus() nele ao clicar; como o <main> do dashboard tem
      // overflow-hidden (ADR de layout fixo), o navegador faz scroll-into-view
      // programático ali mesmo sem barra de rolagem visível, empurrando o
      // cabeçalho/seletor de modo para fora da viewport ao abrir o popup.
      const marker = L.marker([Number(mun.latitude), Number(mun.longitude)], {
        icon: iconeLideranca(liderancas.length),
        keyboard: false,
      }).addTo(m);
      marker.bindPopup(
        liderancas.length === 1 ? popupLideranca(liderancas[0], mun) : popupMunicipio(mun, liderancas)
      );
      markersRef.current.push(marker);
    });
  }, [liderancasEstaveis, viewMode]);

  // 6. Enquadra o mapa para caber todas as lideranças, em vez de um centro/zoom fixo
  useEffect(() => {
    const m = map.current;
    if (!m) return;

    const pontos = pontosDasLiderancas(liderancasEstaveis);
    if (pontos.length === 0) return;

    const bounds = L.latLngBounds(pontos.map(({ mun }) => [Number(mun.latitude), Number(mun.longitude)] as [number, number]));
    m.fitBounds(bounds, { padding: [60, 60], maxZoom: 12 });
  }, [liderancasEstaveis]);

  return (
    <div className="w-full h-[420px] min-h-[420px] sm:h-[600px] sm:min-h-[600px] rounded-2xl overflow-hidden shadow-2xl border border-zinc-800 bg-zinc-950 relative">
      <div ref={mapContainer} className="w-full h-full" />

      {/* Controle de Mapa Base */}
      <div className="absolute top-2 right-2 sm:top-4 sm:right-4 z-[1000] flex bg-zinc-900/80 backdrop-blur-md rounded-xl p-1 border border-zinc-700/50 shadow-xl">
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
