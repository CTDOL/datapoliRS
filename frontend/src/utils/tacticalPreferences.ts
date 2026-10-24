import type { MapViewMode } from '@/components/map/ElectionMap';
import { api } from '@/services/api';
import { useAuthStore, type PreferenciasUsuario } from '@/stores/useAuthStore';

/**
 * Preferências pessoais do Mapa Tático e das buscas. São gravadas no servidor
 * (PUT /api/v1/usuario/preferencias), então valem em qualquer navegador e
 * sobrevivem a um novo login. As leituras vêm do store, preenchido no login.
 */

export interface FontesLegislativas {
  alrs: boolean;
  camara: boolean;
  senado: boolean;
}

const PREFERENCIAS_PADRAO: PreferenciasUsuario = {
  mapa_padrao: 'liderancas',
  fontes_legislativas: { alrs: true, camara: true, senado: true },
};

function preferenciasAtuais(): PreferenciasUsuario {
  return { ...PREFERENCIAS_PADRAO, ...useAuthStore.getState().user?.preferencias };
}

/** Atualiza o store primeiro (a tela reage na hora) e grava no servidor. Se a gravação falhar, volta ao valor anterior. */
async function gravar(parcial: Partial<PreferenciasUsuario>): Promise<void> {
  const anterior = preferenciasAtuais();
  useAuthStore.getState().atualizarPreferencias(parcial);
  try {
    await api.put('/api/v1/usuario/preferencias', parcial);
  } catch (erro) {
    useAuthStore.getState().atualizarPreferencias(anterior);
    throw erro;
  }
}

export function getMapaPadrao(): MapViewMode {
  return preferenciasAtuais().mapa_padrao;
}

export function setMapaPadrao(mode: MapViewMode): Promise<void> {
  return gravar({ mapa_padrao: mode });
}

export function getFontesLegislativas(): FontesLegislativas {
  return preferenciasAtuais().fontes_legislativas;
}

export function setFontesLegislativas(fontes: FontesLegislativas): Promise<void> {
  return gravar({ fontes_legislativas: fontes });
}
