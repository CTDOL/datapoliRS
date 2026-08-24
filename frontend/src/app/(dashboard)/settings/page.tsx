'use client';

import { useState } from 'react';
import { Landmark, Users, MapPin, Lock, Cpu } from 'lucide-react';
import { useSettings } from '@/features/settings/useSettings';
import { usePlatformConfig } from '@/features/settings/usePlatformConfig';
import { MandatoSettingsTab } from '@/features/settings/MandatoSettingsTab';
import { EquipeSettingsTab } from '@/features/settings/EquipeSettingsTab';
import { PreferenciasSettingsTab } from '@/features/settings/PreferenciasSettingsTab';
import { SegurancaSettingsTab } from '@/features/settings/SegurancaSettingsTab';
import { PlataformaSettingsTab } from '@/features/settings/PlataformaSettingsTab';
import { useAuthStore } from '@/stores/useAuthStore';

type TabKey = 'mandato' | 'equipe' | 'preferencias' | 'seguranca' | 'plataforma';

const TABS: { key: TabKey; label: string; icon: typeof Landmark }[] = [
  { key: 'mandato', label: 'Perfil do Mandato', icon: Landmark },
  { key: 'equipe', label: 'Equipe & Acessos', icon: Users },
  { key: 'preferencias', label: 'Preferências Táticas', icon: MapPin },
  { key: 'seguranca', label: 'Segurança & Dados', icon: Lock },
  { key: 'plataforma', label: 'APIs & Sistema', icon: Cpu },
];

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<TabKey>('mandato');
  const user = useAuthStore((state) => state.user);
  const isAdmin = user?.role === 'admin';

  const {
    profile,
    options,
    team,
    isLoadingProfile,
    isLoadingTeam,
    isSubmitting,
    updateProfile,
    inviteMember,
    updateMember,
    changePassword,
    exportGabineteData,
  } = useSettings(isAdmin);

  const { configuracoes, isLoading: isLoadingConfig, isSubmitting: isSubmittingConfig, salvarConfiguracoes } = usePlatformConfig(isAdmin);

  return (
    <div className="w-full h-full p-8 flex flex-col gap-6 overflow-y-auto">
      <div>
        <h1 className="text-3xl font-bold text-white tracking-tight">Configurações do Gabinete</h1>
        <p className="text-zinc-400 mt-1">Perfil do mandato, equipe, preferências e segurança.</p>
      </div>

      <div className="flex gap-2 border-b border-zinc-800/60">
        {TABS.map((tab) => {
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-all -mb-px ${
                isActive
                  ? 'text-purple-400 border-purple-500'
                  : 'text-zinc-400 border-transparent hover:text-white'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      <div className="backdrop-blur-xl bg-zinc-900/40 border border-zinc-800/60 rounded-3xl p-8 shadow-2xl">
        {activeTab === 'mandato' && (
          <MandatoSettingsTab
            profile={profile}
            options={options}
            isLoading={isLoadingProfile}
            isSubmitting={isSubmitting}
            isAdmin={isAdmin}
            onSave={updateProfile}
          />
        )}
        {activeTab === 'equipe' && (
          <EquipeSettingsTab
            team={team}
            isLoading={isLoadingTeam}
            isSubmitting={isSubmitting}
            isAdmin={isAdmin}
            currentUserEmail={user?.email ?? null}
            onInvite={inviteMember}
            onUpdateMember={updateMember}
          />
        )}
        {activeTab === 'preferencias' && <PreferenciasSettingsTab />}
        {activeTab === 'seguranca' && (
          <SegurancaSettingsTab
            isAdmin={isAdmin}
            isSubmitting={isSubmitting}
            onChangePassword={changePassword}
            onExportData={exportGabineteData}
          />
        )}
        {activeTab === 'plataforma' && (
          <PlataformaSettingsTab
            configuracoes={configuracoes}
            isLoading={isLoadingConfig}
            isSubmitting={isSubmittingConfig}
            isAdmin={isAdmin}
            onSave={salvarConfiguracoes}
          />
        )}
      </div>
    </div>
  );
}
