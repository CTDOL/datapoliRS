'use client';

import { useEffect, useState } from 'react';
import { Download, Loader2, ShieldAlert, Trash2 } from 'lucide-react';
import { api } from '@/services/api';
import { MapaIpsSuspeitos } from './MapaIpsSuspeitos';
import { baixarCsv, gerarCsv, paginar, type Coluna } from './listagem';

interface Saude { api: { status: string; versao: string; ambiente: string }; banco: { status: string; latencia_ms?: number }; cache: { status: string; detalhe?: string } }
interface Alerta { severidade: 'alta' | 'media'; titulo: string; detalhe: string }
interface IpSuspeito { ip: string; falhas_login: number; emails_distintos: number; negados_403: number; ultimo_evento: string; motivos: string[]; localizacao: string | null; coordenadas: [number, number] | null }
interface Registro { created_at: string; evento: string; email: string | null; caminho: string | null; ip: string | null; status_http: number | null }

const EVENTOS = ['', 'login_ok', 'login_falha', 'acesso_negado_403', 'exportacao_dados', 'lideranca_excluida', 'usuario_alterado'];

const COLUNAS_IPS: Coluna<IpSuspeito>[] = [
  { titulo: 'IP', valor: (s) => s.ip },
  { titulo: 'Motivo', valor: (s) => s.motivos.join(' · ') },
  { titulo: 'Senhas erradas', valor: (s) => s.falhas_login },
  { titulo: 'Contas tentadas', valor: (s) => s.emails_distintos },
  { titulo: 'Acessos negados', valor: (s) => s.negados_403 },
  { titulo: 'Localização', valor: (s) => s.localizacao },
];

const COLUNAS_TRILHA: Coluna<Registro>[] = [
  { titulo: 'Data', valor: (r) => new Date(r.created_at).toLocaleString('pt-BR') },
  { titulo: 'Evento', valor: (r) => r.evento },
  { titulo: 'E-mail', valor: (r) => r.email },
  { titulo: 'Caminho', valor: (r) => r.caminho },
  { titulo: 'IP', valor: (r) => r.ip },
  { titulo: 'HTTP', valor: (r) => r.status_http },
];

/** Barra de paginação de 20 em 20: Anterior, página atual e Próxima. */
function Paginacao({ pagina, total, aoMudar, rotulo }: { pagina: number; total: number; aoMudar: (p: number) => void; rotulo: string }) {
  if (total <= 1) return null;
  return (
    <nav aria-label={`Paginação de ${rotulo}`} className="mt-3 flex items-center justify-end gap-3 text-xs text-zinc-400">
      <button onClick={() => aoMudar(pagina - 1)} disabled={pagina <= 1} className="px-3 py-1 rounded-lg border border-zinc-700 disabled:opacity-40">Anterior</button>
      <span>Página {pagina} de {total}</span>
      <button onClick={() => aoMudar(pagina + 1)} disabled={pagina >= total} className="px-3 py-1 rounded-lg border border-zinc-700 disabled:opacity-40">Próxima</button>
    </nav>
  );
}

function cor(status: string) {
  return status === 'ok' ? 'text-teal-400' : status === 'indisponivel' ? 'text-amber-400' : 'text-red-400';
}

/** Painel do super-admin: saúde, alertas, trilha de acesso e expurgo (ADR 040). */
export function ObservabilidadePlataforma() {
  const [saude, setSaude] = useState<Saude | null>(null);
  const [alertas, setAlertas] = useState<Alerta[]>([]);
  const [ipsSuspeitos, setIpsSuspeitos] = useState<IpSuspeito[]>([]);
  const [registros, setRegistros] = useState<Registro[]>([]);
  const [evento, setEvento] = useState('');
  const [carregando, setCarregando] = useState(true);
  const [confirmandoExpurgo, setConfirmandoExpurgo] = useState(false);
  const [mensagem, setMensagem] = useState<string | null>(null);
  const [paginaIps, setPaginaIps] = useState(1);
  const [paginaTrilha, setPaginaTrilha] = useState(1);

  const carregarRegistros = async (filtro: string) => {
    const res = await api.get<Registro[]>('/api/v1/plataforma/logs', { params: filtro ? { evento: filtro } : {} });
    setRegistros(res.data);
  };

  useEffect(() => {
    let ativo = true;
    Promise.all([
      api.get<Saude>('/api/v1/plataforma/saude'),
      api.get<Alerta[]>('/api/v1/plataforma/alertas'),
      api.get<Registro[]>('/api/v1/plataforma/logs'),
      api.get<IpSuspeito[]>('/api/v1/plataforma/ips-suspeitos'),
    ])
      .then(([s, a, l, ips]) => {
        if (!ativo) return;
        setSaude(s.data);
        setAlertas(a.data);
        setRegistros(l.data);
        setIpsSuspeitos(ips.data);
      })
      .catch(() => {
        if (ativo) setMensagem('Não foi possível carregar o painel.');
      })
      .finally(() => {
        if (ativo) setCarregando(false);
      });
    return () => {
      ativo = false;
    };
  }, []);

  const trocarFiltro = async (valor: string) => {
    setEvento(valor);
    setPaginaTrilha(1);
    try {
      await carregarRegistros(valor);
    } catch {
      setMensagem('Não foi possível filtrar a trilha.');
    }
  };

  const expurgar = async () => {
    setConfirmandoExpurgo(false);
    try {
      const res = await api.post<{ removidos: number }>('/api/v1/plataforma/logs/expurgo');
      setMensagem(`Expurgo concluído: ${res.data.removidos} registro(s) com mais de 6 meses removido(s).`);
      await carregarRegistros(evento);
    } catch {
      setMensagem('Não foi possível concluir o expurgo.');
    }
  };

  if (carregando) {
    return <div className="flex items-center gap-2 text-zinc-400 text-sm"><Loader2 className="w-4 h-4 animate-spin" /> Carregando painel...</div>;
  }

  return (
    <div className="space-y-8">
      {mensagem && <p role="status" className="text-sm text-zinc-300">{mensagem}</p>}

      <section className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-5">
          <p className="text-xs text-zinc-400">API</p>
          <p className={`text-lg font-semibold ${cor(saude?.api.status ?? 'erro')}`}>{saude?.api.status ?? '—'}</p>
          <p className="text-xs text-zinc-500">{saude?.api.versao} · {saude?.api.ambiente}</p>
        </div>
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-5">
          <p className="text-xs text-zinc-400">Banco de dados</p>
          <p className={`text-lg font-semibold ${cor(saude?.banco.status ?? 'erro')}`}>{saude?.banco.status ?? '—'}</p>
          <p className="text-xs text-zinc-500">{saude?.banco.latencia_ms != null ? `${saude.banco.latencia_ms} ms` : ''}</p>
        </div>
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-5">
          <p className="text-xs text-zinc-400">Cache (Redis)</p>
          <p className={`text-lg font-semibold ${cor(saude?.cache.status ?? 'erro')}`}>{saude?.cache.status ?? '—'}</p>
          <p className="text-xs text-zinc-500">{saude?.cache.detalhe ?? ''}</p>
        </div>
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2"><ShieldAlert className="w-4 h-4" /> Alertas da última hora</h2>
        {alertas.length === 0 ? (
          <p className="mt-3 text-sm text-zinc-400">Nenhum alerta.</p>
        ) : (
          <ul className="mt-3 space-y-2">
            {alertas.map((a, i) => (
              <li key={i} className={`rounded-xl border px-4 py-3 text-sm ${a.severidade === 'alta' ? 'border-red-500/40 text-red-300' : 'border-amber-500/40 text-amber-300'}`}>
                <strong>{a.titulo}</strong> — {a.detalhe}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6">
        <h2 className="text-sm font-semibold text-white">IPs suspeitos (última hora)</h2>
        {ipsSuspeitos.length === 0 ? (
          <p className="mt-3 text-sm text-zinc-400">Nenhum IP com tentativas suspeitas.</p>
        ) : (
          <>
            <MapaIpsSuspeitos pontos={ipsSuspeitos} />
          <div className="mt-4 flex justify-end">
            <button onClick={() => baixarCsv('ips-suspeitos.csv', gerarCsv(ipsSuspeitos, COLUNAS_IPS))}
                    className="flex items-center gap-2 text-xs px-3 py-2 rounded-lg border border-zinc-700 text-zinc-200 hover:bg-zinc-800">
              <Download className="w-3.5 h-3.5" /> Exportar CSV
            </button>
          </div>
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-xs text-zinc-300">
              <thead className="text-zinc-500">
                <tr><th className="py-2 pr-4">IP</th><th className="pr-4">Motivo</th><th className="pr-4">Senhas erradas</th><th className="pr-4">Contas tentadas</th><th className="pr-4">Acessos negados</th><th>Localização</th></tr>
              </thead>
              <tbody>
                {paginar(ipsSuspeitos, paginaIps).itens.map((s) => (
                  <tr key={s.ip} className="border-t border-zinc-800">
                    <td className="py-2 pr-4 font-mono">{s.ip}</td>
                    <td className="pr-4 text-red-300">{s.motivos.join(' · ')}</td>
                    <td className="pr-4">{s.falhas_login}</td>
                    <td className="pr-4">{s.emails_distintos}</td>
                    <td className="pr-4">{s.negados_403}</td>
                    <td>{s.localizacao ?? 'sem localização'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Paginacao pagina={paginar(ipsSuspeitos, paginaIps).pagina} total={paginar(ipsSuspeitos, paginaIps).total} aoMudar={setPaginaIps} rotulo="IPs suspeitos" />
          </>
        )}
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-sm font-semibold text-white">Trilha de acesso</h2>
          <div className="flex items-center gap-3">
            <select aria-label="Filtrar por evento" value={evento} onChange={(e) => trocarFiltro(e.target.value)}
                    className="rounded-lg bg-zinc-950 border border-zinc-800 px-3 py-2 text-xs text-white">
              {EVENTOS.map((e) => <option key={e} value={e}>{e || 'Todos os eventos'}</option>)}
            </select>
            <button onClick={() => baixarCsv('trilha-acesso.csv', gerarCsv(registros, COLUNAS_TRILHA))}
                    className="flex items-center gap-2 text-xs px-3 py-2 rounded-lg border border-zinc-700 text-zinc-200 hover:bg-zinc-800">
              <Download className="w-3.5 h-3.5" /> Exportar CSV
            </button>
            {confirmandoExpurgo ? (
              <span className="flex items-center gap-2 text-xs">
                <button onClick={expurgar} className="px-3 py-2 rounded-lg border border-red-500/40 text-red-300">Confirmar expurgo</button>
                <button onClick={() => setConfirmandoExpurgo(false)} className="px-3 py-2 text-zinc-400">Cancelar</button>
              </span>
            ) : (
              <button onClick={() => setConfirmandoExpurgo(true)}
                      className="flex items-center gap-2 text-xs px-3 py-2 rounded-lg border border-zinc-700 text-zinc-200 hover:bg-zinc-800">
                <Trash2 className="w-3.5 h-3.5" /> Expurgar acima de 6 meses
              </button>
            )}
          </div>
        </div>

        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-xs text-zinc-300">
            <thead className="text-zinc-500">
              <tr><th className="py-2 pr-4">Data</th><th className="pr-4">Evento</th><th className="pr-4">E-mail</th><th className="pr-4">Caminho</th><th className="pr-4">IP</th><th>HTTP</th></tr>
            </thead>
            <tbody>
              {paginar(registros, paginaTrilha).itens.map((r, i) => (
                <tr key={i} className="border-t border-zinc-800">
                  <td className="py-2 pr-4">{new Date(r.created_at).toLocaleString('pt-BR')}</td>
                  <td className="pr-4">{r.evento}</td>
                  <td className="pr-4">{r.email ?? '—'}</td>
                  <td className="pr-4">{r.caminho ?? '—'}</td>
                  <td className="pr-4">{r.ip ?? '—'}</td>
                  <td>{r.status_http ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <Paginacao pagina={paginar(registros, paginaTrilha).pagina} total={paginar(registros, paginaTrilha).total} aoMudar={setPaginaTrilha} rotulo="trilha de acesso" />
      </section>

      <p className="text-xs text-zinc-500">This product includes GeoLite2 data created by MaxMind, available from https://www.maxmind.com</p>
    </div>
  );
}
