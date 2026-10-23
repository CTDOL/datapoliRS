'use client';

import { usePlatformConfig } from '@/features/settings/usePlatformConfig';
import { PlataformaSettingsTab } from '@/features/settings/PlataformaSettingsTab';
import { ApisExternasSettings } from '@/features/settings/ApisExternasSettings';

export default function PlataformaConfiguracoesPage() {
  const { configuracoes, isLoading, isSubmitting, salvarConfiguracoes } = usePlatformConfig(true);

  return (
    <div className="w-full h-full p-4 sm:p-8 flex flex-col gap-6 overflow-y-auto">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">APIs e sistema</h1>
        <p className="text-zinc-400 mt-1">Configurações da instância, valem para todos os gabinetes.</p>
      </div>
      <ApisExternasSettings />
      <PlataformaSettingsTab configuracoes={configuracoes.filter((c) => c.categoria !== 'apis')} isLoading={isLoading} isSubmitting={isSubmitting} isAdmin={true} onSave={salvarConfiguracoes} />
    </div>
  );
}
