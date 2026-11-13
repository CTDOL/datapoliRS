'use client';

import { BalcaoCaixa } from '@/features/balcao/components/BalcaoCaixa';

export default function BalcaoPage() {
  return (
    <div className="flex h-full w-full flex-col gap-6 overflow-y-auto p-4 sm:p-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
          Balcão Inteligente
        </h1>
        <p className="mt-1 text-sm text-zinc-400">
          Triagem de demandas do portal público, timeline append-only e resolução com evidências.
        </p>
      </div>
      <BalcaoCaixa />
    </div>
  );
}

