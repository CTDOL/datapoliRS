'use client';

import { Suspense } from 'react';
import { QuadroTarefas } from '@/features/tarefas/QuadroTarefas';

export default function TarefasPage() {
  return (
    <div className="w-full h-full p-4 sm:p-8 flex flex-col gap-6 overflow-y-auto">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">Tarefas</h1>
        <p className="text-zinc-400 mt-1">Andamento das tarefas do gabinete. Admin e operador registram comentários de execução.</p>
      </div>
      {/* useSearchParams exige Suspense no App Router para o build estático */}
      <Suspense fallback={null}>
        <QuadroTarefas />
      </Suspense>
    </div>
  );
}
