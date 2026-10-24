export const ITENS_POR_PAGINA = 20;

export interface Coluna<T> {
  titulo: string;
  valor: (linha: T) => string | number | null | undefined;
}

/** Recorta a página pedida. Página fora do intervalo cai na última existente. */
export function paginar<T>(itens: T[], pagina: number): { itens: T[]; pagina: number; total: number } {
  const total = Math.max(1, Math.ceil(itens.length / ITENS_POR_PAGINA));
  const atual = Math.min(Math.max(pagina, 1), total);
  const inicio = (atual - 1) * ITENS_POR_PAGINA;
  return { itens: itens.slice(inicio, inicio + ITENS_POR_PAGINA), pagina: atual, total };
}

/** CSV com ponto e vírgula e BOM, para o Excel em português abrir os acentos corretamente. */
export function gerarCsv<T>(linhas: T[], colunas: Coluna<T>[]): string {
  const escapar = (v: unknown) => {
    const texto = v === null || v === undefined ? '' : String(v);
    return /[";\n]/.test(texto) ? `"${texto.replace(/"/g, '""')}"` : texto;
  };
  const cabecalho = colunas.map((c) => escapar(c.titulo)).join(';');
  const corpo = linhas.map((l) => colunas.map((c) => escapar(c.valor(l))).join(';'));
  return '﻿' + [cabecalho, ...corpo].join('\n');
}

export function baixarCsv(nomeArquivo: string, conteudo: string): void {
  const url = URL.createObjectURL(new Blob([conteudo], { type: 'text/csv;charset=utf-8' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = nomeArquivo;
  link.click();
  URL.revokeObjectURL(url);
}
