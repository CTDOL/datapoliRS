'use client';

import { useState } from 'react';
import { Plus } from 'lucide-react';
import { useLiderancas } from '@/features/liderancas/useLiderancas';
import { LiderancasTable } from '@/features/liderancas/LiderancasTable';
import { LiderancaFormModal } from '@/features/liderancas/LiderancaFormModal';

export default function LiderancasPage() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { liderancas, isLoading, isSubmitting, addLideranca } = useLiderancas();

  return (
    <div className="w-full h-full p-8 flex flex-col relative">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Lideranças Políticas</h1>
          <p className="text-slate-400 mt-1">Gestão de contatos e influenciadores do Gabinete.</p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="bg-blue-600 hover:bg-blue-500 text-white px-5 py-2.5 rounded-xl font-medium transition-all shadow-lg flex items-center gap-2"
        >
          <Plus className="w-5 h-5" />
          Adicionar Liderança
        </button>
      </div>

      <LiderancasTable liderancas={liderancas} isLoading={isLoading} />
      
      <LiderancaFormModal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
        onSubmit={addLideranca} 
        isSubmitting={isSubmitting} 
      />
    </div>
  );
}