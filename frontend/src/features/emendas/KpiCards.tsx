import { FileText, Landmark, HandCoins, Wallet } from 'lucide-react';
import { EmendaKpis } from './useEmendas';

function formatMoney(value: string | number) {
  return Number(value).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 });
}

interface KpiCardsProps {
  kpis: EmendaKpis | null;
}

export function KpiCards({ kpis }: KpiCardsProps) {
  const cards = [
    {
      label: 'Total de Emendas',
      value: kpis ? String(kpis.total_emendas) : '—',
      icon: FileText,
      color: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
    },
    {
      label: 'Valor Indicado',
      value: kpis ? formatMoney(kpis.vl_total_indicado) : '—',
      icon: Landmark,
      color: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
    },
    {
      label: 'Valor Empenhado',
      value: kpis ? formatMoney(kpis.vl_total_empenhado) : '—',
      icon: HandCoins,
      color: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
    },
    {
      label: 'Valor Pago',
      value: kpis ? formatMoney(kpis.vl_total_pago) : '—',
      icon: Wallet,
      color: 'text-teal-400 bg-teal-500/10 border-teal-500/20',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map(({ label, value, icon: Icon, color }) => (
        <div key={label} className="bg-zinc-900/50 backdrop-blur-md border border-zinc-800 rounded-2xl p-5 flex items-center gap-4 shadow-xl">
          <div className={`w-12 h-12 rounded-xl flex items-center justify-center border ${color}`}>
            <Icon className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-zinc-400 uppercase tracking-wide font-semibold">{label}</p>
            <p className="text-xl font-bold text-white">{value}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
