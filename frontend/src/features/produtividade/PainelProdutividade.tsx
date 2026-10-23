'use client';

import { useEffect, useState } from 'react';
import { Loader2 } from 'lucide-react';
import { api } from '@/services/api';

export interface ProdutividadeDados {
  tarefas: { total: number; pendente: number; em_andamento: number; concluida: number; atrasadas: number };
  por_responsavel: { nome: string | null; abertas: number; concluidas: number }[];
  comentarios_ultimos_7_dias: number;
  projetos_lei: number;
  emendas: number;
}

function Indicador({ titulo, valor, destaque }: { titulo: string; valor: number; destaque?: boolean }) {
  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-5">
      <p className="text-xs text-zinc-400">{titulo}</p>
      <p className={`text-2xl font-semibold ${destaque && valor > 0 ? 'text-amber-400' : 'text-white'}`}>{valor}</p>
    </div>
  );
}

/** Visão geral do gabinete para a autoridade (admin): andamento das tarefas e carga por responsável. */
export function PainelProdutividade() {
  const [dados, setDados] = useState<ProdutividadeDados | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    let ativo = true;
    api.get<ProdutividadeDados>('/api/v1/gabinete/produtividade')
      .then((res) => { if (ativo) setDados(res.data); })
      .catch(() => { if (ativo) setErro('Não foi possível carregar o painel.'); });
    return () => { ativo = false; };
  }, []);

  if (erro) return <p role="alert" className="text-sm text-red-400">{erro}</p>;
  if (!dados) return <div className="flex items-center gap-2 text-zinc-400 text-sm"><Loader2 className="w-4 h-4 animate-spin" /> Carregando painel…</div>;

  const { tarefas } = dados;
  return (
    <div className="space-y-6">
      <section aria-label="Indicadores" className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Indicador titulo="Tarefas" valor={tarefas.total} />
        <Indicador titulo="Pendentes" valor={tarefas.pendente} />
        <Indicador titulo="Em andamento" valor={tarefas.em_andamento} />
        <Indicador titulo="Atrasadas" valor={tarefas.atrasadas} destaque />
        <Indicador titulo="Concluídas" valor={tarefas.concluida} />
        <Indicador titulo="Comentários (7 dias)" valor={dados.comentarios_ultimos_7_dias} />
        <Indicador titulo="Projetos de lei" valor={dados.projetos_lei} />
        <Indicador titulo="Emendas" valor={dados.emendas} />
      </section>

      <section aria-labelledby="carga-responsavel" className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-5">
        <h2 id="carga-responsavel" className="text-sm font-semibold text-white mb-3">Carga por responsável</h2>
        {dados.por_responsavel.length === 0 ? (
          <p className="text-sm text-zinc-500">Nenhuma tarefa cadastrada.</p>
        ) : (
          <table className="w-full text-left text-sm text-zinc-300">
            <thead className="text-xs text-zinc-500">
              <tr><th className="py-2">Responsável</th><th>Abertas</th><th>Concluídas</th></tr>
            </thead>
            <tbody>
              {dados.por_responsavel.map((r) => (
                <tr key={r.nome ?? 'sem'} className="border-t border-zinc-800">
                  <td className="py-2">{r.nome ?? 'Sem responsável'}</td>
                  <td>{r.abertas}</td>
                  <td>{r.concluidas}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
