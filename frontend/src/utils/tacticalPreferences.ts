import type { MapViewMode } from '@/components/map/ElectionMap';

const MAPA_PADRAO_KEY = 'datapolirs:mapa-padrao';
const FONTES_LEGISLATIVAS_KEY = 'datapolirs:fontes-legislativas';

export interface FontesLegislativas {
  alrs: boolean;
  camara: boolean;
  senado: boolean;
}

const FONTES_PADRAO: FontesLegislativas = { alrs: true, camara: true, senado: true };

export function getMapaPadrao(): MapViewMode {
  if (typeof window === 'undefined') return 'liderancas';
  const stored = localStorage.getItem(MAPA_PADRAO_KEY);
  if (stored === 'liderancas' || stored === 'votacao' || stored === 'cruzada') return stored;
  return 'liderancas';
}

export function setMapaPadrao(mode: MapViewMode): void {
  localStorage.setItem(MAPA_PADRAO_KEY, mode);
}

export function getFontesLegislativas(): FontesLegislativas {
  if (typeof window === 'undefined') return FONTES_PADRAO;
  try {
    const stored = localStorage.getItem(FONTES_LEGISLATIVAS_KEY);
    if (!stored) return FONTES_PADRAO;
    return { ...FONTES_PADRAO, ...JSON.parse(stored) };
  } catch {
    return FONTES_PADRAO;
  }
}

export function setFontesLegislativas(fontes: FontesLegislativas): void {
  localStorage.setItem(FONTES_LEGISLATIVAS_KEY, JSON.stringify(fontes));
}
