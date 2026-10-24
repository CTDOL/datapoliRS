import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ApisExternasSettings } from './ApisExternasSettings';
import { api } from '@/services/api';

vi.mock('@/services/api', () => ({ api: { get: vi.fn(), put: vi.fn() } }));

const RESPOSTA = {
  fontes: [
    { fonte: 'tse', nome: 'TSE (DivulgaCandContas)', base_url: 'https://divulgacandcontas.tse.jus.br/divulga/rest/v1/candidatura', ativa: true, padrao: 'https://divulgacandcontas.tse.jus.br/divulga/rest/v1/candidatura' },
    { fonte: 'camara', nome: 'Câmara dos Deputados', base_url: 'https://dadosabertos.camara.leg.br/api/v2', ativa: true, padrao: 'https://dadosabertos.camara.leg.br/api/v2' },
  ],
  maxmind: { base_local_encontrada: false, observacao: 'A chave fica no .env do servidor.' },
};

describe('ApisExternasSettings', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.get).mockResolvedValue({ data: RESPOSTA });
  });

  it('mostra cada fonte com o endereço atual e a situação', async () => {
    render(<ApisExternasSettings />);

    expect(await screen.findByText('Câmara dos Deputados')).toBeTruthy();
    expect((screen.getByLabelText('Usar Câmara dos Deputados') as HTMLInputElement).checked).toBe(true);
    expect(screen.getByDisplayValue('https://dadosabertos.camara.leg.br/api/v2')).toBeTruthy();
  });

  it('desliga uma fonte e envia só o que foi alterado nas fontes', async () => {
    vi.mocked(api.put).mockResolvedValue({ data: { ...RESPOSTA, fontes: [{ ...RESPOSTA.fontes[0] }, { ...RESPOSTA.fontes[1], ativa: false }] } });
    render(<ApisExternasSettings />);
    await screen.findByText('Câmara dos Deputados');

    fireEvent.click(screen.getByLabelText('Usar Câmara dos Deputados'));
    fireEvent.click(screen.getByRole('button', { name: /Salvar fontes de dados/ }));

    await waitFor(() => expect(api.put).toHaveBeenCalled());
    const corpo = vi.mocked(api.put).mock.calls[0][1] as { fontes: { fonte: string; ativa: boolean }[] };
    expect(corpo.fontes.find((f) => f.fonte === 'camara')?.ativa).toBe(false);
    expect(await screen.findByText(/Fontes de dados salvas/)).toBeTruthy();
  });

  it('mostra o motivo quando o endereço é recusado', async () => {
    vi.mocked(api.put).mockRejectedValue({ response: { data: { detail: 'Endereço inválido para Câmara: use https://' } } });
    render(<ApisExternasSettings />);
    await screen.findByText('Câmara dos Deputados');

    fireEvent.click(screen.getByRole('button', { name: /Salvar fontes de dados/ }));

    expect(await screen.findByRole('alert')).toBeTruthy();
    expect(screen.getByText(/use https:\/\//)).toBeTruthy();
  });
});
