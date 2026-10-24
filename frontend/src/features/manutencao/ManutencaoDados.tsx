'use client';

import { useState } from 'react';
import { useManutencao, MUNICIPIOS_RS, JobEtl, SaudePleito } from './useManutencao';

const dataHora = (iso: string) => new Date(iso).toLocaleString('pt-BR');

const ROTULO_TIPO: Record<JobEtl['tipo'], string> = {
  votacao: 'Votação',
  comparecimento: 'Comparecimento',
};

const ROTULO_STATUS: Record<JobEtl['status'], string> = {
  pendente: 'Na fila',
  executando: 'Executando',
  concluido: 'Concluído',
  falha: 'Falhou',
};

function FormularioCarga({ onEnviar, erroEnvio }: {
  onEnviar: (tipo: JobEtl['tipo'], ano: number, confirmacao: string) => Promise<boolean>;
  erroEnvio: string | null;
}) {
  const [tipo, setTipo] = useState<JobEtl['tipo']>('votacao');
  const [ano, setAno] = useState<number>(2026);
  const [confirmacao, setConfirmacao] = useState('');
  const [enviando, setEnviando] = useState(false);

  const esperado = `CARREGAR ${tipo.toUpperCase()} ${ano}`;
  const podeEnviar = confirmacao.trim() === esperado && !enviando;

  const enviar = async () => {
    setEnviando(true);
    const ok = await onEnviar(tipo, ano, confirmacao.trim());
    setEnviando(false);
    if (ok) setConfirmacao('');
  };

  return (
    <section className="rounded-lg border border-zinc-800 p-4 flex flex-col gap-3">
      <h2 className="text-lg font-semibold text-white">Carregar dados do TSE</h2>
      <p className="text-zinc-400 text-sm">
        A carga baixa o arquivo oficial do TSE e grava no banco. Ela não troca o pleito ativo, e leva alguns minutos.
      </p>
      <div className="flex flex-wrap gap-3 items-end">
        <label className="flex flex-col text-sm text-zinc-300">
          Tipo
          <select value={tipo} onChange={(e) => setTipo(e.target.value as JobEtl['tipo'])}
            className="mt-1 rounded bg-zinc-900 border border-zinc-700 px-2 py-1 text-white">
            <option value="votacao">Votação</option>
            <option value="comparecimento">Comparecimento</option>
          </select>
        </label>
        <label className="flex flex-col text-sm text-zinc-300">
          Ano
          <input type="number" min={2000} max={2100} value={ano}
            onChange={(e) => setAno(Number(e.target.value))}
            className="mt-1 w-28 rounded bg-zinc-900 border border-zinc-700 px-2 py-1 text-white" />
        </label>
        <label className="flex flex-col text-sm text-zinc-300 flex-1 min-w-[16rem]">
          Para confirmar, digite <span className="font-mono text-amber-300">{esperado}</span>
          <input type="text" value={confirmacao} onChange={(e) => setConfirmacao(e.target.value)}
            className="mt-1 rounded bg-zinc-900 border border-zinc-700 px-2 py-1 text-white font-mono" />
        </label>
        <button type="button" disabled={!podeEnviar} onClick={enviar}
          className="rounded bg-[color:var(--cor-primaria)] px-4 py-2 text-on-accent disabled:opacity-40 disabled:cursor-not-allowed">
          {enviando ? 'Enfileirando…' : 'Carregar'}
        </button>
      </div>
      {erroEnvio && <p className="text-red-400 text-sm">{erroEnvio}</p>}
    </section>
  );
}

function AtivarPleito({ pleito, onAtivar, erroAtivacao }: {
  pleito: SaudePleito;
  onAtivar: (cd: string, confirmacao: string, aceitar: boolean) => Promise<boolean>;
  erroAtivacao: string | null;
}) {
  const [aberto, setAberto] = useState(false);
  const [confirmacao, setConfirmacao] = useState('');
  const [aceitar, setAceitar] = useState(false);
  const esperado = `ATIVAR ${pleito.ano_eleicao}`;
  const bloqueadoSemAceite = pleito.codigos_sem_cadastro > 0 && !aceitar;
  const podeAtivar = confirmacao.trim() === esperado && !bloqueadoSemAceite;

  if (!aberto) {
    return <button type="button" onClick={() => setAberto(true)} className="underline text-[color:var(--cor-texto-destaque)]">Ativar</button>;
  }
  return (
    <div className="flex flex-col gap-2 min-w-[14rem]">
      {pleito.codigos_sem_cadastro > 0 && (
        <label className="flex items-center gap-2 text-amber-300 text-xs">
          <input type="checkbox" checked={aceitar} onChange={(e) => setAceitar(e.target.checked)} />
          Aceito ativar com {pleito.codigos_sem_cadastro} código(s) sem cadastro
        </label>
      )}
      <input type="text" value={confirmacao} onChange={(e) => setConfirmacao(e.target.value)}
        placeholder={esperado} className="rounded bg-zinc-900 border border-zinc-700 px-2 py-1 font-mono text-white" />
      <div className="flex gap-2">
        <button type="button" disabled={!podeAtivar}
          onClick={async () => { if (await onAtivar(pleito.cd_eleicao, confirmacao.trim(), aceitar)) setAberto(false); }}
          className="rounded bg-[color:var(--cor-primaria)] px-3 py-1 text-on-accent disabled:opacity-40">Confirmar</button>
        <button type="button" onClick={() => setAberto(false)} className="text-zinc-400 underline">Cancelar</button>
      </div>
      {erroAtivacao && <p className="text-red-400 text-xs">{erroAtivacao}</p>}
    </div>
  );
}

export function ManutencaoDados() {
  const { saude, cargas, jobs, cdAtivo, isLoading, erro, erroEnvio, erroAtivacao, recarregar, enfileirar, ativarPleito } = useManutencao();

  if (isLoading) return <p className="text-zinc-400">Carregando…</p>;
  if (erro) {
    return (
      <div className="text-red-400">
        <p>{erro}</p>
        <button onClick={recarregar} className="underline mt-2">Tentar de novo</button>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      <FormularioCarga onEnviar={enfileirar} erroEnvio={erroEnvio} />

      <section>
        <h2 className="text-lg font-semibold text-white mb-3">Cargas na fila</h2>
        {jobs.length === 0 ? (
          <p className="text-zinc-400">Nenhuma carga solicitada.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left text-zinc-300">
              <thead className="text-zinc-400 border-b border-zinc-800">
                <tr>
                  <th className="py-2 pr-4">Solicitada em</th>
                  <th className="py-2 pr-4">Tipo</th>
                  <th className="py-2 pr-4">Ano</th>
                  <th className="py-2 pr-4">Por</th>
                  <th className="py-2 pr-4">Status</th>
                  <th className="py-2 pr-4">Detalhe</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((j) => (
                  <tr key={j.id_job} className="border-b border-zinc-900">
                    <td className="py-2 pr-4">{dataHora(j.solicitado_em)}</td>
                    <td className="py-2 pr-4">{ROTULO_TIPO[j.tipo]}</td>
                    <td className="py-2 pr-4">{j.ano_eleicao}</td>
                    <td className="py-2 pr-4">{j.solicitado_por}</td>
                    <td className={`py-2 pr-4 ${j.status === 'falha' ? 'text-red-400' : j.status === 'concluido' ? 'text-emerald-400' : 'text-amber-300'}`}>
                      {ROTULO_STATUS[j.status]}
                    </td>
                    <td className="py-2 pr-4 text-xs text-zinc-400">{j.erro ?? ''}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section>
        <h2 className="text-lg font-semibold text-white mb-3">Saúde por pleito</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left text-zinc-300">
            <thead className="text-zinc-400 border-b border-zinc-800">
              <tr>
                <th className="py-2 pr-4">Pleito</th>
                <th className="py-2 pr-4">Ano</th>
                <th className="py-2 pr-4">Turno</th>
                <th className="py-2 pr-4">Linhas de votação</th>
                <th className="py-2 pr-4">Municípios (de {MUNICIPIOS_RS})</th>
                <th className="py-2 pr-4">Zonas</th>
                <th className="py-2 pr-4">Códigos sem cadastro</th>
                <th className="py-2 pr-4">Linhas de comparecimento</th>
                <th className="py-2 pr-4">Pleito ativo</th>
              </tr>
            </thead>
            <tbody>
              {saude.map((p) => (
                <tr key={p.cd_eleicao} className="border-b border-zinc-900">
                  <td className="py-2 pr-4">{p.ds_eleicao} <span className="text-zinc-500">({p.cd_eleicao})</span></td>
                  <td className="py-2 pr-4">{p.ano_eleicao}</td>
                  <td className="py-2 pr-4">{p.nr_turno}</td>
                  <td className="py-2 pr-4">{p.linhas_votacao.toLocaleString('pt-BR')}</td>
                  <td className={`py-2 pr-4 ${p.municipios_votacao >= MUNICIPIOS_RS ? '' : 'text-amber-400'}`}>{p.municipios_votacao}</td>
                  <td className="py-2 pr-4">{p.zonas_votacao}</td>
                  <td className={`py-2 pr-4 ${p.codigos_sem_cadastro > 0 ? 'text-amber-400' : ''}`}>{p.codigos_sem_cadastro}</td>
                  <td className="py-2 pr-4">{p.linhas_comparecimento.toLocaleString('pt-BR')}</td>
                  <td className="py-2 pr-4">
                    {p.cd_eleicao === cdAtivo
                      ? <span className="text-emerald-400">Ativo</span>
                      : <AtivarPleito pleito={p} onAtivar={ativarPleito} erroAtivacao={erroAtivacao} />}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold text-white mb-3">Histórico de cargas</h2>
        {cargas.length === 0 ? (
          <p className="text-zinc-400">Nenhuma carga registrada ainda.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left text-zinc-300">
              <thead className="text-zinc-400 border-b border-zinc-800">
                <tr>
                  <th className="py-2 pr-4">Quando</th>
                  <th className="py-2 pr-4">Tipo</th>
                  <th className="py-2 pr-4">Ano</th>
                  <th className="py-2 pr-4">Pleitos</th>
                  <th className="py-2 pr-4">Arquivo</th>
                  <th className="py-2 pr-4">SHA-256</th>
                  <th className="py-2 pr-4">Linhas</th>
                  <th className="py-2 pr-4">Status</th>
                </tr>
              </thead>
              <tbody>
                {cargas.map((c) => (
                  <tr key={c.id_carga} className="border-b border-zinc-900" title={c.erro ?? undefined}>
                    <td className="py-2 pr-4">{dataHora(c.concluido_em)}</td>
                    <td className="py-2 pr-4">{ROTULO_TIPO[c.tipo]}</td>
                    <td className="py-2 pr-4">{c.ano_eleicao}</td>
                    <td className="py-2 pr-4">{c.cd_eleicoes.join(', ')}</td>
                    <td className="py-2 pr-4">{c.arquivo_origem}</td>
                    <td className="py-2 pr-4 font-mono text-xs">{c.sha256.slice(0, 12)}…</td>
                    <td className="py-2 pr-4">{c.linhas_carregadas?.toLocaleString('pt-BR') ?? '—'}</td>
                    <td className={`py-2 pr-4 ${c.status === 'falha' ? 'text-red-400' : 'text-emerald-400'}`}>{c.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
