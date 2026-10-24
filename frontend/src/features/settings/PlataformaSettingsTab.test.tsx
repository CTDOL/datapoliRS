import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { PlataformaSettingsTab } from './PlataformaSettingsTab';
import type { ConfiguracaoItem } from './usePlatformConfig';

const CONFIG = (chave: string, valor: string, categoria: ConfiguracaoItem['categoria'], descricao: string): ConfiguracaoItem =>
  ({ chave, valor, tipo: 'int', categoria, descricao, updated_at: '2026-10-23T10:00:00Z' });

const CONFIGURACOES: ConfiguracaoItem[] = [
  CONFIG('rate_limit.voting.times', '20', 'rate_limit', 'Maximo de requisicoes por janela no modulo de Votacao e Candidatos'),
  CONFIG('rate_limit.login.times', '5', 'rate_limit', 'Maximo de tentativas de login por janela'),
  CONFIG('cache_ttl.geojson_municipios', '604800', 'cache', 'Duracao do cache do GeoJSON dos municipios'),
  { chave: 'ambiente.tipo', valor: 'NON_PRODUCTION', tipo: 'string', categoria: 'sistema', descricao: 'Tipo de ambiente', updated_at: '2026-10-23T10:00:00Z' },
  CONFIG('chave.nova.sem.secao', '1', 'cache', 'Chave nova ainda sem seção'),
];

describe('PlataformaSettingsTab', () => {
  it('agrupa por API e mantém chave sem seção em Outras', () => {
    render(<PlataformaSettingsTab configuracoes={CONFIGURACOES} isLoading={false} isSubmitting={false} isAdmin onSave={vi.fn()} />);

    expect(screen.getByRole('heading', { name: 'Votação e candidatos' })).toBeTruthy();
    expect(screen.getByRole('heading', { name: 'Autenticação' })).toBeTruthy();
    expect(screen.getByRole('heading', { name: 'Mapa e geografia' })).toBeTruthy();
    expect(screen.getByRole('heading', { name: 'Sistema' })).toBeTruthy();
    expect(screen.getByRole('heading', { name: 'Outras' })).toBeTruthy();
    expect(screen.queryByRole('heading', { name: 'Eleições e cargos' })).toBeNull();
  });

  it('mostra ambiente.tipo como somente leitura e não o envia ao salvar', async () => {
    const onSave = vi.fn().mockResolvedValue({ ok: true });
    render(<PlataformaSettingsTab configuracoes={CONFIGURACOES} isLoading={false} isSubmitting={false} isAdmin onSave={onSave} />);
    await screen.findByDisplayValue('5'); // valores entram no formulário num efeito assíncrono

    expect((screen.getByLabelText('Tipo de ambiente') as HTMLInputElement).readOnly).toBe(true);
    fireEvent.click(screen.getByRole('button', { name: /Salvar Alterações/ }));

    await screen.findByText(/Configurações aplicadas/);
    const enviado = onSave.mock.calls[0][0] as Record<string, string>;
    expect(enviado['ambiente.tipo']).toBeUndefined();
    expect(enviado['rate_limit.login.times']).toBe('5');
  });
});
