import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BuscaExternaProjetosLei, mensagemFontesComErro } from './BuscaExternaProjetosLei';

describe('mensagemFontesComErro', () => {
  it('diz que a fonte não respondeu sem prometer que o problema passa', () => {
    const texto = mensagemFontesComErro(['ALRS'], false);

    expect(texto).toContain('Assembleia Legislativa do RS (ALRS) não respondeu');
    expect(texto).toContain('não consultou essa fonte');
    expect(texto).not.toMatch(/tente novamente/i);
  });

  it('avisa que a lista pode estar incompleta quando há resultados de outras fontes', () => {
    const texto = mensagemFontesComErro(['ALRS'], true);

    expect(texto).toContain('pode estar incompleta');
  });

  it('usa o plural quando mais de uma fonte falha', () => {
    expect(mensagemFontesComErro(['ALRS', 'CAMARA'], false)).toContain('não responderam');
  });
});

describe('BuscaExternaProjetosLei', () => {
  it('exibe o aviso de fonte sem resposta', () => {
    render(
      <BuscaExternaProjetosLei
        nomeBusca="nadine"
        onNomeBuscaChange={() => undefined}
        resultados={[]}
        fontesComErro={['ALRS']}
        isBuscando={false}
        importandoChave={null}
      />,
    );

    expect(screen.getByRole('alert').textContent).toContain('Assembleia Legislativa do RS (ALRS) não respondeu');
  });

  it('mostra o termo pesquisado, o autor, a data e a ementa completa de cada resultado', () => {
    render(
      <BuscaExternaProjetosLei
        nomeBusca="nadine"
        onNomeBuscaChange={() => undefined}
        resultados={[{
          fonte: 'CAMARA',
          identificador_externo: '123',
          tipo: 'PL',
          numero: '5',
          ano: 2026,
          ementa: 'Dispõe sobre fisioterapeutas nas maternidades do Estado do Rio Grande do Sul, com texto longo que não deve ser cortado na lista.',
          situacao: 'Para Parecer',
          autor: 'Delegada Nadine',
          data_apresentacao: '2026-03-10',
          url_fonte: null,
          ja_importado: false,
          id_projeto_lei: null,
        }]}
        fontesComErro={[]}
        isBuscando={false}
        importandoChave={null}
      />,
    );

    expect(screen.getByText('«nadine»')).toBeTruthy();
    expect(screen.getByText('Delegada Nadine')).toBeTruthy();
    expect(screen.getByText('10/03/2026')).toBeTruthy();
    expect(screen.getByText(/não deve ser cortado/)).toBeTruthy();
  });
});
