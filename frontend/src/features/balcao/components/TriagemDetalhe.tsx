'use client';

import { useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Download,
  FileText,
  Sparkles,
  Trash2,
} from 'lucide-react';
import { balcaoService } from '../services/balcaoService';
import { useMunicipios } from '@/features/geo/useMunicipios';
import type {
  AnexoCriadoResposta,
  DescartarRequest,
  EfetivarRequest,
  EfetivarResponse,
  EntradaDetalhe,
  EventoTimeline,
  ResolverRequest,
  ResolverResponse,
} from '../types';
import { AtendimentoTimelinePanel } from './AtendimentoTimelinePanel';

interface TriagemDetalheProps {
  entrada: EntradaDetalhe;
  efetivacaoRecente: EfetivarResponse | null;
  timeline: EventoTimeline[];
  podeEscrever: boolean;
  processando: boolean;
  onAnalisar?: (idEntrada: string) => Promise<EntradaDetalhe | null>;
  onEfetivar: (idEntrada: string, payload: EfetivarRequest) => Promise<EfetivarResponse | null>;
  onDescartar: (idEntrada: string, payload: DescartarRequest) => Promise<boolean>;
  onAnexar: (idAtendimento: string, arquivo: File) => Promise<AnexoCriadoResposta | null>;
  onResolver: (
    idAtendimento: string,
    idAtendido: string,
    payload: ResolverRequest
  ) => Promise<ResolverResponse | null>;
}

export function TriagemDetalhe({
  entrada,
  efetivacaoRecente,
  timeline,
  podeEscrever,
  processando,
  onAnalisar,
  onEfetivar,
  onDescartar,
  onAnexar,
  onResolver,
}: TriagemDetalheProps) {
  const extraidos = entrada.dados_extraidos ?? {};
  const [nome, setNome] = useState(typeof extraidos.nome === 'string' ? extraidos.nome : '');
  const [telefone, setTelefone] = useState(
    typeof extraidos.telefone === 'string' ? extraidos.telefone : ''
  );
  const [email, setEmail] = useState(typeof extraidos.email === 'string' ? extraidos.email : '');
  const [municipioId, setMunicipioId] = useState(
    typeof extraidos.municipio_id === 'string' ? extraidos.municipio_id : ''
  );
  const [resumo, setResumo] = useState(entrada.texto_original || '');
  const [motivoDescarte, setMotivoDescarte] = useState('');

  const pendente = entrada.status === 'PENDENTE';
  const { municipios } = useMunicipios(pendente);
  const municipioNome =
    municipios.find((m) => m.cd_ibge_7 === municipioId.trim())?.nm_municipio ||
    extraidos.municipios_candidatos_opcoes?.find((o) => o.id === municipioId.trim())?.nome ||
    (municipioId.trim() === extraidos.municipio_id ? extraidos.municipio_nome : null) ||
    null;
  const sugestaoResolvida = entrada.sugestoes.find((s) =>
    s.motivo.toLowerCase().includes('resolv')
  );

  const handleEfetivar = async (e: React.FormEvent) => {
    e.preventDefault();
    await onEfetivar(entrada.id, {
      nome: nome.trim() || null,
      telefone: telefone.trim() || null,
      email: email.trim() || null,
      municipio_id: municipioId.trim() || null,
      resumo: resumo.trim() || null,
    });
  };

  const handleAnalisar = async () => {
    if (!onAnalisar) return;
    const atualizada = await onAnalisar(entrada.id);
    if (!atualizada) return;
    const novos = atualizada.dados_extraidos ?? {};
    if (typeof novos.nome === 'string') setNome(novos.nome);
    if (typeof novos.telefone === 'string') setTelefone(novos.telefone);
    if (typeof novos.email === 'string') setEmail(novos.email);
    if (typeof novos.municipio_id === 'string') setMunicipioId(novos.municipio_id);
  };

  const handleDescartar = async () => {
    await onDescartar(entrada.id, {
      motivo: motivoDescarte.trim() || null,
    });
  };

  return (
    <div className="space-y-5 rounded-2xl border border-zinc-800 bg-zinc-900/60 p-5">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-zinc-800 pb-3">
        <div>
          <span className="text-xs font-medium uppercase tracking-wider text-zinc-400">
            Status: <strong className="text-white">{entrada.status}</strong>
          </span>
          <p className="text-xs text-zinc-500">
            Recebida em {new Date(entrada.criado_em).toLocaleString('pt-BR')}
          </p>
        </div>
        <span className="font-mono text-[11px] text-zinc-500">{entrada.id}</span>
      </div>

      {sugestaoResolvida && (
        <div
          role="alert"
          className="flex items-start gap-3 rounded-xl border border-amber-300 bg-amber-50 p-3.5 text-xs text-amber-950"
        >
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
          <div>
            <p className="font-semibold">Alerta de assunto semelhante já resolvido (365 dias)</p>
            <p className="mt-0.5 text-amber-800">
              {sugestaoResolvida.motivo} · Similaridade:{' '}
              {Math.round(sugestaoResolvida.score_similaridade * 100)}%
            </p>
          </div>
        </div>
      )}

      {entrada.sugestoes.length > 0 && !sugestaoResolvida && (
        <div className="rounded-xl border border-sky-300 bg-sky-50 p-3 text-xs text-sky-950">
          <p className="flex items-center gap-1.5 font-semibold">
            <Sparkles className="h-3.5 w-3.5 text-sky-600" />
            <span>Sugestões de vínculo ({entrada.sugestoes.length})</span>
          </p>
          <ul className="mt-1.5 space-y-1.5 text-sky-900">
            {entrada.sugestoes.map((sug) => (
              <li key={sug.id} className="flex flex-wrap items-center justify-between gap-2">
                <span>
                  {sug.motivo} ({Math.round(sug.score_similaridade * 100)}%)
                </span>
                {pendente && podeEscrever && sug.atendimento_relacionado_id && (
                  <button
                    type="button"
                    disabled={processando}
                    onClick={() =>
                      onDescartar(entrada.id, {
                        motivo: `Agrupado ao atendimento existente (${sug.motivo})`,
                      })
                    }
                    className="rounded-md border border-sky-400 bg-white px-2.5 py-1 text-[11px] font-semibold text-sky-900 hover:bg-sky-100 disabled:opacity-60"
                  >
                    Agrupar no atendimento
                  </button>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div>
        <h3 className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-zinc-400">
          Texto Recebido
        </h3>
        <p className="whitespace-pre-wrap rounded-xl border border-zinc-800 bg-zinc-950/70 p-3.5 text-sm text-zinc-200">
          {entrada.texto_original || '(texto esvaziado após descarte)'}
        </p>
      </div>

      {entrada.anexos.length > 0 && (
        <div>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-zinc-400">
            Anexos ({entrada.anexos.length})
          </h3>
          <div className="flex flex-wrap gap-2">
            {entrada.anexos.map((anexo) => (
              <a
                key={anexo.id}
                href={balcaoService.urlDownloadAnexo(anexo.id)}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-1.5 text-xs text-zinc-200 hover:bg-zinc-700"
              >
                <FileText className="h-3.5 w-3.5 text-purple-400" />
                <span>{anexo.mime_type}</span>
                <Download className="h-3 w-3 text-zinc-400" />
              </a>
            ))}
          </div>
        </div>
      )}

      {pendente && podeEscrever && (
        <form onSubmit={handleEfetivar} className="space-y-4 border-t border-zinc-800 pt-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="text-sm font-semibold text-white">Triagem & Efetivação</h3>
            {onAnalisar && (
              <button
                type="button"
                onClick={handleAnalisar}
                disabled={processando}
                className="inline-flex items-center gap-1.5 rounded-lg border border-purple-600 bg-purple-50 px-3 py-1.5 text-xs font-semibold text-purple-900 hover:bg-purple-100 disabled:opacity-60"
              >
                <Sparkles className="h-3.5 w-3.5 text-purple-700" />
                <span>{processando ? 'Analisando...' : 'Analisar (Regex / IA)'}</span>
              </button>
            )}
          </div>

          {extraidos.ia_complementou && (
            <p className="rounded-lg border border-purple-300 bg-purple-50 px-3 py-1.5 text-xs text-purple-900">
              Análise por IA aplicada para complementar campos em aberto.
            </p>
          )}

          {Array.isArray(extraidos.municipios_candidatos) &&
            extraidos.municipios_candidatos.length > 1 &&
            !municipioId.trim() && (
              <div className="rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 text-xs text-amber-950 space-y-2">
                <p>
                  Múltiplos municípios citados ({extraidos.municipios_candidatos.join(', ')}):
                  escolha o correto ou acione a análise com IA.
                </p>
                {Array.isArray(extraidos.municipios_candidatos_opcoes) &&
                  extraidos.municipios_candidatos_opcoes.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {extraidos.municipios_candidatos_opcoes.map((opcao) => (
                        <button
                          key={opcao.id}
                          type="button"
                          onClick={() => setMunicipioId(opcao.id)}
                          className="rounded-md border border-amber-400 bg-white px-2.5 py-1 text-xs font-semibold text-amber-950 hover:bg-amber-100"
                        >
                          Usar {opcao.nome} ({opcao.id})
                        </button>
                      ))}
                    </div>
                  )}
              </div>
            )}

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <label htmlFor="triagem-nome" className="mb-1 block text-xs text-zinc-300">
                Nome do atendido
              </label>
              <input
                id="triagem-nome"
                type="text"
                value={nome}
                onChange={(e) => setNome(e.target.value)}
                className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-xs text-white focus:border-purple-500 focus:outline-none"
              />
            </div>
            <div>
              <label htmlFor="triagem-telefone" className="mb-1 block text-xs text-zinc-300">
                Telefone
              </label>
              <input
                id="triagem-telefone"
                type="text"
                value={telefone}
                onChange={(e) => setTelefone(e.target.value)}
                className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-xs text-white focus:border-purple-500 focus:outline-none"
              />
            </div>
            <div>
              <label htmlFor="triagem-email" className="mb-1 block text-xs text-zinc-300">
                E-mail
              </label>
              <input
                id="triagem-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-xs text-white focus:border-purple-500 focus:outline-none"
              />
            </div>
            <div>
              <label htmlFor="triagem-municipio" className="mb-1 flex items-center justify-between gap-2 text-xs text-zinc-300">
                <span>Código IBGE do município</span>
                {municipioNome && (
                  <span className="font-semibold text-purple-700">{municipioNome}</span>
                )}
              </label>
              <input
                id="triagem-municipio"
                type="text"
                list="balcao-municipios-lista"
                value={municipioId}
                onChange={(e) => setMunicipioId(e.target.value)}
                placeholder="Digite o código IBGE ou escolha pelo nome"
                className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-xs text-white focus:border-purple-500 focus:outline-none"
              />
              {municipios.length > 0 && (
                <datalist id="balcao-municipios-lista">
                  {municipios.map((m) => (
                    <option key={m.cd_ibge_7} value={m.cd_ibge_7}>
                      {m.nm_municipio} ({m.cd_ibge_7})
                    </option>
                  ))}
                </datalist>
              )}
            </div>
          </div>

          <div>
            <label htmlFor="triagem-resumo" className="mb-1 block text-xs text-zinc-300">
              Resumo autorizado do atendimento
            </label>
            <textarea
              id="triagem-resumo"
              rows={3}
              value={resumo}
              onChange={(e) => setResumo(e.target.value)}
              className="w-full rounded-lg border border-zinc-700 bg-zinc-950 p-2.5 text-xs text-white focus:border-purple-500 focus:outline-none"
            />
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
            <button
              type="submit"
              disabled={processando}
              className="inline-flex items-center gap-2 rounded-xl bg-purple-600 px-4 py-2 text-xs font-semibold text-white hover:bg-purple-500 disabled:opacity-60"
            >
              <CheckCircle2 className="h-4 w-4" />
              <span>{processando ? 'Processando...' : 'Efetivar Entrada'}</span>
            </button>

            <div className="flex items-center gap-2">
              <input
                type="text"
                aria-label="Motivo do descarte"
                value={motivoDescarte}
                onChange={(e) => setMotivoDescarte(e.target.value)}
                placeholder="Motivo do descarte (opcional)"
                className="rounded-lg border border-zinc-700 bg-zinc-950 px-2.5 py-1.5 text-xs text-white placeholder-zinc-500 focus:border-rose-500 focus:outline-none"
              />
              <button
                type="button"
                onClick={handleDescartar}
                disabled={processando}
                className="inline-flex items-center gap-1.5 rounded-xl border border-rose-300 bg-rose-50 px-3 py-2 text-xs font-semibold text-rose-900 hover:bg-rose-100 disabled:opacity-60"
              >
                <Trash2 className="h-3.5 w-3.5" />
                <span>Descartar</span>
              </button>
            </div>
          </div>
        </form>
      )}

      {(efetivacaoRecente || timeline.length > 0) && (
        <AtendimentoTimelinePanel
          atendimentoId={efetivacaoRecente?.atendimento_id ?? null}
          atendidoId={efetivacaoRecente?.atendido_id ?? null}
          protocolo={efetivacaoRecente?.protocolo ?? null}
          timeline={timeline}
          podeEscrever={podeEscrever}
          processando={processando}
          onAnexar={onAnexar}
          onResolver={onResolver}
        />
      )}
    </div>
  );
}

