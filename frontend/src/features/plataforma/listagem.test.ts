import { describe, it, expect } from 'vitest';
import { paginar, gerarCsv, ITENS_POR_PAGINA } from './listagem';

const itens = Array.from({ length: 45 }, (_, i) => ({ id: i + 1, nome: `item ${i + 1}` }));

describe('paginar', () => {
  it('mostra 20 itens por página e a última página com o restante', () => {
    expect(ITENS_POR_PAGINA).toBe(20);
    expect(paginar(itens, 1)).toMatchObject({ pagina: 1, total: 3 });
    expect(paginar(itens, 1).itens).toHaveLength(20);
    expect(paginar(itens, 3).itens).toHaveLength(5);
  });

  it('corrige página fora do intervalo', () => {
    expect(paginar(itens, 99).pagina).toBe(3);
    expect(paginar(itens, 0).pagina).toBe(1);
  });

  it('lista vazia tem uma página só', () => {
    expect(paginar([], 1)).toMatchObject({ pagina: 1, total: 1, itens: [] });
  });
});

describe('gerarCsv', () => {
  it('usa ponto e vírgula, BOM e escapa aspas, vírgulas e quebras', () => {
    const csv = gerarCsv(
      [{ nome: 'Ana "A"; teste', nota: null }],
      [{ titulo: 'Nome', valor: (l) => l.nome }, { titulo: 'Nota', valor: (l) => l.nota }],
    );
    expect(csv.startsWith('﻿')).toBe(true);
    expect(csv).toContain('Nome;Nota');
    expect(csv).toContain('"Ana ""A""; teste";');
  });
});
