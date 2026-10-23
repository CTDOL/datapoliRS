'use client';

import { useEffect, useState } from 'react';
import { Loader2, Palette, Save } from 'lucide-react';
import { api } from '@/services/api';

// Padrão da plataforma, usado enquanto o gabinete não escolheu cores (ADR 038).
const COR_PADRAO = '#9333ea';

interface Props {
  isAdmin: boolean;
}

/** Cores do gabinete: a cor primária é o destaque da navegação, dos botões e do cabeçalho. */
export function IdentidadeVisualSettings({ isAdmin }: Props) {
  const [corPrimaria, setCorPrimaria] = useState(COR_PADRAO);
  const [corSecundaria, setCorSecundaria] = useState('#0e7490');
  const [carregando, setCarregando] = useState(true);
  const [salvando, setSalvando] = useState(false);
  const [mensagem, setMensagem] = useState<{ tipo: 'ok' | 'erro'; texto: string } | null>(null);

  useEffect(() => {
    api
      .get('/api/v1/gabinete/tema')
      .then((res) => {
        if (res.data.cor_primaria) setCorPrimaria(res.data.cor_primaria);
        if (res.data.cor_secundaria) setCorSecundaria(res.data.cor_secundaria);
      })
      .catch(() => setMensagem({ tipo: 'erro', texto: 'Não foi possível carregar as cores do gabinete.' }))
      .finally(() => setCarregando(false));
  }, []);

  const salvar = async (evento: React.FormEvent) => {
    evento.preventDefault();
    setSalvando(true);
    setMensagem(null);
    try {
      await api.put('/api/v1/gabinete/tema', { cor_primaria: corPrimaria, cor_secundaria: corSecundaria });
      setMensagem({ tipo: 'ok', texto: 'Cores salvas. Elas valem a partir da próxima entrada no sistema.' });
    } catch (erro: unknown) {
      const detalhe = (erro as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setMensagem({ tipo: 'erro', texto: detalhe ?? 'Não foi possível salvar as cores.' });
    } finally {
      setSalvando(false);
    }
  };

  return (
    <section className="max-w-2xl mt-8 rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6">
      <h3 className="flex items-center gap-2 text-sm font-semibold text-white">
        <Palette className="w-4 h-4" /> Identidade visual do gabinete
      </h3>
      <p className="text-xs text-zinc-400 mt-1">
        Cores da paleta do partido. O contraste mínimo é exigido para o texto branco nos botões.
      </p>

      {carregando ? (
        <div className="mt-4 flex items-center gap-2 text-zinc-400 text-sm"><Loader2 className="w-4 h-4 animate-spin" /> Carregando...</div>
      ) : (
        <form onSubmit={salvar} className="mt-4 space-y-4">
          <div className="flex flex-wrap gap-6">
            <label className="text-xs text-zinc-300">
              Cor primária
              <input type="color" value={corPrimaria} onChange={(e) => setCorPrimaria(e.target.value)}
                     disabled={!isAdmin} aria-label="Cor primária"
                     className="mt-1 block h-10 w-20 rounded-lg bg-transparent disabled:opacity-50" />
            </label>
            <label className="text-xs text-zinc-300">
              Cor secundária
              <input type="color" value={corSecundaria} onChange={(e) => setCorSecundaria(e.target.value)}
                     disabled={!isAdmin} aria-label="Cor secundária"
                     className="mt-1 block h-10 w-20 rounded-lg bg-transparent disabled:opacity-50" />
            </label>
          </div>

          {mensagem && (
            <p role={mensagem.tipo === 'erro' ? 'alert' : 'status'}
               className={`text-sm ${mensagem.tipo === 'erro' ? 'text-red-400' : 'text-teal-400'}`}>
              {mensagem.texto}
            </p>
          )}

          {isAdmin && (
            <button type="submit" disabled={salvando}
                    className="flex items-center gap-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-60 text-white px-4 py-2.5 rounded-xl text-sm font-medium">
              {salvando ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />} Salvar cores
            </button>
          )}
        </form>
      )}
    </section>
  );
}
