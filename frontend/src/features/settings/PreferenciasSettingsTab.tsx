'use client';

import { useEffect, useState } from 'react';
import { Check, MapPin } from 'lucide-react';
import type { MapViewMode } from '@/components/map/ElectionMap';
import { api } from '@/services/api';
import {
  FontesLegislativas,
  getFontesLegislativas,
  getMapaPadrao,
  setFontesLegislativas,
  setMapaPadrao,
} from '@/utils/tacticalPreferences';

const VIEW_MODE_BASE_LABELS: Record<MapViewMode, string> = {
  liderancas: 'Lideranças',
  votacao: 'Votação',
  cruzada: 'Visão Cruzada',
};
const VIEW_MODE_ORDER: MapViewMode[] = ['liderancas', 'votacao', 'cruzada'];

const FONTE_LABELS: { key: keyof FontesLegislativas; label: string }[] = [
  { key: 'alrs', label: 'ALRS — Assembleia Legislativa do RS' },
  { key: 'camara', label: 'Câmara dos Deputados' },
  { key: 'senado', label: 'Senado Federal' },
];

export function PreferenciasSettingsTab() {
  const [mapaPadrao, setMapaPadraoState] = useState<MapViewMode>('liderancas');
  const [fontes, setFontesState] = useState<FontesLegislativas>({ alrs: true, camara: true, senado: true });
  const [saved, setSaved] = useState(false);
  const [anoEleicaoRecente, setAnoEleicaoRecente] = useState<number | null>(null);

  useEffect(() => {
    setTimeout(() => {
      setMapaPadraoState(getMapaPadrao());
      setFontesState(getFontesLegislativas());
    }, 0);
  }, []);

  // Ano do pleito mais recente com dados carregados — evita hardcodar "2022" no
  // rótulo: quando um novo pleito (ex: 2026) for ingerido, atualiza sozinho.
  useEffect(() => {
    api.get('/api/v1/eleicoes')
      .then((response) => {
        const eleicoes = response.data as { ano_eleicao: number }[];
        if (eleicoes.length > 0) setAnoEleicaoRecente(eleicoes[0].ano_eleicao);
      })
      .catch((error) => console.error('Erro ao buscar pleitos disponíveis', error));
  }, []);

  const viewModeOptions = VIEW_MODE_ORDER.map((value) => ({
    value,
    label: value === 'votacao' && anoEleicaoRecente
      ? `${VIEW_MODE_BASE_LABELS[value]} ${anoEleicaoRecente}`
      : VIEW_MODE_BASE_LABELS[value],
  }));

  const flashSaved = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 1500);
  };

  const handleMapaPadraoChange = (value: MapViewMode) => {
    setMapaPadraoState(value);
    setMapaPadrao(value);
    flashSaved();
  };

  const handleFonteToggle = (key: keyof FontesLegislativas) => {
    const updated = { ...fontes, [key]: !fontes[key] };
    setFontesState(updated);
    setFontesLegislativas(updated);
    flashSaved();
  };

  return (
    <div className="max-w-2xl space-y-8">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-purple-500/10 rounded-xl flex items-center justify-center border border-purple-500/20">
          <MapPin className="w-5 h-5 text-purple-400" />
        </div>
        <div>
          <h2 className="text-lg font-bold text-white">Preferências Táticas & Mapa</h2>
          <p className="text-sm text-zinc-400">Salvas neste navegador.</p>
        </div>
      </div>

      <div>
        <label className="block text-xs font-semibold text-zinc-300 uppercase mb-2">Modo padrão do Mapa Tático ao entrar</label>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {viewModeOptions.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => handleMapaPadraoChange(opt.value)}
              className={`px-4 py-3 rounded-xl border text-sm font-medium transition-all ${
                mapaPadrao === opt.value
                  ? 'bg-purple-500/10 text-purple-400 border-purple-500/30'
                  : 'bg-zinc-950 text-zinc-400 border-zinc-800 hover:border-zinc-700'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-xs font-semibold text-zinc-300 uppercase mb-2">Fontes legislativas ativas no monitoramento</label>
        <div className="space-y-2">
          {FONTE_LABELS.map(({ key, label }) => (
            <label
              key={key}
              className="flex items-center gap-3 px-4 py-3 rounded-xl border border-zinc-800 bg-zinc-950 cursor-pointer hover:border-zinc-700 transition-colors"
            >
              <input
                type="checkbox"
                checked={fontes[key]}
                onChange={() => handleFonteToggle(key)}
                className="sr-only"
              />
              <span className={`w-5 h-5 rounded-md border flex items-center justify-center ${fontes[key] ? 'bg-purple-600 border-purple-500' : 'border-zinc-700'}`}>
                {fontes[key] && <Check className="w-3.5 h-3.5 text-white" />}
              </span>
              <span className="text-sm text-zinc-200">{label}</span>
            </label>
          ))}
        </div>
      </div>

      {saved && <p className="text-sm text-emerald-400">Preferência salva.</p>}
    </div>
  );
}
