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

const IBGE_COORDS: Record<string, [number, number]> = {
  '4300034': [-54.1611, -31.8656], // Aceguá
  '4314902': [-51.2177, -30.0346], // Porto Alegre
  '4305108': [-51.1794, -29.1678], // Caxias do Sul
  '4314407': [-52.3426, -31.7654], // Pelotas
  '4304606': [-52.8122, -29.7186], // Canoas
  '4309209': [-50.9984, -29.9439], // Gravataí
  '4313409': [-51.1444, -29.6868], // Novo Hamburgo
};

export default function DashboardPage() {
  const [liderancas, setLiderancas] = useState<any[]>([]);

  useEffect(() => {
    async function loadLiderancas() {
      try {
        console.log('📡 Buscando lideranças da API...');
        const res = await api.get('/api/v1/gabinete/liderancas');
        console.log('✅ Resposta da API recebida:', res.data);

        const mapped = res.data.map((l: any) => {
          const coords = IBGE_COORDS[l.cd_ibge_7] || [-51.2177, -30.0346];
          return {
            ...l,
            longitude: coords[0],
            latitude: coords[1],
          };
        });

        console.log('🗺️ Dados mapeados para o mapa:', mapped);
        setLiderancas(mapped);
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