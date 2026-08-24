'use client';

import { useEffect, useState } from 'react';
import { AlertTriangle, Cpu, Loader2, Save, ShieldAlert } from 'lucide-react';
import { ConfiguracaoItem } from './usePlatformConfig';

interface Props {
  configuracoes: ConfiguracaoItem[];
  isLoading: boolean;
  isSubmitting: boolean;
  isAdmin: boolean;
  onSave: (valores: Record<string, string>) => Promise<{ ok: true } | { ok: false; message: string }>;
}

const CATEGORIA_LABELS: Record<string, string> = {
  eleitoral: 'Ciclo Eleitoral',
  rate_limit: 'Rate Limiting das APIs',
  cache: 'Cache (TTL)',
};

const CATEGORIA_ORDER = ['eleitoral', 'rate_limit', 'cache'];

export function PlataformaSettingsTab({ configuracoes, isLoading, isSubmitting, isAdmin, onSave }: Props) {
  const [valores, setValores] = useState<Record<string, string>>({});
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  useEffect(() => {
    setTimeout(() => {
      const initial: Record<string, string> = {};
      configuracoes.forEach((item) => { initial[item.chave] = item.valor; });
      setValores(initial);
    }, 0);
  }, [configuracoes]);

  if (!isAdmin) {
    return (
      <div className="max-w-4xl flex flex-col items-center justify-center gap-3 py-16 text-center">
        <ShieldAlert className="w-8 h-8 text-zinc-600" />
        <p className="text-zinc-400">Apenas administradores podem ajustar as configurações da plataforma.</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24 text-zinc-500">
        <Loader2 className="w-6 h-6 animate-spin" />
      </div>
    );
  }

  const porCategoria = CATEGORIA_ORDER.map((categoria) => ({
    categoria,
    itens: configuracoes.filter((item) => item.categoria === categoria),
  })).filter((grupo) => grupo.itens.length > 0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFeedback(null);
    const result = await onSave(valores);
    setFeedback(
      result.ok
        ? { type: 'success', message: 'Configurações aplicadas — sem precisar reiniciar o sistema.' }
        : { type: 'error', message: result.message }
    );
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-4xl space-y-8">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-purple-500/10 rounded-xl flex items-center justify-center border border-purple-500/20">
          <Cpu className="w-5 h-5 text-purple-400" />
        </div>
        <div>
          <h2 className="text-lg font-bold text-white">APIs & Sistema</h2>
          <p className="text-sm text-zinc-400">Ajustes finos globais — afetam toda a plataforma, não só este gabinete.</p>
        </div>
      </div>

      <div className="flex items-start gap-3 px-4 py-3 rounded-xl border border-amber-500/20 bg-amber-500/5">
        <AlertTriangle className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />
        <p className="text-xs text-amber-200/80">
          Estes parâmetros são compartilhados por todos os gabinetes desta instância. Uma alteração aqui vale para todo mundo,
          não apenas para o seu.
        </p>
      </div>

      {porCategoria.map((grupo) => (
        <div key={grupo.categoria}>
          <label className="block text-xs font-semibold text-zinc-300 uppercase mb-2">
            {CATEGORIA_LABELS[grupo.categoria] ?? grupo.categoria}
          </label>
          <div className="rounded-2xl border border-zinc-800 divide-y divide-zinc-800/60 overflow-hidden">
            {grupo.itens.map((item) => (
              <div key={item.chave} className="flex items-center justify-between gap-4 px-4 py-3 bg-zinc-950">
                <div className="min-w-0">
                  <p className="text-sm text-zinc-200">{item.descricao}</p>
                  <p className="text-xs text-zinc-500 font-mono mt-0.5">{item.chave}</p>
                </div>
                <input
                  type={item.tipo === 'int' ? 'number' : 'text'}
                  value={valores[item.chave] ?? ''}
                  onChange={(e) => setValores({ ...valores, [item.chave]: e.target.value })}
                  className="w-40 shrink-0 bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-white text-sm outline-none focus:ring-2 focus:ring-purple-500/50 text-right"
                />
              </div>
            ))}
          </div>
        </div>
      ))}

      {feedback && (
        <p className={`text-sm ${feedback.type === 'success' ? 'text-emerald-400' : 'text-red-400'}`}>{feedback.message}</p>
      )}

      <button
        type="submit"
        disabled={isSubmitting}
        className="bg-purple-600 hover:bg-purple-500 text-white px-5 py-2.5 rounded-xl font-medium transition-all shadow-lg flex items-center gap-2 disabled:opacity-70"
      >
        {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
        Salvar Alterações
      </button>
    </form>
  );
}
