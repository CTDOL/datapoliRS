'use client';

import { useEffect, useState } from 'react';
import { Loader2, Plus, Power, KeyRound } from 'lucide-react';
import { api } from '@/services/api';

interface Gabinete {
  id_tenant: string;
  nm_mandato: string;
  ds_cargo_mandato: string;
  is_ativo: boolean;
  emails_admin: string | null;
}

const VAZIO = { nm_mandato: '', ds_cargo_mandato: '', cd_ibge_base: '', email_admin: '', senha_inicial: '' };

/** Gestão dos gabinetes pela área da plataforma (ADR 037). Não lê nem altera dados dos gabinetes. */
export function GabinetesPlataforma() {
  const [gabinetes, setGabinetes] = useState<Gabinete[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [novo, setNovo] = useState(VAZIO);
  const [senhaAdmin, setSenhaAdmin] = useState<Record<string, string>>({});
  const [mensagem, setMensagem] = useState<{ tipo: 'ok' | 'erro'; texto: string } | null>(null);

  const carregar = async () => {
    try {
      const res = await api.get<Gabinete[]>('/api/v1/plataforma/gabinetes');
      setGabinetes(res.data);
    } catch {
      setMensagem({ tipo: 'erro', texto: 'Não foi possível carregar os gabinetes.' });
    } finally {
      setCarregando(false);
    }
  };

  useEffect(() => {
    let ativo = true;
    api
      .get<Gabinete[]>('/api/v1/plataforma/gabinetes')
      .then((res) => {
        if (ativo) setGabinetes(res.data);
      })
      .catch(() => {
        if (ativo) setMensagem({ tipo: 'erro', texto: 'Não foi possível carregar os gabinetes.' });
      })
      .finally(() => {
        if (ativo) setCarregando(false);
      });
    return () => {
      ativo = false;
    };
  }, []);

  const informarErro = (erro: unknown, padrao: string) => {
    const detalhe = (erro as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
    setMensagem({ tipo: 'erro', texto: detalhe ?? padrao });
  };

  const criar = async (evento: React.FormEvent) => {
    evento.preventDefault();
    setMensagem(null);
    try {
      await api.post('/api/v1/plataforma/gabinetes', {
        nm_mandato: novo.nm_mandato,
        ds_cargo_mandato: novo.ds_cargo_mandato,
        cd_ibge_base: novo.cd_ibge_base || null,
        email_admin: novo.email_admin,
        senha_inicial: novo.senha_inicial,
      });
      setNovo(VAZIO);
      setMensagem({ tipo: 'ok', texto: 'Gabinete criado. O admin troca a senha no primeiro acesso.' });
      await carregar();
    } catch (erro) {
      informarErro(erro, 'Não foi possível criar o gabinete.');
    }
  };

  const alternarAtivo = async (gabinete: Gabinete) => {
    setMensagem(null);
    try {
      await api.patch(`/api/v1/plataforma/gabinetes/${gabinete.id_tenant}`, { is_ativo: !gabinete.is_ativo });
      await carregar();
    } catch (erro) {
      informarErro(erro, 'Não foi possível alterar o gabinete.');
    }
  };

  const redefinirSenha = async (gabinete: Gabinete) => {
    const email = gabinete.emails_admin?.split(',')[0]?.trim();
    const senha = senhaAdmin[gabinete.id_tenant] ?? '';
    if (!email) return setMensagem({ tipo: 'erro', texto: 'Este gabinete não tem administrador.' });
    setMensagem(null);
    try {
      await api.post(`/api/v1/plataforma/gabinetes/${gabinete.id_tenant}/admin/senha`, { email_admin: email, senha_nova: senha });
      setSenhaAdmin({ ...senhaAdmin, [gabinete.id_tenant]: '' });
      setMensagem({ tipo: 'ok', texto: 'Senha redefinida. O admin troca a senha no próximo acesso.' });
    } catch (erro) {
      informarErro(erro, 'Não foi possível redefinir a senha.');
    }
  };

  return (
    <div className="space-y-8">
      {mensagem && (
        <p role={mensagem.tipo === 'erro' ? 'alert' : 'status'}
           className={`text-sm ${mensagem.tipo === 'erro' ? 'text-red-400' : 'text-teal-400'}`}>{mensagem.texto}</p>
      )}

      <section className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6">
        <h2 className="text-sm font-semibold text-white">Gabinetes</h2>
        {carregando ? (
          <div className="mt-4 flex items-center gap-2 text-zinc-400 text-sm"><Loader2 className="w-4 h-4 animate-spin" /> Carregando...</div>
        ) : (
          <ul className="mt-4 divide-y divide-zinc-800">
            {gabinetes.map((g) => (
              <li key={g.id_tenant} className="py-4 flex flex-col gap-3">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-sm text-white font-medium">{g.nm_mandato}</p>
                    <p className="text-xs text-zinc-400">{g.ds_cargo_mandato} · admin: {g.emails_admin ?? 'nenhum'} · {g.is_ativo ? 'ativo' : 'inativo'}</p>
                  </div>
                  <button onClick={() => alternarAtivo(g)}
                          className="flex items-center gap-2 text-xs px-3 py-2 rounded-lg border border-zinc-700 text-zinc-200 hover:bg-zinc-800">
                    <Power className="w-3.5 h-3.5" /> {g.is_ativo ? 'Desativar' : 'Ativar'}
                  </button>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <input type="password" aria-label={`Nova senha do admin de ${g.nm_mandato}`}
                         value={senhaAdmin[g.id_tenant] ?? ''}
                         onChange={(e) => setSenhaAdmin({ ...senhaAdmin, [g.id_tenant]: e.target.value })}
                         placeholder="Nova senha do admin (mín. 8)"
                         className="flex-1 min-w-[180px] rounded-lg bg-zinc-950 border border-zinc-800 px-3 py-2 text-xs text-white" />
                  <button onClick={() => redefinirSenha(g)} disabled={(senhaAdmin[g.id_tenant] ?? '').length < 8}
                          className="flex items-center gap-2 text-xs px-3 py-2 rounded-lg border border-zinc-700 text-zinc-200 hover:bg-zinc-800 disabled:opacity-50">
                    <KeyRound className="w-3.5 h-3.5" /> Redefinir senha
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2"><Plus className="w-4 h-4" /> Novo gabinete</h2>
        <form onSubmit={criar} className="mt-4 grid gap-3 sm:grid-cols-2 max-w-3xl">
          <input required placeholder="Nome do mandato" value={novo.nm_mandato} onChange={(e) => setNovo({ ...novo, nm_mandato: e.target.value })}
                 className="rounded-lg bg-zinc-950 border border-zinc-800 px-3 py-2 text-sm text-white" />
          <input required placeholder="Cargo (ex.: Deputado Estadual)" value={novo.ds_cargo_mandato} onChange={(e) => setNovo({ ...novo, ds_cargo_mandato: e.target.value })}
                 className="rounded-lg bg-zinc-950 border border-zinc-800 px-3 py-2 text-sm text-white" />
          <input placeholder="Código IBGE do município-base (7 dígitos)" value={novo.cd_ibge_base} onChange={(e) => setNovo({ ...novo, cd_ibge_base: e.target.value })}
                 className="rounded-lg bg-zinc-950 border border-zinc-800 px-3 py-2 text-sm text-white" />
          <input required type="email" placeholder="E-mail do admin" value={novo.email_admin} onChange={(e) => setNovo({ ...novo, email_admin: e.target.value })}
                 className="rounded-lg bg-zinc-950 border border-zinc-800 px-3 py-2 text-sm text-white" />
          <input required type="password" minLength={8} placeholder="Senha inicial do admin (mín. 8)" value={novo.senha_inicial} onChange={(e) => setNovo({ ...novo, senha_inicial: e.target.value })}
                 className="rounded-lg bg-zinc-950 border border-zinc-800 px-3 py-2 text-sm text-white sm:col-span-2" />
          <button type="submit" className="sm:col-span-2 justify-self-start bg-[color:var(--cor-primaria)] hover:bg-[color:var(--cor-primaria-hover)] text-on-accent px-4 py-2.5 rounded-xl text-sm font-medium">
            Criar gabinete
          </button>
        </form>
      </section>
    </div>
  );
}
