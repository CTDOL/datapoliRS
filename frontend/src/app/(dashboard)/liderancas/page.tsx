'use client';

import { useState } from 'react';
import { Plus } from 'lucide-react';
import { useLiderancas } from '@/features/liderancas/useLiderancas';
import { LiderancasTable } from '@/features/liderancas/LiderancasTable';
import { LiderancaFormModal } from '@/features/liderancas/LiderancaFormModal';
import { Lideranca } from '@/features/liderancas/useLiderancas';
import { useAuthStore } from '@/stores/useAuthStore';

export default function LiderancasPage() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingLideranca, setEditingLideranca] = useState<Lideranca | null>(null);
  const {
    liderancas,
    isLoading,
    isSubmitting,
    termo,
    setTermo,
    filtroCidade,
    setFiltroCidade,
    filtroTipo,
    setFiltroTipo,
    page,
    setPage,
    totalPages,
    total,
    addLideranca,
    updateLideranca,
    uploadFoto,
    deleteLideranca,
  } = useLiderancas();
  const isAdmin = useAuthStore((state) => state.user?.role === 'admin');

  return (
    <div className="w-full h-full p-4 sm:p-8 flex flex-col relative">
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4 mb-6 sm:mb-8">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">Lideranças Políticas</h1>
          <p className="text-zinc-400 mt-1 text-sm sm:text-base">Gestão de contatos e influenciadores do Gabinete.</p>
        </div>
        <button
          onClick={() => {
            setEditingLideranca(null);
            setIsModalOpen(true);
          }}
          className="shrink-0 bg-purple-600 hover:bg-purple-500 text-white px-5 py-2.5 rounded-xl font-medium transition-all shadow-lg flex items-center justify-center gap-2 whitespace-nowrap"
        >
          <Plus className="w-5 h-5" />
          Adicionar Liderança
        </button>
      </div>

      <LiderancasTable
        liderancas={liderancas}
        isLoading={isLoading}
        onEdit={(lideranca) => {
          setEditingLideranca(lideranca);
          setIsModalOpen(true);
        }}
        onDelete={(lideranca) => deleteLideranca(lideranca.id_lideranca)}
        canDelete={isAdmin}
        termo={termo}
        onTermoChange={setTermo}
        filtroCidade={filtroCidade}
        onFiltroCidadeChange={setFiltroCidade}
        filtroTipo={filtroTipo}
        onFiltroTipoChange={setFiltroTipo}
        page={page}
        totalPages={totalPages}
        total={total}
        onPageChange={setPage}
      />

      <LiderancaFormModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setEditingLideranca(null);
        }}
        onSubmit={async (data) => {
          if (editingLideranca) {
            return await updateLideranca(editingLideranca.id_lideranca, data);
          } else {
            return await addLideranca(data);
          }
        }}
        onUploadFoto={uploadFoto}
        isSubmitting={isSubmitting}
        initialData={editingLideranca}
      />
    </div>
  );
}
