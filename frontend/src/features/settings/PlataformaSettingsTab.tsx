'use client';

import { useEffect, useState } from 'react';
import { AlertTriangle, Loader2, Save, ShieldAlert } from 'lucide-react';
import { ConfiguracaoItem } from './usePlatformConfig';
import { CHAVES_SOMENTE_LEITURA, GRUPOS_API, ROTULOS } from './configuracoesPorApi';

interface Props {
  configuracoes: ConfiguracaoItem[];
  isLoading: boolean;
  isSubmitting: boolean;
  isAdmin: boolean;
  onSave: (valores: Record<string, string>) => Promise<{ ok: true } | { ok: false; message: string }>;
}

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

  // Uma seção por API/módulo. Chave nova que ainda não está mapeada cai em "Outras", para não sumir da tela.
  const chavesMapeadas = new Set(GRUPOS_API.flatMap((g) => g.chaves));
  const secoes = [
    ...GRUPOS_API.map((grupo) => ({
      ...grupo,
      itens: configuracoes.filter((item) => grupo.chaves.includes(item.chave)),
    })),
    {
      id: 'outras',
      titulo: 'Outras',
      descricao: 'Configurações sem seção própria.',
      chaves: [],
      itens: configuracoes.filter((item) => !chavesMapeadas.has(item.chave)),
    },
  ].filter((secao) => secao.itens.length > 0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFeedback(null);
    const editaveis = Object.fromEntries(
      Object.entries(valores).filter(([chave]) => !CHAVES_SOMENTE_LEITURA.includes(chave)),
    );
    const result = await onSave(editaveis);
    setFeedback(
      result.ok
        ? { type: 'success', message: 'Configurações aplicadas — sem precisar reiniciar o sistema.' }
        : { type: 'error', message: result.message }
    );
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-4xl space-y-8">
      <div className="flex items-start gap-3 px-4 py-3 rounded-xl border border-amber-500/20 bg-amber-500/5">
        <AlertTriangle className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />
        <p className="text-xs text-amber-200/80">Esta configuração vale para todos os gabinetes.</p>
      </div>

      {secoes.map((secao) => (
        <section key={secao.id} aria-labelledby={`secao-${secao.id}`}>
          <h3 id={`secao-${secao.id}`} className="text-base font-semibold text-white">{secao.titulo}</h3>
          <p className="text-sm text-zinc-400 mt-1 mb-3">{secao.descricao}</p>
          <div className="rounded-2xl border border-zinc-800 divide-y divide-zinc-800/60 overflow-hidden">
            {secao.itens.map((item) => {
              const rotulo = ROTULOS[item.chave];
              const texto = rotulo?.texto ?? item.descricao;
              const ajuda = rotulo?.ajuda?.(valores[item.chave] ?? item.valor);
              return (
              <div key={item.chave} className="flex items-center justify-between gap-4 px-4 py-3 bg-zinc-950">
                <div className="min-w-0">
                  <p className="text-sm text-zinc-200">{texto}</p>
                  {ajuda && <p className="text-xs text-zinc-500 mt-0.5">{ajuda}</p>}
                  <details className="mt-1 text-xs text-zinc-600">
                    <summary className="cursor-pointer">Detalhes técnicos</summary>
                    <p className="font-mono mt-1">{item.chave}</p>
                  </details>
                </div>
                <input
                  type={item.tipo === 'int' ? 'number' : 'text'}
                  aria-label={texto}
                  readOnly={CHAVES_SOMENTE_LEITURA.includes(item.chave)}
                  value={valores[item.chave] ?? ''}
                  onChange={(e) => setValores({ ...valores, [item.chave]: e.target.value })}
                  className="w-40 shrink-0 bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-white text-sm outline-none focus:ring-2 focus:ring-purple-500/50 text-right read-only:opacity-60"
                />
              </div>
              );
            })}
          </div>
        </section>
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
