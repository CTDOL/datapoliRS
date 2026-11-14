'use client';

import { useEffect, useState } from 'react';
import { Copy, KeyRound, Link2, ShieldOff, AlertTriangle, CheckCircle2, Cpu } from 'lucide-react';
import { balcaoService } from '../services/balcaoService';
import {
  extrairMensagemErroApi,
  type IaConfigAtualizarRequest,
  type IaConfigResposta,
  type IaConfigTestarRequest,
  type IaConfigTesteResposta,
  type PortalCriadoResposta,
  type PortalResumo,
} from '../types';

export function PortaisAdminPanel() {
  const [portais, setPortais] = useState<PortalResumo[]>([]);
  const [portalCriado, setPortalCriado] = useState<PortalCriadoResposta | null>(null);
  const [rotuloNovoPortal, setRotuloNovoPortal] = useState('');
  const [portalConfirmarRevogacao, setPortalConfirmarRevogacao] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [mensagemStatus, setMensagemStatus] = useState<string | null>(null);
  const [copiado, setCopiado] = useState(false);
  const [copiadoId, setCopiadoId] = useState<string | null>(null);

  const [iaConfig, setIaConfig] = useState<IaConfigResposta | null>(null);
  const [iaProvider, setIaProvider] = useState('regex');
  const [iaModel, setIaModel] = useState('');
  const [iaBaseUrl, setIaBaseUrl] = useState('');
  const [iaApiKey, setIaApiKey] = useState('');
  const [salvandoIa, setSalvandoIa] = useState(false);
  const [testandoIa, setTestandoIa] = useState(false);
  const [resultadoTesteIa, setResultadoTesteIa] = useState<IaConfigTesteResposta | null>(null);

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
      const criado = await balcaoService.criarPortal(rotuloNovoPortal);
      setPortalCriado(criado);
      setRotuloNovoPortal('');
      setPortais((prev) => [
        { id: criado.id, rotulo: criado.rotulo ?? null, ativo: criado.ativo, criado_em: criado.criado_em, token: criado.token },
        ...prev,
      ]);
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
        setMensagemStatus(`Link revogado permanentemente.`);
        setPortalConfirmarRevogacao(null);
        setPortais((prev) => prev.map((p) => (p.id === res.id ? { ...p, ativo: false, token: null } : p)));
      }
    } catch (err) {
      setErro(extrairMensagemErroApi(err, 'Não foi possível revogar o portal informado.'));
    } finally {
      setCarregando(false);
    }
  };

  const substituirLegado = async (portal: PortalResumo) => {
    setCarregando(true);
    setErro(null);
    setMensagemStatus(null);
    try {
      const criado = await balcaoService.criarPortal(portal.rotulo ?? undefined);
      await balcaoService.revogarPortal(portal.id);
      setPortalCriado(criado);
      setPortais((prev) => [
        { id: criado.id, rotulo: criado.rotulo ?? null, ativo: criado.ativo, criado_em: criado.criado_em, token: criado.token },
        ...prev.map((p) => (p.id === portal.id ? { ...p, ativo: false, token: null } : p)),
      ]);
      setMensagemStatus('Link antigo substituído por um novo link copiável.');
    } catch (err) {
      setErro(extrairMensagemErroApi(err, 'Não foi possível substituir o link legado.'));
    } finally {
      setCarregando(false);
    }
  };

  const montarLink = (token: string) =>
    typeof window !== 'undefined' ? `${window.location.origin}/portal/${token}` : `/portal/${token}`;

  const linkCompleto = portalCriado ? montarLink(portalCriado.token) : '';

  const handleCopiar = async () => {
    if (!linkCompleto || !navigator?.clipboard) return;
    await navigator.clipboard.writeText(linkCompleto);
    setCopiado(true);
  };

  const handleCopiarPortal = async (portal: PortalResumo) => {
    if (!portal.token || !navigator?.clipboard) return;
    await navigator.clipboard.writeText(montarLink(portal.token));
    setCopiadoId(portal.id);
    setTimeout(() => setCopiadoId((atual) => (atual === portal.id ? null : atual)), 2500);
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
    setResultadoTesteIa(null);
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

  const handleTestarIa = async () => {
    setTestandoIa(true);
    setErro(null);
    setResultadoTesteIa(null);
    try {
      const payload: IaConfigTestarRequest = {
        provider: iaProvider,
        model: iaModel,
        base_url: iaBaseUrl,
      };
      if (iaApiKey.trim()) {
        payload.api_key = iaApiKey.trim();
      }
      const res = await balcaoService.testarIaConfig(payload);
      setResultadoTesteIa(res);
    } catch (err) {
      setErro(extrairMensagemErroApi(err, 'Não foi possível testar a API de IA.'));
    } finally {
      setTestandoIa(false);
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
              <span>Portais Públicos (Links de Divulgação)</span>
            </h2>
            <p className="mt-1 text-xs text-zinc-400">
              Gere e mantenha múltiplos links ativos (WhatsApp, QR Code, bio) com cópia e revogação a qualquer momento.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <input
              type="text"
              aria-label="Rótulo opcional do novo portal"
              maxLength={80}
              value={rotuloNovoPortal}
              onChange={(e) => setRotuloNovoPortal(e.target.value)}
              placeholder="Rótulo opcional (ex.: WhatsApp)"
              className="w-56 rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-xs text-white placeholder-zinc-500 focus:border-purple-500 focus:outline-none"
            />
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
        </div>

        {portalCriado && (
          <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-2.5 text-xs">
            <span className="font-medium text-emerald-200">
              Novo link criado e adicionado à lista abaixo!
            </span>
            <button
              type="button"
              onClick={handleCopiar}
              className="inline-flex items-center gap-1.5 rounded-lg border border-emerald-500/40 bg-emerald-600/20 px-3 py-1 text-xs font-semibold text-emerald-100 hover:bg-emerald-600/30"
            >
              <Copy className="h-3.5 w-3.5" />
              <span>{copiado ? 'Copiado!' : 'Copiar Novo Link'}</span>
            </button>
          </div>
        )}

        <div className="space-y-2">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-zinc-400">
            Links Ativos ({portais.filter((p) => p.ativo).length})
          </h3>
          {portais.filter((p) => p.ativo).length === 0 ? (
            <p className="rounded-xl border border-zinc-800 bg-zinc-950/40 px-4 py-3 text-xs text-zinc-400">
              Nenhum link ativo no momento. Clique em <strong>Gerar Novo Portal</strong> acima para criar um link.
            </p>
          ) : (
            <ul className="divide-y divide-zinc-800 rounded-xl border border-zinc-800 bg-zinc-950/40">
              {portais
                .filter((p) => p.ativo)
                .map((portal) => {
                  const confirmando = portalConfirmarRevogacao === portal.id;
                  return (
                    <li key={portal.id} className="space-y-2.5 px-3.5 py-3 text-xs">
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <div className="min-w-0 flex-1 space-y-1">
                          <div className="flex flex-wrap items-center gap-2">
                            {portal.rotulo && (
                              <span className="rounded-md border border-purple-500/30 bg-purple-500/10 px-2 py-0.5 text-[11px] font-semibold text-purple-200">
                                {portal.rotulo}
                              </span>
                            )}
                            <span className="rounded-md border border-emerald-300 bg-emerald-50 px-2 py-0.5 text-[11px] font-semibold text-emerald-800">
                              Ativo
                            </span>
                            <span className="text-[11px] text-zinc-500">
                              {new Date(portal.criado_em).toLocaleString('pt-BR')}
                            </span>
                          </div>
                          {portal.token ? (
                            <code className="block truncate rounded-lg bg-zinc-950 px-2.5 py-1.5 text-[11px] text-zinc-200">
                              {montarLink(portal.token)}
                            </code>
                          ) : (
                            <span className="block font-mono text-[11px] text-zinc-400">
                              Link antigo sem cópia salva — clique em Substituir Link para gerar um copiável
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          {portal.token ? (
                            <button
                              type="button"
                              onClick={() => handleCopiarPortal(portal)}
                              className="inline-flex items-center gap-1.5 rounded-lg border border-purple-500/40 bg-purple-600/20 px-3 py-1.5 text-xs font-semibold text-purple-100 hover:bg-purple-600/30"
                            >
                              <Copy className="h-3.5 w-3.5" />
                              <span>{copiadoId === portal.id ? 'Copiado!' : 'Copiar Link'}</span>
                            </button>
                          ) : (
                            <button
                              type="button"
                              disabled={carregando}
                              onClick={() => substituirLegado(portal)}
                              className="inline-flex items-center gap-1.5 rounded-lg border border-purple-500/40 bg-purple-600/20 px-3 py-1.5 text-xs font-semibold text-purple-100 hover:bg-purple-600/30 disabled:opacity-60"
                            >
                              <Copy className="h-3.5 w-3.5" />
                              <span>Substituir Link</span>
                            </button>
                          )}
                          <button
                            type="button"
                            disabled={carregando || confirmando}
                            onClick={() => setPortalConfirmarRevogacao(portal.id)}
                            className="inline-flex items-center gap-1.5 rounded-lg border border-rose-300 bg-rose-50 px-3 py-1.5 text-xs font-semibold text-rose-900 hover:bg-rose-100 disabled:opacity-50"
                          >
                            <ShieldOff className="h-3.5 w-3.5" />
                            <span>Revogar Link</span>
                          </button>
                        </div>
                      </div>

                      {confirmando && (
                        <div
                          role="alert"
                          className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-rose-500/40 bg-rose-950/50 px-3 py-2 text-xs text-rose-200"
                        >
                          <span className="flex items-center gap-1.5 font-medium">
                            <AlertTriangle className="h-4 w-4 shrink-0 text-rose-400" />
                            <span>Atenção: esta revogação é irrevogável! O link deixará de funcionar imediatamente.</span>
                          </span>
                          <div className="flex items-center gap-2">
                            <button
                              type="button"
                              disabled={carregando}
                              onClick={() => setPortalConfirmarRevogacao(null)}
                              className="rounded-md border border-zinc-600 bg-zinc-800 px-2.5 py-1 text-[11px] font-medium text-zinc-200 hover:bg-zinc-700"
                            >
                              Cancelar
                            </button>
                            <button
                              type="button"
                              disabled={carregando}
                              onClick={() => revogarPorId(portal.id)}
                              className="rounded-md bg-rose-600 px-3 py-1 text-[11px] font-semibold text-white hover:bg-rose-500 disabled:opacity-60"
                            >
                              Confirmar Revogação
                            </button>
                          </div>
                        </div>
                      )}
                    </li>
                  );
                })}
            </ul>
          )}
        </div>
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
                disabled={salvandoIa || testandoIa}
                onClick={handleRemoverApiKey}
                className="rounded-xl border border-rose-300 bg-rose-50 px-3 py-2 text-xs font-semibold text-rose-900 hover:bg-rose-100 disabled:opacity-60"
              >
                Remover chave
              </button>
            )}
            <button
              type="button"
              disabled={salvandoIa || testandoIa}
              onClick={handleTestarIa}
              className="rounded-xl border border-purple-600 bg-purple-50 px-3 py-2 text-xs font-semibold text-purple-900 hover:bg-purple-100 disabled:opacity-60"
            >
              {testandoIa ? 'Testando...' : 'Testar API'}
            </button>
            <button
              type="submit"
              disabled={salvandoIa || testandoIa}
              className="rounded-xl bg-purple-600 px-4 py-2 text-xs font-semibold text-white hover:bg-purple-500 disabled:opacity-60"
            >
              {salvandoIa ? 'Salvando...' : 'Aplicar Motor'}
            </button>
          </div>
        </form>
        {resultadoTesteIa && (
          <div
            role="status"
            className={`rounded-xl border p-3 text-xs ${
              resultadoTesteIa.ok
                ? 'border-emerald-300 bg-emerald-50 text-emerald-900'
                : 'border-rose-300 bg-rose-50 text-rose-900'
            }`}
          >
            <p className="font-semibold">
              {resultadoTesteIa.ok ? 'Teste OK' : 'Falha no teste'} ({resultadoTesteIa.provider}
              {resultadoTesteIa.model ? ` · ${resultadoTesteIa.model}` : ''}
              {resultadoTesteIa.latencia_ms > 0 ? ` · ${resultadoTesteIa.latencia_ms} ms` : ''})
            </p>
            <p className="mt-1">{resultadoTesteIa.detalhe}</p>
            {Object.keys(resultadoTesteIa.resultado).length > 0 && (
              <p className="mt-1 font-mono text-[11px]">
                Extração de teste: {JSON.stringify(resultadoTesteIa.resultado)}
              </p>
            )}
          </div>
        )}
      </section>
    </div>
  );
}

