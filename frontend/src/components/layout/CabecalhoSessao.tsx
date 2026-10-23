'use client';

import { useAuthStore } from '@/stores/useAuthStore';

// Rótulos dos papéis do RBAC (admin, operador, leitor). Papel desconhecido aparece como veio.
const ROTULO_PERFIL: Record<string, string> = {
  admin: 'Administrador',
  operador: 'Operador',
  leitor: 'Leitor',
};

/** Linha de identificação da sessão: gabinete, usuário logado e perfil. */
export function CabecalhoSessao() {
  const user = useAuthStore((s) => s.user);
  if (!user) return null;

  return (
    <div className="flex flex-wrap items-center gap-x-6 gap-y-1 px-6 py-2 text-xs border-b border-zinc-800/60 bg-zinc-900/40">
      <span>
        <span className="text-zinc-500">Gabinete: </span>
        <strong className="text-zinc-200">{user.nm_mandato ?? '—'}</strong>
      </span>
      <span>
        <span className="text-zinc-500">Usuário: </span>
        <span className="text-zinc-200">{user.email}</span>
      </span>
      <span>
        <span className="text-zinc-500">Perfil: </span>
        <span className="text-zinc-200">{ROTULO_PERFIL[user.role] ?? user.role}</span>
      </span>
    </div>
  );
}
