'use client';

import { useState } from 'react';
import { Copy, KeyRound, Link2, ShieldOff, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { balcaoService } from '../services/balcaoService';
import { extrairMensagemErroApi, type PortalCriadoResposta } from '../types';

export function PortaisAdminPanel() {
  const [portalCriado, setPortalCriado] = useState<PortalCriadoResposta | null>(null);
  const [portalIdRevogar, setPortalIdRevogar] = useState('');
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [mensagemStatus, setMensagemStatus] = useState<string | null>(null);
  const [copiado, setCopiado] = useState(false);

  const handleCriarPortal = async () => {
    setCarregando(true);
    setErro(null);
    setMensagemStatus(null);
    setCopiado(false);
    try {
      const criado = await balcaoService.criarPortal();
      setPortalCriado(criado);
    } catch (err) {
      setErro(extrairMensagemErroApi(err, 'Não foi possível gerar um novo portal público.'));
    } finally {
      setCarregando(false);
    }
  };

  const handleRevogar = async (e: React.FormEvent) => {
    e.preventDefault();
    const id = portalIdRevogar.trim();
    if (!id) {
      setErro('Informe o ID do portal para revogar.');
      return;
    }
    setCarregando(true);
    setErro(null);
    setMensagemStatus(null);
    try {
      const res = await balcaoService.revogarPortal(id);
      if (!res.ativo) {
        setMensagemStatus(`Portal ${res.id} revogado com sucesso.`);
        setPortalIdRevogar('');
      }
    } catch (err) {
      setErro(extrairMensagemErroApi(err, 'Não foi possível revogar o portal informado.'));
    } finally {
      setCarregando(false);
    }
  };

  const linkCompleto =
    portalCriado && typeof window !== 'undefined'
      ? `${window.location.origin}/portal/${portalCriado.token}`
      : portalCriado
        ? `/portal/${portalCriado.token}`
        : '';

  const handleCopiar = async () => {
    if (!linkCompleto || !navigator?.clipboard) return;
    await navigator.clipboard.writeText(linkCompleto);
    setCopiado(true);
  };

  return (
    <div className="space-y-6">
      {erro && (
        <div
          role="alert"
          className="flex items-center gap-2 rounded-xl border border-rose-500/30 bg-rose-500/10 p-3 text-sm text-rose-200"
        >
          <AlertTriangle className="h-4 w-4 text-rose-400" />
          <span>{erro}</span>
        </div>
      )}

      {mensagemStatus && (
        <div
          role="status"
          className="flex items-center gap-2 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3 text-sm text-emerald-200"
        >
          <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          <span>{mensagemStatus}</span>
        </div>
      )}

      <section className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-5 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="flex items-center gap-2 text-base font-semibold text-white">
              <Link2 className="h-4 w-4 text-purple-400" />
              <span>Gerar Link de Portal Público</span>
            </h2>
            <p className="mt-1 text-xs text-zinc-400">
              O token em claro é exibido apenas uma vez no momento da criação.
            </p>
          </div>
          <button
            type="button"
            onClick={handleCriarPortal}
            disabled={carregando}
            className="inline-flex items-center gap-2 rounded-xl bg-purple-600 px-4 py-2 text-xs font-semibold text-white hover:bg-purple-500 disabled:opacity-60"
          >
            <KeyRound className="h-4 w-4" />
            <span>{carregando ? 'Gerando...' : 'Gerar Novo Portal'}</span>
          </button>
        </div>

        {portalCriado && (
          <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 space-y-2">
            <p className="text-xs font-semibold text-amber-200">
              Copie e guarde este link agora. Ele não será exibido novamente.
            </p>
            <div className="flex flex-wrap items-center gap-2">
              <code className="flex-1 break-all rounded-lg bg-zinc-950 px-3 py-2 text-xs text-zinc-100">
                {linkCompleto}
              </code>
              <button
                type="button"
                onClick={handleCopiar}
                className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-xs font-medium text-white hover:bg-zinc-700"
              >
                <Copy className="h-3.5 w-3.5" />
                <span>{copiado ? 'Copiado' : 'Copiar'}</span>
              </button>
            </div>
            <p className="text-[11px] text-zinc-400">
              ID do portal: <span className="font-mono text-zinc-200">{portalCriado.id}</span>
            </p>
          </div>
        )}
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-5 space-y-3">
        <h2 className="flex items-center gap-2 text-base font-semibold text-white">
          <ShieldOff className="h-4 w-4 text-rose-400" />
          <span>Revogar Portal Existente</span>
        </h2>
        <form onSubmit={handleRevogar} className="flex flex-wrap items-center gap-3">
          <input
            type="text"
            aria-label="ID do portal para revogar"
            value={portalIdRevogar}
            onChange={(e) => setPortalIdRevogar(e.target.value)}
            placeholder="UUID do portal (ex.: 550e8400-e29b-41d4-...)"
            className="min-w-[260px] flex-1 rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-xs text-white placeholder-zinc-500 focus:border-purple-500 focus:outline-none"
          />
          <button
            type="submit"
            disabled={carregando}
            className="rounded-xl border border-rose-500/40 bg-rose-500/15 px-4 py-2 text-xs font-semibold text-rose-200 hover:bg-rose-500/25 disabled:opacity-60"
          >
            Revogar Portal
          </button>
        </form>
      </section>
    </div>
  );
}

