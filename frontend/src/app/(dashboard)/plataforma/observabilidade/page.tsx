'use client';

import { ObservabilidadePlataforma } from '@/features/plataforma/ObservabilidadePlataforma';

export default function ObservabilidadePage() {
  return (
    <div className="w-full h-full p-4 sm:p-8 flex flex-col gap-6 overflow-y-auto">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">Observabilidade e SOC</h1>
        <p className="text-zinc-400 mt-1">Saúde dos serviços, alertas e trilha de acesso. Os registros são guardados por 6 meses.</p>
      </div>
      <ObservabilidadePlataforma />
    </div>
  );
}
