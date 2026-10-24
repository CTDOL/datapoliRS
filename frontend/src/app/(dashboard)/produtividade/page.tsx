'use client';

import { useAuthStore } from '@/stores/useAuthStore';
import { PainelProdutividade } from '@/features/produtividade/PainelProdutividade';

export default function ProdutividadePage() {
  const isAdmin = useAuthStore((state) => state.user?.role === 'admin');

  return (
    <div className="w-full h-full p-4 sm:p-8 flex flex-col gap-6 overflow-y-auto">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">Visão geral</h1>
        <p className="text-zinc-400 mt-1">Painel de produtividade do gabinete.</p>
      </div>
      {isAdmin ? <PainelProdutividade /> : <p className="text-zinc-400">Acesso restrito à autoridade do gabinete (administrador).</p>}
    </div>
  );
}
