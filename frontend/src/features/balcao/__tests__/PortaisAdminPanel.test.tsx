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
      expect(screen.getByText(/\/portal\/token-secreto-abc/)).toBeTruthy();
    });

    fireEvent.change(screen.getByLabelText(/ID do portal para revogar/i), {
      target: { value: 'portal-uuid-1' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Revogar Portal/i }));

    await waitFor(() => {
      expect(screen.getByRole('status').textContent).toMatch(/portal-uuid-1 revogado/i);
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
});
