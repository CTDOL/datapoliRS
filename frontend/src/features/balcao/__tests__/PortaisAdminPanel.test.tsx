import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { PortaisAdminPanel } from '../components/PortaisAdminPanel';
import { balcaoService } from '../services/balcaoService';

vi.mock('../services/balcaoService', async (importOriginal) => {
  const original = await importOriginal<typeof import('../services/balcaoService')>();
  return {
    ...original,
    balcaoService: {
      ...original.balcaoService,
      listarPortais: vi.fn().mockResolvedValue([]),
      criarPortal: vi.fn(),
      revogarPortal: vi.fn(),
      obterIaConfig: vi.fn().mockResolvedValue({
        provider: 'regex',
        model: '',
        base_url: '',
        api_key_configurada: false,
        provedores_suportados: ['regex', 'openai', 'ollama', 'gemini', 'anthropic'],
      }),
      atualizarIaConfig: vi.fn().mockResolvedValue({
        provider: 'ollama',
        model: 'llama3.2',
        base_url: 'http://127.0.0.1:11434/v1',
        api_key_configurada: false,
        provedores_suportados: ['regex', 'openai', 'ollama', 'gemini', 'anthropic'],
      }),
      testarIaConfig: vi.fn().mockResolvedValue({
        ok: true,
        provider: 'cohere',
        model: 'command-a-03-2025',
        latencia_ms: 120,
        detalhe: 'Conexão validada com sucesso.',
        resultado: { nome: 'Maria Silva', municipio: 'Porto Alegre' },
      }),
    },
  };
});

describe('PortaisAdminPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('gera novo portal com token único e revoga portal existente', async () => {
    vi.mocked(balcaoService.criarPortal).mockResolvedValue({
      id: 'portal-uuid-1',
      token: 'token-secreto-abc',
      ativo: true,
      criado_em: '2026-11-13T11:00:00Z',
    });
    vi.mocked(balcaoService.revogarPortal).mockResolvedValue({
      id: 'portal-uuid-1',
      ativo: false,
    });

    render(<PortaisAdminPanel />);

    fireEvent.click(screen.getByRole('button', { name: /Gerar Novo Portal/i }));

    await waitFor(() => {
      expect(screen.getAllByText(/\/portal\/token-secreto-abc/).length).toBeGreaterThan(0);
    });

    const revogarBtn = screen.getByRole('button', { name: /Revogar Link/i });
    fireEvent.click(revogarBtn);

    expect(screen.getByRole('alert').textContent).toMatch(/irrevogável/i);
    fireEvent.click(screen.getByRole('button', { name: /Cancelar/i }));
    expect(screen.queryByRole('alert')).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: /Revogar Link/i }));
    fireEvent.click(screen.getByRole('button', { name: /Confirmar Revogação/i }));

    await waitFor(() => {
      expect(balcaoService.revogarPortal).toHaveBeenCalledWith('portal-uuid-1');
      expect(screen.getByRole('status').textContent).toMatch(/Link revogado permanentemente/i);
    });
  });

  it('comuta o motor de extração IA/Regex em runtime', async () => {
    render(<PortaisAdminPanel />);

    fireEvent.change(screen.getByLabelText(/Motor de extração/i), {
      target: { value: 'ollama' },
    });
    fireEvent.change(screen.getByLabelText(/Modelo de IA/i), {
      target: { value: 'llama3.2' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Aplicar Motor/i }));

    await waitFor(() => {
      expect(balcaoService.atualizarIaConfig).toHaveBeenCalledWith({
        provider: 'ollama',
        model: 'llama3.2',
        base_url: '',
      });
      expect(screen.getByRole('status').textContent).toMatch(/ollama/i);
    });
  });

  it('envia chave de API pelo formulário quando informada', async () => {
    render(<PortaisAdminPanel />);

    fireEvent.change(screen.getByLabelText(/Motor de extração/i), {
      target: { value: 'cohere' },
    });
    fireEvent.change(screen.getByLabelText(/Chave de API de IA/i), {
      target: { value: 'cohere-key-xyz' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Aplicar Motor/i }));

    await waitFor(() => {
      expect(balcaoService.atualizarIaConfig).toHaveBeenCalledWith({
        provider: 'cohere',
        model: '',
        base_url: '',
        api_key: 'cohere-key-xyz',
      });
    });
  });

  it('testa a API de IA pelo botão Testar API', async () => {
    render(<PortaisAdminPanel />);

    fireEvent.change(screen.getByLabelText(/Motor de extração/i), {
      target: { value: 'cohere' },
    });
    fireEvent.change(screen.getByLabelText(/Chave de API de IA/i), {
      target: { value: 'cohere-key-xyz' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Testar API/i }));

    await waitFor(() => {
      expect(balcaoService.testarIaConfig).toHaveBeenCalledWith({
        provider: 'cohere',
        model: '',
        base_url: '',
        api_key: 'cohere-key-xyz',
      });
      expect(screen.getByText(/Teste OK/i)).toBeTruthy();
      expect(screen.getByText(/Conexão validada com sucesso/i)).toBeTruthy();
    });
  });

  it('lista portais ativos com rótulo e permite copiar o link completo a qualquer momento', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText },
      configurable: true,
    });
    vi.mocked(balcaoService.listarPortais).mockResolvedValue([
      {
        id: 'portal-ativo-1',
        rotulo: 'WhatsApp',
        ativo: true,
        criado_em: '2026-11-14T09:00:00Z',
        token: 'tok-ativo-123',
      },
    ]);
    vi.mocked(balcaoService.criarPortal).mockResolvedValue({
      id: 'portal-novo-2',
      rotulo: 'QR Evento',
      token: 'tok-novo-456',
      ativo: true,
      criado_em: '2026-11-14T09:05:00Z',
    });

    render(<PortaisAdminPanel />);

    await waitFor(() => {
      expect(screen.getByText('WhatsApp')).toBeTruthy();
    });

    fireEvent.click(screen.getByRole('button', { name: /Copiar Link/i }));
    expect(writeText).toHaveBeenCalledWith(`${window.location.origin}/portal/tok-ativo-123`);

    fireEvent.change(screen.getByLabelText(/Rótulo opcional do novo portal/i), {
      target: { value: 'QR Evento' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Gerar Novo Portal/i }));

    await waitFor(() => {
      expect(balcaoService.criarPortal).toHaveBeenCalledWith('QR Evento');
      expect(screen.getByText('QR Evento')).toBeTruthy();
    });
  });
});
