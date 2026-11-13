'use client';

import { useRef, useState } from 'react';
import { CheckCircle2, FileUp, Send, AlertTriangle } from 'lucide-react';
import {
  balcaoService,
  LIMITE_ANEXO_BYTES,
  TIPOS_ANEXO_PERMITIDOS,
} from '../services/balcaoService';
import { extrairMensagemErroApi } from '../types';

interface PortalPublicoFormProps {
  token: string;
}

function mapearErroPortal(error: unknown): string {
  const status = (error as { response?: { status?: number } })?.response?.status;
  if (status === 404) return 'Este link de atendimento é inválido ou foi desativado.';
  if (status === 413) return 'O arquivo enviado ultrapassa o limite máximo de 10 MB.';
  if (status === 415) return 'Formato de arquivo não permitido. Envie JPEG, PNG, WEBP ou PDF.';
  if (status === 429) return 'Muitas solicitações seguidas. Aguarde um minuto e tente novamente.';
  if (status === 503) return 'Serviço temporariamente indisponível. Tente novamente em instantes.';
  return extrairMensagemErroApi(error, 'Não foi possível enviar sua solicitação.');
}

export function PortalPublicoForm({ token }: PortalPublicoFormProps) {
  const [texto, setTexto] = useState('');
  const [anexo, setAnexo] = useState<File | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [confirmacao, setConfirmacao] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setErro(null);
    const arquivo = e.target.files?.[0] ?? null;
    if (!arquivo) {
      setAnexo(null);
      return;
    }
    if (arquivo.size > LIMITE_ANEXO_BYTES) {
      setErro('O arquivo enviado ultrapassa o limite máximo de 10 MB.');
      setAnexo(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }
    if (
      arquivo.type &&
      !TIPOS_ANEXO_PERMITIDOS.includes(arquivo.type as (typeof TIPOS_ANEXO_PERMITIDOS)[number])
    ) {
      setErro('Formato de arquivo não permitido. Envie JPEG, PNG, WEBP ou PDF.');
      setAnexo(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }
    setAnexo(arquivo);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErro(null);
    setConfirmacao(null);

    if (!texto.trim()) {
      setErro('Descreva sua solicitação antes de enviar.');
      return;
    }

    setEnviando(true);
    try {
      const resposta = await balcaoService.enviarEntradaPortal(token, texto.trim(), anexo);
      setConfirmacao(resposta.mensagem);
      setTexto('');
      setAnexo(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch (err) {
      setErro(mapearErroPortal(err));
    } finally {
      setEnviando(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {confirmacao && (
        <div
          role="status"
          className="flex items-start gap-3 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4 text-sm text-emerald-200"
        >
          <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-emerald-400" />
          <p>{confirmacao}</p>
        </div>
      )}

      {erro && (
        <div
          role="alert"
          className="flex items-start gap-3 rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-200"
        >
          <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-rose-400" />
          <p>{erro}</p>
        </div>
      )}

      <div>
        <label htmlFor="portal-texto" className="mb-2 block text-sm font-medium text-zinc-200">
          Descreva sua solicitação, demanda ou recado
        </label>
        <textarea
          id="portal-texto"
          rows={6}
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          placeholder="Informe seu nome, município, contato e o que você precisa..."
          className="w-full rounded-xl border border-zinc-700/80 bg-zinc-950/70 p-3.5 text-sm text-white placeholder-zinc-500 focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
        />
      </div>

      <div>
        <label htmlFor="portal-anexo" className="mb-2 block text-sm font-medium text-zinc-200">
          Anexar documento ou foto (opcional — JPEG, PNG, WEBP ou PDF até 10 MB)
        </label>
        <div className="flex flex-wrap items-center gap-3">
          <label
            htmlFor="portal-anexo"
            className="inline-flex cursor-pointer items-center gap-2 rounded-xl border border-zinc-700 bg-zinc-800/70 px-4 py-2.5 text-sm font-medium text-zinc-200 hover:bg-zinc-800"
          >
            <FileUp className="h-4 w-4" />
            <span>{anexo ? anexo.name : 'Escolher arquivo'}</span>
          </label>
          <input
            ref={fileInputRef}
            id="portal-anexo"
            type="file"
            accept="image/jpeg,image/png,image/webp,application/pdf"
            onChange={handleFileChange}
            className="sr-only"
          />
          {anexo && (
            <button
              type="button"
              onClick={() => {
                setAnexo(null);
                if (fileInputRef.current) fileInputRef.current.value = '';
              }}
              className="text-xs text-zinc-400 hover:text-zinc-200"
            >
              Remover arquivo
            </button>
          )}
        </div>
      </div>

      <button
        type="submit"
        disabled={enviando}
        className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-purple-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-purple-500 disabled:cursor-not-allowed disabled:opacity-60"
      >
        <Send className="h-4 w-4" />
        <span>{enviando ? 'Enviando...' : 'Enviar solicitação'}</span>
      </button>
    </form>
  );
}

