'use client';

import { ManutencaoDados } from '@/features/manutencao/ManutencaoDados';
import { useAuthStore } from '@/stores/useAuthStore';

export default function ManutencaoPage() {
  const isSuperAdmin = useAuthStore((state) => state.user?.role === 'super_admin');

  return (
    <div className="w-full h-full p-4 sm:p-8 flex flex-col gap-6 relative overflow-y-auto">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">Manutenção de Dados</h1>
        <p className="text-zinc-400 mt-1">Saúde dos dados eleitorais e histórico das cargas do TSE.</p>
      </div>
      {isSuperAdmin ? <ManutencaoDados /> : <p className="text-zinc-400">Acesso restrito ao super-admin da plataforma.</p>}
    </div>
  );
}
