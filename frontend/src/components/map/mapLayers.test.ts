import { describe, it, expect } from 'vitest';
import { popupLideranca, pontosDasLiderancas } from './mapLayers';
import type { LiderancaPoint } from './ElectionMap';

const PORTO_ALEGRE = { cd_ibge_7: '4314902', nm_municipio: 'Porto Alegre', latitude: -30.03, longitude: -51.23 };

function lideranca(campos: Partial<LiderancaPoint>): LiderancaPoint {
  return { id_lideranca: 'x', nm_completo: 'Liderança', tp_influencia: 'Comunitária', municipios: [PORTO_ALEGRE], ...campos };
}

describe('popupLideranca', () => {
  it('escapa HTML vindo do cadastro: nome malicioso não vira tag', () => {
    const html = popupLideranca(
      lideranca({ nm_completo: '<img src=x onerror=alert(1)>', ds_foto_url: '"><script>alert(2)</script>' }),
      PORTO_ALEGRE
    );

    expect(html).not.toContain('<img src=x');
    expect(html).not.toContain('<script>');
    expect(html).toContain('&lt;img src=x onerror=alert(1)&gt;');
  });

  it('mantém o conteúdo legível de um cadastro normal', () => {
    const html = popupLideranca(lideranca({ nm_completo: 'Maria & José', nr_telefone: '51999998888' }), PORTO_ALEGRE);

    expect(html).toContain('Maria &amp; José');
    expect(html).toContain('Porto Alegre');
    expect(html).toContain('WhatsApp');
  });
});

describe('pontosDasLiderancas', () => {
  it('gera um ponto por município com coordenadas e ignora os sem coordenada', () => {
    const semCoordenada = { cd_ibge_7: '4300000', nm_municipio: 'Sem GPS' };
    const pontos = pontosDasLiderancas([lideranca({ municipios: [PORTO_ALEGRE, semCoordenada] })]);

    expect(pontos).toHaveLength(1);
    expect(pontos[0].mun.cd_ibge_7).toBe('4314902');
  });
});
