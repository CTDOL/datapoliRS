'use client';

import { useState } from 'react';
import { Plus } from 'lucide-react';
import { useEmendas } from '@/features/emendas/useEmendas';
import { EmendasTable } from '@/features/emendas/EmendasTable';
import { EmendaFormModal } from '@/features/emendas/EmendaFormModal';
import { KpiCards } from '@/features/emendas/KpiCards';
import { Emenda } from '@/features/emendas/useEmendas';
import { useAuthStore } from '@/stores/useAuthStore';

export default function EmendasPage() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingEmenda, setEditingEmenda] = useState<Emenda | null>(null);
  const {
    emendas,
    kpis,
    isLoading,
    isSubmitting,
    termo,
    setTermo,
    anoExercicio,
    setAnoExercicio,
    tpSituacao,
    setTpSituacao,
    page,
    setPage,
    totalPages,
    total,
    addEmenda,
    updateEmenda,
    deleteEmenda,
  } = useEmendas();
  const isAdmin = useAuthStore((state) => state.user?.role === 'admin');

  return (
    <div className="w-full h-full p-8 flex flex-col gap-6 relative overflow-y-auto">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Emendas Orçamentárias</h1>
          <p className="text-zinc-400 mt-1">Acompanhamento de indicações, empenhos e pagamentos do mandato.</p>
        </div>
        <button
          onClick={() => {
            setEditingEmenda(null);
            setIsModalOpen(true);
          }}
          className="bg-purple-600 hover:bg-purple-500 text-white px-5 py-2.5 rounded-xl font-medium transition-all shadow-lg flex items-center gap-2"
        >
          <Plus className="w-5 h-5" />
          Nova Emenda
        </button>
      </div>

      <KpiCards kpis={kpis} />

      <EmendasTable
        emendas={emendas}
        isLoading={isLoading}
        onEdit={(emenda) => {
          setEditingEmenda(emenda);
          setIsModalOpen(true);
        }}
        onDelete={(emenda) => deleteEmenda(emenda.id_emenda)}
        canDelete={isAdmin}
        termo={termo}
        onTermoChange={setTermo}
        anoExercicio={anoExercicio}
        onAnoChange={setAnoExercicio}
        tpSituacao={tpSituacao}
        onSituacaoChange={setTpSituacao}
        page={page}
        totalPages={totalPages}
        total={total}
        onPageChange={setPage}
      />

      <EmendaFormModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setEditingEmenda(null);
        }}
        onSubmit={async (data) => {
          if (editingEmenda) {
            return await updateEmenda(editingEmenda.id_emenda, data);
          } else {
            return await addEmenda(data);
          }
        }}
        isSubmitting={isSubmitting}
        initialData={editingEmenda}
      />
    </div>
  );
}
