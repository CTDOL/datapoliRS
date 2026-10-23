import L from 'leaflet';
import { buildWhatsappLink } from '@/utils/whatsapp';
import type { LiderancaPoint, MapViewMode, MunicipioAtuacaoPoint } from './ElectionMap';

export type MapTheme = 'dark' | 'light';

// Tiles raster: Esri Canvas (gratuito, sem API key). O CARTO passou a
// exigir API key nos endpoints basemaps.cartocdn.com/{dark,light}_all —
// substituído para não depender de credencial paga em ambiente local.
// Esri separa o canvas base dos rótulos (nomes de cidade) em dois
// serviços de tile distintos — "Base" sozinho renderiza um mapa em
// branco/cinza sem nenhum nome; "Reference" é a camada transparente de
// labels que precisa ser empilhada por cima.
const TILE_URLS: Record<MapTheme, string> = {
  dark: 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
  light: 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}',
};
const LABEL_URLS: Record<MapTheme, string> = {
  dark: 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}',
  light: 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Reference/MapServer/tile/{z}/{y}/{x}',
};

const SEM_VOTOS_COR = 'rgba(148, 163, 184, 0.06)';

/** Canvas base + camada de rótulos do tema. Devolve as duas para a troca de tema removê-las. */
export function adicionarCamadasBase(mapa: L.Map, tema: MapTheme): L.TileLayer[] {
  const base = L.tileLayer(TILE_URLS[tema], {
    maxZoom: 16,
    attribution: '&copy; Esri, &copy; OpenStreetMap',
  }).addTo(mapa);
  const rotulos = L.tileLayer(LABEL_URLS[tema], {
    maxZoom: 16,
    pane: 'shadowPane', // acima dos tiles base, abaixo dos vetores (overlayPane)
  }).addTo(mapa);
  return [base, rotulos];
}

// Borda branca translúcida (0.2 alpha) some contra o basemap claro do tema
// Light — precisa de um traço escuro ali para as divisas dos municípios
// ficarem visíveis; no tema Dark o branco translúcido já contrasta bem.
function corDaBorda(tema: MapTheme): string {
  return tema === 'light' ? 'rgba(15, 23, 42, 0.35)' : 'rgba(255, 255, 255, 0.2)';
}

function corCoropletica(votos: number, maxVotos: number): string {
  if (!votos) return SEM_VOTOS_COR;
  const fracao = votos / maxVotos;
  if (fracao > 0.75) return '#4c1d95';
  if (fracao > 0.5) return '#6d28d9';
  if (fracao > 0.25) return '#7c3aed';
  if (fracao > 0.1) return '#a78bfa';
  if (fracao > 0.02) return '#c4b5fd';
  return '#ede9fe';
}

/** Pinta cada município pela fração dos votos do candidato em relação ao município com mais votos. */
export function aplicarEstiloCoropletico(camada: L.GeoJSON, votos: Record<string, number>, tema: MapTheme) {
  const valores = Object.values(votos);
  const maxVotos = valores.length > 0 ? Math.max(1, ...valores) : 1;
  camada.setStyle((feature) => {
    const ibgeId = (feature?.properties as { id?: string } | undefined)?.id;
    const v = (ibgeId && votos[ibgeId]) || 0;
    return {
      fillColor: corCoropletica(v, maxVotos),
      weight: 0.5,
      color: corDaBorda(tema),
      opacity: 1,
      fillOpacity: 0.8,
    };
  });
}

/** A coropletia só aparece nos modos que mostram votação. */
export function ajustarVisibilidadeCoropletica(mapa: L.Map, camada: L.GeoJSON, modo: MapViewMode) {
  const deveMostrar = modo === 'votacao' || modo === 'cruzada';
  const estaNoMapa = mapa.hasLayer(camada);
  if (deveMostrar && !estaNoMapa) camada.addTo(mapa);
  if (!deveMostrar && estaNoMapa) mapa.removeLayer(camada);
}

/** Um ponto por (liderança, município com coordenadas): uma liderança pode atuar em vários. */
export function pontosDasLiderancas(liderancas: LiderancaPoint[]) {
  return liderancas.flatMap((l) =>
    (l.municipios || [])
      .filter((mun) => mun.latitude && mun.longitude)
      .map((mun) => ({ l, mun }))
  );
}

export interface GrupoMunicipio {
  mun: MunicipioAtuacaoPoint;
  liderancas: LiderancaPoint[];
}

/** Um grupo por município: lideranças do mesmo município dividem o mesmo pino, em vez de se sobreporem. */
export function agruparPorMunicipio(liderancas: LiderancaPoint[]): GrupoMunicipio[] {
  const grupos = new Map<string, GrupoMunicipio>();
  for (const { l, mun } of pontosDasLiderancas(liderancas)) {
    const grupo = grupos.get(mun.cd_ibge_7);
    if (!grupo) {
      grupos.set(mun.cd_ibge_7, { mun, liderancas: [l] });
    } else if (!grupo.liderancas.includes(l)) {
      grupo.liderancas.push(l);
    }
  }
  return [...grupos.values()];
}

// Nome, telefone e URL da foto vêm do cadastro do gabinete e entram em HTML
// cru do popup do Leaflet: sem escape, um nome com <img onerror=...> executaria
// script no navegador de quem abrisse o popup.
function escaparHtml(texto: string): string {
  return texto
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// Elemento externo: é o que o Leaflet posiciona via transform inline.
// Não pode receber a propriedade CSS `scale` (via hover:scale-*) aqui — no
// Tailwind v4, `scale` é composto ENVOLVENDO o transform inline do Leaflet,
// amplificando também o deslocamento, não só o tamanho.
export function iconeLideranca(quantidade = 1): L.DivIcon {
  const contador = quantidade > 1
    ? `<span class="absolute -top-2 -right-2 min-w-[18px] h-[18px] px-1 rounded-full bg-white text-sky-700 text-[10px] font-bold flex items-center justify-center shadow">${quantidade}</span>`
    : '';
  return L.divIcon({
    className: '',
    html: `
      <div class="lideranca-marker relative w-4 h-4 cursor-pointer">
        <div class="w-full h-full bg-sky-500 border-2 border-white rounded-full shadow-[0_0_10px_rgba(14,165,233,0.8)] hover:scale-125 transition-transform"></div>
        ${contador}
      </div>
    `,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
  });
}

/** Popup de um pino com mais de uma liderança: uma linha por liderança, com o mesmo escape do popup individual. */
export function popupMunicipio(mun: MunicipioAtuacaoPoint, liderancas: LiderancaPoint[]): string {
  const itens = liderancas
    .map(
      (l) => `
      <div style="padding:6px 0; border-top:1px solid #e2e8f0; overflow:hidden;">
        ${l.ds_foto_url
          ? `<img src="${escaparHtml(l.ds_foto_url)}" alt="${escaparHtml(l.nm_completo)}" style="width:36px; height:36px; border-radius:9999px; object-fit:cover; float:left; margin-right:8px;" />`
          : ''}
        <strong style="color:#0284c7; font-size:13px;">${escaparHtml(l.nm_completo)}</strong><br/>
        <span style="font-size:12px;">Influência: <b>${escaparHtml(l.tp_influencia || '')}</b></span>
        ${l.nr_telefone ? `<br/><span style="font-size:12px; color:#334155;">📞 ${escaparHtml(l.nr_telefone)}</span>` : ''}
      </div>`
    )
    .join('');

  return `
    <div style="color:#0f172a; padding:4px; font-family:sans-serif; min-width:200px;">
      <div style="font-size:12px; color:#64748b;">${escaparHtml(mun.nm_municipio || '')} · ${liderancas.length} lideranças</div>
      ${itens}
    </div>
  `;
}

export function popupLideranca(l: LiderancaPoint, mun: MunicipioAtuacaoPoint): string {
  const whatsappLink = l.nr_telefone ? buildWhatsappLink(l.nr_telefone) : null;
  const telefoneHtml = l.nr_telefone
    ? `
      <div style="margin-top:8px; padding-top:8px; border-top:1px solid #e2e8f0; display:flex; align-items:center; justify-content:space-between; gap:8px;">
        <span style="font-size:12px; color:#334155;">📞 ${escaparHtml(l.nr_telefone)}</span>
        ${whatsappLink
          ? `<a href="${escaparHtml(whatsappLink)}" target="_blank" rel="noopener noreferrer"
               style="display:inline-flex; align-items:center; gap:4px; background:#25D366; color:#fff; font-size:11px; font-weight:600; padding:4px 10px; border-radius:9999px; text-decoration:none; white-space:nowrap;">
               WhatsApp
             </a>`
          : ''}
      </div>`
    : '';

  const fotoHtml = l.ds_foto_url
    ? `<img src="${escaparHtml(l.ds_foto_url)}" alt="${escaparHtml(l.nm_completo)}" style="width:48px; height:48px; border-radius:9999px; object-fit:cover; float:left; margin-right:10px;" />`
    : '';

  return `
    <div style="color:#0f172a; padding:4px; font-family:sans-serif; min-width:200px; overflow:hidden;">
      ${fotoHtml}
      <strong style="color:#0284c7; font-size:14px;">${escaparHtml(l.nm_completo)}</strong><br/>
      <span style="font-size:12px;">Influência: <b>${escaparHtml(l.tp_influencia || '')}</b></span><br/>
      <span style="color:#64748b; font-size:11px;">${escaparHtml(mun.nm_municipio || '')}</span>
      ${telefoneHtml}
    </div>
  `;
}
