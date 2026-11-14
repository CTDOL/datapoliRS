'use client';

import { useRef, useState } from 'react';
import { CheckCircle2, Clock, FileCheck2, Upload } from 'lucide-react';
import type {
  AnexoCriadoResposta,
  EventoTimeline,
  ResolverRequest,
  ResolverResponse,
} from '../types';

interface AtendimentoTimelinePanelProps {
  atendimentoId: string | null;
  atendidoId: string | null;
  protocolo?: string | null;
  timeline: EventoTimeline[];
  podeEscrever: boolean;
  processando: boolean;
  onAnexar: (idAtendimento: string, arquivo: File) => Promise<AnexoCriadoResposta | null>;
  onResolver: (
    idAtendimento: string,
    idAtendido: string,
    payload: ResolverRequest
  ) => Promise<ResolverResponse | null>;
}

export function AtendimentoTimelinePanel({
  atendimentoId,
  atendidoId,
  protocolo,
  timeline,
  podeEscrever,
  processando,
  onAnexar,
  onResolver,
}: AtendimentoTimelinePanelProps) {
  const [despacho, setDespacho] = useState('');
  const [evidenciaAnexo, setEvidenciaAnexo] = useState<AnexoCriadoResposta | null>(null);
  const [erroLocal, setErroLocal] = useState<string | null>(null);
  const [resolvidoSucesso, setResolvidoSucesso] = useState<ResolverResponse | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleUploadEvidencia = async (e: React.ChangeEvent<HTMLInputElement>) => {
    setErroLocal(null);
    const arquivo = e.target.files?.[0];
    if (!arquivo || !atendimentoId) return;
    const anexo = await onAnexar(atendimentoId, arquivo);
    if (anexo) {
      setEvidenciaAnexo(anexo);
    }
  };

  const handleResolver = async (e: React.FormEvent) => {
    e.preventDefault();
    setErroLocal(null);
    if (!atendimentoId || !atendidoId) return;

    if (!despacho.trim()) {
      setErroLocal('Informe o despacho para concluir o atendimento.');
      return;
    }
    if (!evidenciaAnexo?.id) {
      setErroLocal('Anexe uma evidência antes de resolver o atendimento.');
      return;
    }

    const res = await onResolver(atendimentoId, atendidoId, {
      despacho: despacho.trim(),
      evidencia_anexo_id: evidenciaAnexo.id,
    });
    if (res) {
      setResolvidoSucesso(res);
      setDespacho('');
      setEvidenciaAnexo(null);
      if (fileRef.current) fileRef.current.value = '';
    }
  };

  return (
    <div className="space-y-4 rounded-xl border border-zinc-800 bg-zinc-950/60 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="flex items-center gap-2 text-sm font-semibold text-white">
          <Clock className="h-4 w-4 text-purple-400" />
          <span>Timeline do Atendido (Append-Only)</span>
        </h3>
        {protocolo && (
          <span className="rounded-md border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-0.5 font-mono text-xs font-semibold text-emerald-300">
            {protocolo}
          </span>
        )}
      </div>

      {timeline.length === 0 ? (
        <p className="text-xs text-zinc-500">Nenhum evento registrado ainda na timeline.</p>
      ) : (
        <ul className="space-y-2.5">
          {timeline.map((ev) => (
            <li
              key={ev.id}
              className="rounded-lg border border-zinc-800/80 bg-zinc-900/60 p-3 text-xs"
            >
              <div className="flex items-center justify-between gap-2 text-zinc-400">
                <span className="font-semibold text-zinc-200">
                  {ev.tipo === 'RESOLUCAO' ? 'Resolução' : ev.tipo_evento || 'Atendimento'}
                  {ev.protocolo ? ` · ${ev.protocolo}` : ''}
                </span>
                <span>{new Date(ev.ocorrido_em).toLocaleString('pt-BR')}</span>
              </div>
              {ev.resumo && <p className="mt-1.5 text-zinc-300">{ev.resumo}</p>}
            </li>
          ))}
        </ul>
      )}

      {podeEscrever && atendimentoId && atendidoId && (
        <form onSubmit={handleResolver} className="space-y-3 border-t border-zinc-800 pt-4">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
            Resolver Atendimento com Evidência
          </h4>

          {resolvidoSucesso && (
            <div
              role="status"
              className="flex items-center gap-2 rounded-lg border border-emerald-300 bg-emerald-50 p-2.5 text-xs text-emerald-900"
            >
              <CheckCircle2 className="h-4 w-4 text-emerald-400" />
              <span>Atendimento resolvido com sucesso.</span>
            </div>
          )}

          {erroLocal && (
            <div
              role="alert"
              className="rounded-lg border border-rose-300 bg-rose-50 p-2.5 text-xs text-rose-900"
            >
              {erroLocal}
            </div>
          )}

          <div>
            <label htmlFor="resolucao-despacho" className="mb-1 block text-xs text-zinc-300">
              Despacho de conclusão
            </label>
            <textarea
              id="resolucao-despacho"
              rows={3}
              value={despacho}
              onChange={(e) => setDespacho(e.target.value)}
              placeholder="Descreva a providência tomada..."
              className="w-full rounded-lg border border-zinc-700 bg-zinc-900 p-2.5 text-xs text-white placeholder-zinc-500 focus:border-purple-500 focus:outline-none"
            />
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <label
              htmlFor="resolucao-evidencia"
              className="inline-flex cursor-pointer items-center gap-2 rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-1.5 text-xs font-medium text-zinc-200 hover:bg-zinc-700"
            >
              <Upload className="h-3.5 w-3.5" />
              <span>{evidenciaAnexo ? 'Evidência anexada' : 'Anexar evidência'}</span>
            </label>
            <input
              ref={fileRef}
              id="resolucao-evidencia"
              type="file"
              accept="image/jpeg,image/png,image/webp,application/pdf"
              onChange={handleUploadEvidencia}
              className="sr-only"
            />
            {evidenciaAnexo && (
              <span className="inline-flex items-center gap-1 text-xs text-emerald-300">
                <FileCheck2 className="h-3.5 w-3.5" />
                <span>{evidenciaAnexo.mime_type}</span>
              </span>
            )}
          </div>

          <button
            type="submit"
            disabled={processando}
            className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white hover:bg-emerald-500 disabled:opacity-60"
          >
            <CheckCircle2 className="h-3.5 w-3.5" />
            <span>{processando ? 'Salvando...' : 'Resolver Atendimento'}</span>
          </button>
        </form>
      )}
    </div>
  );
}

