'use client';

import { useState } from 'react';
import { useProjetosLei, ProjetoLei } from '@/features/projetosLei/useProjetosLei';
import { BuscaExternaProjetosLei } from '@/features/projetosLei/BuscaExternaProjetosLei';
import { ProjetosLeiTable } from '@/features/projetosLei/ProjetosLeiTable';
import { ProjetoLeiDetailModal } from '@/features/projetosLei/ProjetoLeiDetailModal';
import { useAuthStore } from '@/stores/useAuthStore';

export default function ProjetosLeiPage() {
  const [projetoAberto, setProjetoAberto] = useState<ProjetoLei | null>(null);
  const {
    nomeBusca, setNomeBusca, resultadosExternos, fontesComErro, isBuscando, importandoChave, importar,
    projetosLei, isLoading, termo, setTermo, fonte, setFonte,
    page, setPage, totalPages, total, deleteProjetoLei,
    sincronizar, sincronizandoId, syncFeedback,
  } = useProjetosLei();
  const isAdmin = useAuthStore((state) => state.user?.role === 'admin');

  return (
    <div className="w-full h-full p-4 sm:p-8 flex flex-col gap-6 relative overflow-y-auto">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">Projetos de Lei</h1>
        <p className="text-zinc-400 mt-1">Busque pelo nome do parlamentar nas fontes oficiais e acompanhe a tramitação com sua equipe.</p>
      </div>

      <BuscaExternaProjetosLei
        nomeBusca={nomeBusca}
        onNomeBuscaChange={setNomeBusca}
        resultados={resultadosExternos}
        fontesComErro={fontesComErro}
        isBuscando={isBuscando}
        importandoChave={importandoChave}
        onImportar={importar}
      />

      <ProjetosLeiTable
        projetosLei={projetosLei}
        isLoading={isLoading}
        onAbrir={setProjetoAberto}
        onDelete={(pl) => deleteProjetoLei(pl.id_projeto_lei)}
        canDelete={isAdmin}
        onSincronizar={async (pl) => {
          const atualizado = await sincronizar(pl.id_projeto_lei);
          // Se o modal desta proposição estiver aberto, ele passa a mostrar a situação nova.
          if (atualizado && projetoAberto?.id_projeto_lei === pl.id_projeto_lei) setProjetoAberto(atualizado);
        }}
        sincronizandoId={sincronizandoId}
        syncFeedback={syncFeedback}
        termo={termo}
        onTermoChange={setTermo}
        fonte={fonte}
        onFonteChange={setFonte}
        page={page}
        totalPages={totalPages}
        total={total}
        onPageChange={setPage}
      />

      <ProjetoLeiDetailModal projetoLei={projetoAberto} onClose={() => setProjetoAberto(null)} />
    </div>
  );
}
