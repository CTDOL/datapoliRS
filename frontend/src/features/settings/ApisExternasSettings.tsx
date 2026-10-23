'use client';

import { useEffect, useState } from 'react';
import { Loader2, Save } from 'lucide-react';
import { api } from '@/services/api';

interface FonteApi { fonte: string; nome: string; base_url: string; ativa: boolean; padrao: string }
interface ApisResposta { fontes: FonteApi[]; maxmind: { base_local_encontrada: boolean; observacao: string } }

/** Fontes de dados externas: endereço e se o sistema está usando cada uma (ADR 040 e integrações legislativas). */
export function ApisExternasSettings() {
  const [dados, setDados] = useState<ApisResposta | null>(null);
  const [rascunho, setRascunho] = useState<FonteApi[]>([]);
  const [salvando, setSalvando] = useState(false);
  const [mensagem, setMensagem] = useState<{ tipo: 'ok' | 'erro'; texto: string } | null>(null);

  useEffect(() => {
    let ativo = true;
    api.get<ApisResposta>('/api/v1/admin/apis')
      .then((res) => {
        if (!ativo) return;
        setDados(res.data);
        setRascunho(res.data.fontes);
      })
      .catch(() => {
        if (ativo) setMensagem({ tipo: 'erro', texto: 'Não foi possível carregar as fontes de dados.' });
      });
    return () => {
      ativo = false;
    };
  }, []);

  const alterar = (fonte: string, campo: Partial<FonteApi>) => {
    setRascunho((atual) => atual.map((f) => (f.fonte === fonte ? { ...f, ...campo } : f)));
  };

  const salvar = async () => {
    setSalvando(true);
    setMensagem(null);
    try {
      const res = await api.put<ApisResposta>('/api/v1/admin/apis', {
        fontes: rascunho.map((f) => ({ fonte: f.fonte, base_url: f.base_url, ativa: f.ativa })),
      });
      setDados(res.data);
      setRascunho(res.data.fontes);
      setMensagem({ tipo: 'ok', texto: 'Fontes de dados salvas. Valem na próxima consulta.' });
    } catch (e: unknown) {
      const detalhe = (e as { response?: { data?: { detail?: string } } }).response?.data?.detail;
      setMensagem({ tipo: 'erro', texto: detalhe ?? 'Não foi possível salvar.' });
    } finally {
      setSalvando(false);
    }
  };

  if (!dados) {
    return <p className="text-sm text-zinc-500">Carregando fontes de dados…</p>;
  }

  return (
    <section aria-labelledby="titulo-fontes" className="space-y-4">
      <div>
        <h2 id="titulo-fontes" className="text-base font-semibold text-white">Fontes de dados</h2>
        <p className="text-sm text-zinc-400 mt-1">
          De onde o sistema busca informações. Uma fonte desligada deixa de ser consultada.
        </p>
      </div>

      {rascunho.map((fonte) => (
        <div key={fonte.fonte} className="rounded-2xl border border-zinc-800 bg-zinc-950 p-4 space-y-3">
          <div className="flex items-center justify-between gap-4">
            <p className="text-sm font-medium text-zinc-100">{fonte.nome}</p>
            <label className="flex items-center gap-2 text-xs text-zinc-300">
              <input
                type="checkbox"
                checked={fonte.ativa}
                onChange={(e) => alterar(fonte.fonte, { ativa: e.target.checked })}
                aria-label={`Usar ${fonte.nome}`}
              />
              {fonte.ativa ? 'Em uso' : 'Desligada'}
            </label>
          </div>
          <label className="block text-xs text-zinc-400">
            Endereço
            <input
              type="url"
              value={fonte.base_url}
              onChange={(e) => alterar(fonte.fonte, { base_url: e.target.value })}
              className="mt-1 w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-white font-mono"
            />
          </label>
          <div className="flex items-center justify-between text-xs text-zinc-500">
            <span>Padrão: {fonte.padrao}</span>
            {fonte.base_url !== fonte.padrao && (
              <button type="button" onClick={() => alterar(fonte.fonte, { base_url: fonte.padrao })} className="underline">
                Voltar ao padrão
              </button>
            )}
          </div>
        </div>
      ))}

      <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-4">
        <p className="text-sm font-medium text-zinc-100">Localização de IPs (MaxMind)</p>
        <p className="text-xs text-zinc-400 mt-1">
          {dados.maxmind.base_local_encontrada ? 'Base local instalada.' : 'Base local não encontrada: a localização fica como "sem localização".'}
        </p>
        <p className="text-xs text-zinc-500 mt-1">{dados.maxmind.observacao}</p>
      </div>

      {mensagem && (
        <p role={mensagem.tipo === 'erro' ? 'alert' : 'status'} className={`text-sm ${mensagem.tipo === 'ok' ? 'text-emerald-400' : 'text-red-400'}`}>
          {mensagem.texto}
        </p>
      )}

      <button
        type="button"
        onClick={salvar}
        disabled={salvando}
        className="bg-purple-600 hover:bg-purple-500 text-white px-5 py-2.5 rounded-xl font-medium flex items-center gap-2 disabled:opacity-70"
      >
        {salvando ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
        Salvar fontes de dados
      </button>
    </section>
  );
}
