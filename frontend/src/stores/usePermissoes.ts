import { useAuthStore } from './useAuthStore';

export interface Permissoes {
  /** Criar e editar. Leitor não escreve. */
  podeEscrever: boolean;
  /** Excluir registros. Só admin. */
  podeExcluir: boolean;
}

/**
 * Matriz RBAC aprovada pelo operador em 2026-10-23: leitor só consulta;
 * operador cria e edita; só admin exclui. A proteção real está no backend
 * (require_role); isto só esconde os controles que não se aplicam ao papel.
 */
export function permissoesDoPapel(role?: string | null): Permissoes {
  return {
    podeEscrever: role === 'admin' || role === 'operador',
    podeExcluir: role === 'admin',
  };
}

export function usePermissoes(): Permissoes {
  const role = useAuthStore((state) => state.user?.role);
  return permissoesDoPapel(role);
}
