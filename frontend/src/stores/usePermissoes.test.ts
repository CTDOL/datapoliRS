import { describe, it, expect } from 'vitest';
import { permissoesDoPapel } from './usePermissoes';

describe('permissoesDoPapel (matriz RBAC aprovada em 2026-10-23)', () => {
  it('admin escreve e exclui', () => {
    expect(permissoesDoPapel('admin')).toEqual({ podeEscrever: true, podeExcluir: true });
  });

  it('operador escreve, mas não exclui', () => {
    expect(permissoesDoPapel('operador')).toEqual({ podeEscrever: true, podeExcluir: false });
  });

  it('leitor só consulta: não escreve e não exclui', () => {
    expect(permissoesDoPapel('leitor')).toEqual({ podeEscrever: false, podeExcluir: false });
  });

  it('sem sessão ou papel desconhecido não ganha nenhuma permissão', () => {
    expect(permissoesDoPapel(undefined)).toEqual({ podeEscrever: false, podeExcluir: false });
    expect(permissoesDoPapel('papel-inventado')).toEqual({ podeEscrever: false, podeExcluir: false });
  });
});
