'use client';

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { api } from '@/services/api';

const ElectionMap = dynamic(() => import('@/components/map/ElectionMap'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-[600px] rounded-2xl border border-slate-800 bg-slate-950 flex items-center justify-center text-slate-500">
      Carregando mapa tático...
    </div>
  ),
});

import { LiderancaPoint } from '@/components/map/ElectionMap';

export default function DashboardPage() {
  const [liderancas, setLiderancas] = useState<LiderancaPoint[]>([]);

  useEffect(() => {
    async function loadLiderancas() {
      try {
        console.log('📡 Buscando lideranças da API...');
        const res = await api.get('/api/v1/gabinete/liderancas');
        console.log('✅ Resposta da API recebida:', res.data);
        setLiderancas(res.data);
      } catch (err) {
        console.error('❌ Erro ao buscar lideranças:', err);
      }
    }

    loadLiderancas();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Mapa Tático de Lideranças</h1>
        <p className="text-slate-400 text-sm">Geolocalização e distribuição de contatos de gabinete.</p>
      </div>

      <ElectionMap liderancas={liderancas} />
    </div>
  );
}