import { AlertTriangle } from 'lucide-react';

// Débito técnico registrado: a busca em fontes oficiais ainda não existe no backend.
// Remover este aviso quando a API oficial de emendas estiver ativa e as validações pendentes forem feitas.
export function AvisoDebitoEmendas() {
  return (
    <div
      role="note"
      className="flex items-start gap-2 px-3.5 py-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-sm"
    >
      <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
      <div className="space-y-1">
        <p className="font-semibold">Função em desenvolvimento — débito técnico</p>
        <p>
          A busca de emendas em fontes oficiais ainda não está disponível: a API correspondente está em desenvolvimento.
          Os registros atuais são cadastrados manualmente.
        </p>
        <p>
          Pendências conhecidas: o banco não valida a ordem dos valores (indicado ≥ empenhado ≥ pago) nem a lista de
          situações, e os indicadores ainda não incluem o valor liquidado previsto na ADR 010.
        </p>
      </div>
    </div>
  );
}
