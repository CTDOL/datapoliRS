'use client';

import { useEffect, useState } from 'react';
import { Loader2, Landmark, Save } from 'lucide-react';
import { FormOptions, TenantProfile, TenantProfileUpdate } from './useSettings';

interface Props {
  profile: TenantProfile | null;
  options: FormOptions | null;
  isLoading: boolean;
  isSubmitting: boolean;
  isAdmin: boolean;
  onSave: (data: TenantProfileUpdate) => Promise<boolean>;
}

export function MandatoSettingsTab({ profile, options, isLoading, isSubmitting, isAdmin, onSave }: Props) {
  const [nmMandato, setNmMandato] = useState('');
  const [cdCargo, setCdCargo] = useState<string>('');
  const [nrPartido, setNrPartido] = useState<string>('');
  const [cdIbgeBase, setCdIbgeBase] = useState<string>('');
  const [feedback, setFeedback] = useState<'idle' | 'success' | 'error'>('idle');

  useEffect(() => {
    if (!profile) return;
    setTimeout(() => {
      setNmMandato(profile.nm_mandato);
      setCdCargo(profile.cd_cargo != null ? String(profile.cd_cargo) : '');
      setNrPartido(profile.nr_partido != null ? String(profile.nr_partido) : '');
      setCdIbgeBase(profile.cd_ibge_base || '');
    }, 0);
  }, [profile]);

  if (isLoading || !profile) {
    return (
      <div className="flex items-center justify-center py-24 text-zinc-500">
        <Loader2 className="w-6 h-6 animate-spin" />
      </div>
    );
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFeedback('idle');
    const success = await onSave({
      nm_mandato: nmMandato,
      cd_cargo: cdCargo ? Number(cdCargo) : null,
      nr_partido: nrPartido ? Number(nrPartido) : null,
      cd_ibge_base: cdIbgeBase || null,
    });
    setFeedback(success ? 'success' : 'error');
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-2xl space-y-5">
      <div className="flex items-center gap-3 mb-2">
        <div className="w-10 h-10 bg-purple-500/10 rounded-xl flex items-center justify-center border border-purple-500/20">
          <Landmark className="w-5 h-5 text-purple-400" />
        </div>
        <div>
          <h2 className="text-lg font-bold text-white">Perfil do Mandato</h2>
          <p className="text-sm text-zinc-400">Identificação institucional do gabinete.</p>
        </div>
      </div>

      <div>
        <label className="block text-xs font-semibold text-zinc-300 uppercase mb-1.5">Nome do Mandato</label>
        <input
          type="text"
          required
          minLength={3}
          disabled={!isAdmin}
          value={nmMandato}
          onChange={(e) => setNmMandato(e.target.value)}
          className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-white outline-none focus:ring-2 focus:ring-purple-500/50 disabled:opacity-60 disabled:cursor-not-allowed"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-semibold text-zinc-300 uppercase mb-1.5">Cargo Eletivo</label>
          <select
            disabled={!isAdmin}
            value={cdCargo}
            onChange={(e) => setCdCargo(e.target.value)}
            className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-white outline-none appearance-none focus:ring-2 focus:ring-purple-500/50 disabled:opacity-60 disabled:cursor-not-allowed"
          >
            <option value="">Não especificado</option>
            {options?.cargos.map((c) => (
              <option key={c.cd_cargo} value={c.cd_cargo}>{c.ds_cargo}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs font-semibold text-zinc-300 uppercase mb-1.5">Partido Político</label>
          <select
            disabled={!isAdmin}
            value={nrPartido}
            onChange={(e) => setNrPartido(e.target.value)}
            className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-white outline-none appearance-none focus:ring-2 focus:ring-purple-500/50 disabled:opacity-60 disabled:cursor-not-allowed"
          >
            <option value="">Não especificado</option>
            {options?.partidos.map((p) => (
              <option key={p.nr_partido} value={p.nr_partido}>{p.sg_partido} ({p.nr_partido})</option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <label className="block text-xs font-semibold text-zinc-300 uppercase mb-1.5">Município-Base</label>
        <select
          disabled={!isAdmin}
          value={cdIbgeBase}
          onChange={(e) => setCdIbgeBase(e.target.value)}
          className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-white outline-none appearance-none focus:ring-2 focus:ring-purple-500/50 disabled:opacity-60 disabled:cursor-not-allowed"
        >
          <option value="">Não especificado</option>
          {options?.municipios.map((m) => (
            <option key={m.cd_ibge_7} value={m.cd_ibge_7}>{m.nm_municipio}</option>
          ))}
        </select>
      </div>

      {!isAdmin && (
        <p className="text-xs text-zinc-500">Apenas administradores podem editar o perfil do mandato.</p>
      )}

      {feedback === 'success' && <p className="text-sm text-emerald-400">Perfil atualizado com sucesso.</p>}
      {feedback === 'error' && <p className="text-sm text-red-400">Não foi possível salvar as alterações.</p>}

      {isAdmin && (
        <button
          type="submit"
          disabled={isSubmitting}
          className="bg-purple-600 hover:bg-purple-500 text-white px-5 py-2.5 rounded-xl font-medium transition-all shadow-lg flex items-center gap-2 disabled:opacity-70"
        >
          {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
          Salvar Alterações
        </button>
      )}
    </form>
  );
}
