'use client';

import { GabinetesPlataforma } from '@/features/plataforma/GabinetesPlataforma';

export default function PlataformaPage() {
  return (
    <div className="w-full h-full p-4 sm:p-8 flex flex-col gap-6 overflow-y-auto">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">Gabinetes da plataforma</h1>
        <p className="text-zinc-400 mt-1">Criação, ativação e acesso dos gabinetes. Os dados de cada gabinete não são acessados por esta área.</p>
      </div>
      <GabinetesPlataforma />
    </div>
  );
}
