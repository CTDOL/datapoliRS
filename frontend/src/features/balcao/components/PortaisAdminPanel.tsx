'use client';

import { useEffect, useState } from 'react';
import { Copy, KeyRound, Link2, ShieldOff, AlertTriangle, CheckCircle2, Cpu } from 'lucide-react';
import { balcaoService } from '../services/balcaoService';
import {
  extrairMensagemErroApi,
  type IaConfigAtualizarRequest,
  type IaConfigResposta,
  type PortalCriadoResposta,
  type PortalResumo,
} from '../types';

export function PortaisAdminPanel() {
  const [portais, setPortais] = useState<PortalResumo[]>([]);
  const [portalCriado, setPortalCriado] = useState<PortalCriadoResposta | null>(null);
  const [portalIdRevogar, setPortalIdRevogar] = useState('');
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [mensagemStatus, setMensagemStatus] = useState<string | null>(null);
  const [copiado, setCopiado] = useState(false);

  const [iaConfig, setIaConfig] = useState<IaConfigResposta | null>(null);
  const [iaProvider, setIaProvider] = useState('regex');
  const [iaModel, setIaModel] = useState('');
  const [iaBaseUrl, setIaBaseUrl] = useState('');
  const [iaApiKey, setIaApiKey] = useState('');
  const [salvandoIa, setSalvandoIa] = useState(false);

  useEffect(() => {
    let ativo = true;
    balcaoService
      .listarPortais?.()
      ?.then((lista) => {
        if (ativo && Array.isArray(lista)) setPortais(lista);
      })
      .catch(() => {
        // Silencioso para não bloquear criação/revogação
      });
    balcaoService
      .obterIaConfig?.()
      ?.then((cfg) => {
        if (!ativo || !cfg) return;
        setIaConfig(cfg);
        setIaProvider(cfg.provider || 'regex');
        setIaModel(cfg.model || '');
        setIaBaseUrl(cfg.base_url || '');
      })
      .catch(() => {
        // Silencioso para não bloquear criação/revogação de portais se usuário não tiver permissão
      });
    return () => {
      ativo = false;
    };
  }, []);

  const handleCriarPortal = async () => {
    setCarregando(true);
    setErro(null);
    setMensagemStatus(null);
    setCopiado(false);
    try {
      const criado = await balcaoService.criarPortal();
      setPortalCriado(criado);
      setPortais((prev) => [{ id: criado.id, ativo: criado.ativo, criado_em: criado.criado_em }, ...prev]);
    } catch (err) {
      setErro(extrairMensagemErroApi(err, 'Não foi possível gerar um novo portal público.'));
    } finally {
      setCarregando(false);
    }
  };

  const revogarPorId = async (id: string) => {
    setCarregando(true);
    setErro(null);
    setMensagemStatus(null);
    try {
      const res = await balcaoService.revogarPortal(id);
      if (!res.ativo) {
        setMensagemStatus(`Portal ${res.id} revogado com sucesso.`);
        setPortalIdRevogar('');
        setPortais((prev) => prev.map((p) => (p.id === res.id ? { ...p, ativo: false } : p)));
      }
    } catch (err) {
      setErro(extrairMensagemErroApi(err, 'Não foi possível revogar o portal informado.'));
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
    await revogarPorId(id);
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

  const handleSalvarIa = async (e: React.FormEvent) => {
    e.preventDefault();
    setSalvandoIa(true);
    setErro(null);
    setMensagemStatus(null);
    try {
      const payload: IaConfigAtualizarRequest = {
        provider: iaProvider,
        model: iaModel,
        base_url: iaBaseUrl,
      };
      if (iaApiKey.trim()) {
        payload.api_key = iaApiKey.trim();
      }
      const atualizado = await balcaoService.atualizarIaConfig(payload);
      setIaConfig(atualizado);
      setIaProvider(atualizado.provider);
      setIaModel(atualizado.model);
      setIaBaseUrl(atualizado.base_url);
      setIaApiKey('');
      setMensagemStatus(`Motor de extração atualizado para "${atualizado.provider}".`);
    } catch (err) {
      setErro(extrairMensagemErroApi(err, 'Não foi possível atualizar o motor de extração.'));
    } finally {
      setSalvandoIa(false);
    }
  };

  const handleRemoverApiKey = async () => {
    setSalvandoIa(true);
    setErro(null);
    setMensagemStatus(null);
    try {
      const atualizado = await balcaoService.atualizarIaConfig({
        provider: iaProvider,
        model: iaModel,
        base_url: iaBaseUrl,
        limpar_api_key: true,
      });
      setIaConfig(atualizado);
      setIaApiKey('');
      setMensagemStatus('Chave de API removida da configuração.');
    } catch (err) {
      setErro(extrairMensagemErroApi(err, 'Não foi possível remover a chave de API.'));
    } finally {
      setSalvandoIa(false);
    }
  };

  return (
    <div className="space-y-6">
      {erro && (
        <div
          role="alert"
          className="flex items-center gap-2 rounded-xl border border-rose-300 bg-rose-50 p-3 text-sm text-rose-900"
        >
          <AlertTriangle className="h-4 w-4 text-rose-400" />
          <span>{erro}</span>
        </div>
      )}

      {mensagemStatus && (
        <div
          role="status"
          className="flex items-center gap-2 rounded-xl border border-emerald-300 bg-emerald-50 p-3 text-sm text-emerald-900"
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
            <p className="text-xs font-semibold text-amber-900">
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
            className="rounded-xl border border-rose-300 bg-rose-50 px-4 py-2 text-xs font-semibold text-rose-900 hover:bg-rose-100 disabled:opacity-60"
          >
            Revogar Portal
          </button>
        </form>

        {portais.length > 0 && (
          <ul className="divide-y divide-zinc-800 rounded-xl border border-zinc-800 bg-zinc-950/40">
            {portais.map((portal) => (
              <li key={portal.id} className="flex flex-wrap items-center justify-between gap-2 px-3.5 py-2.5 text-xs">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono text-zinc-300">{portal.id}</span>
                  <span
                    className={`rounded-md px-2 py-0.5 text-[11px] font-semibold ${
                      portal.ativo ? 'bg-emerald-50 text-emerald-800 border border-emerald-300' : 'bg-zinc-800 text-zinc-400'
                    }`}
                  >
                    {portal.ativo ? 'Ativo' : 'Revogado'}
                  </span>
                  <span className="text-[11px] text-zinc-500">
                    {new Date(portal.criado_em).toLocaleString('pt-BR')}
                  </span>
                </div>
                {portal.ativo && (
                  <button
                    type="button"
                    disabled={carregando}
                    onClick={() => revogarPorId(portal.id)}
                    className="rounded-lg border border-rose-300 bg-rose-50 px-3 py-1 text-[11px] font-semibold text-rose-900 hover:bg-rose-100 disabled:opacity-60"
                  >
                    Revogar
                  </button>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-5 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 className="flex items-center gap-2 text-base font-semibold text-white">
              <Cpu className="h-4 w-4 text-purple-400" />
              <span>Motor de Extração (IA ↔ Regex)</span>
            </h2>
            <p className="mt-1 text-xs text-zinc-400">
              Comutação em runtime com fallback automático silencioso para Regex Python.
              {iaConfig?.api_key_configurada ? ' Chave de API configurada.' : ''}
            </p>
          </div>
        </div>
        <form onSubmit={handleSalvarIa} className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <div>
            <label htmlFor="balcao-ia-provider" className="mb-1 block text-xs text-zinc-400">
              Motor / Provedor
            </label>
            <select
              id="balcao-ia-provider"
              aria-label="Motor de extração"
              value={iaProvider}
              onChange={(e) => setIaProvider(e.target.value)}
              className="w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-xs text-white focus:border-purple-500 focus:outline-none"
            >
              <option value="regex">Regex Python (Determinístico)</option>
              <option value="openai">OpenAI</option>
              <option value="cohere">Cohere (OpenAI-compatível)</option>
              <option value="ollama">Ollama (Local)</option>
              <option value="gemini">Google Gemini</option>
              <option value="anthropic">Anthropic Claude</option>
            </select>
          </div>
          <div>
            <label htmlFor="balcao-ia-model" className="mb-1 block text-xs text-zinc-400">
              Modelo (opcional)
            </label>
            <input
              id="balcao-ia-model"
              type="text"
              aria-label="Modelo de IA"
              value={iaModel}
              onChange={(e) => setIaModel(e.target.value)}
              placeholder="Ex.: gpt-4o-mini, gemini-2.0-flash"
              className="w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-xs text-white placeholder-zinc-500 focus:border-purple-500 focus:outline-none"
            />
          </div>
          <div>
            <label htmlFor="balcao-ia-baseurl" className="mb-1 block text-xs text-zinc-400">
              Base URL (opcional)
            </label>
            <input
              id="balcao-ia-baseurl"
              type="text"
              aria-label="Base URL de IA"
              value={iaBaseUrl}
              onChange={(e) => setIaBaseUrl(e.target.value)}
              placeholder="Ex.: http://127.0.0.1:11434/v1"
              className="w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-xs text-white placeholder-zinc-500 focus:border-purple-500 focus:outline-none"
            />
          </div>
          <div className="sm:col-span-2">
            <label htmlFor="balcao-ia-apikey" className="mb-1 block text-xs text-zinc-400">
              Chave de API (opcional / cifrada em repouso)
            </label>
            <input
              id="balcao-ia-apikey"
              type="password"
              aria-label="Chave de API de IA"
              autoComplete="new-password"
              value={iaApiKey}
              onChange={(e) => setIaApiKey(e.target.value)}
              placeholder={
                iaConfig?.api_key_configurada
                  ? 'Já configurada (deixe em branco para manter)'
                  : 'Cole a chave do provedor (Cohere, OpenAI, Gemini, Anthropic)'
              }
              className="w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-xs text-white placeholder-zinc-500 focus:border-purple-500 focus:outline-none"
            />
          </div>
          <div className="flex items-end justify-end gap-2">
            {iaConfig?.api_key_configurada && (
              <button
                type="button"
                disabled={salvandoIa}
                onClick={handleRemoverApiKey}
                className="rounded-xl border border-rose-300 bg-rose-50 px-3 py-2 text-xs font-semibold text-rose-900 hover:bg-rose-100 disabled:opacity-60"
              >
                Remover chave
              </button>
            )}
            <button
              type="submit"
              disabled={salvandoIa}
              className="rounded-xl bg-purple-600 px-4 py-2 text-xs font-semibold text-white hover:bg-purple-500 disabled:opacity-60"
            >
              {salvandoIa ? 'Salvando...' : 'Aplicar Motor'}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}

