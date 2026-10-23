import { describe, it, expect } from 'vitest';
import { agruparPorMunicipio, popupLideranca, popupMunicipio, pontosDasLiderancas } from './mapLayers';
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

const NOVO_HAMBURGO = { cd_ibge_7: '4313409', nm_municipio: 'Novo Hamburgo', latitude: -29.68, longitude: -51.13 };

describe('agruparPorMunicipio', () => {
  it('junta no mesmo pino as lideranças do mesmo município (caso Novo Hamburgo)', () => {
    const jonas = lideranca({ id_lideranca: '1', nm_completo: 'Jonas', municipios: [NOVO_HAMBURGO] });
    const stive = lideranca({ id_lideranca: '2', nm_completo: 'STIVE', municipios: [NOVO_HAMBURGO] });

    const grupos = agruparPorMunicipio([jonas, stive]);

    expect(grupos).toHaveLength(1);
    expect(grupos[0].mun.cd_ibge_7).toBe('4313409');
    expect(grupos[0].liderancas.map((l) => l.nm_completo)).toEqual(['Jonas', 'STIVE']);
  });

  it('põe uma liderança que atua em dois municípios em dois pinos diferentes', () => {
    const stive = lideranca({ id_lideranca: '2', nm_completo: 'STIVE', municipios: [NOVO_HAMBURGO, PORTO_ALEGRE] });

    const grupos = agruparPorMunicipio([stive]);

    expect(grupos).toHaveLength(2);
    expect(grupos.every((g) => g.liderancas.length === 1)).toBe(true);
  });
});

describe('popupMunicipio', () => {
  it('lista todas as lideranças e escapa o nome de cada uma', () => {
    const html = popupMunicipio(NOVO_HAMBURGO, [
      lideranca({ nm_completo: 'Jonas', ds_foto_url: '/uploads/liderancas/foto.png' }),
      lideranca({ nm_completo: '<img src=x onerror=alert(1)>' }),
    ]);

    expect(html).toContain('Novo Hamburgo · 2 lideranças');
    expect(html).toContain('<img src="');
    expect(html).toContain('Jonas');
    expect(html).not.toContain('<img src=x');
    expect(html).toContain('&lt;img src=x onerror=alert(1)&gt;');
  });
});
