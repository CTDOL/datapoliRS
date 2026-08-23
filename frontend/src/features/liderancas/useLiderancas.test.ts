import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useLiderancas } from './useLiderancas';
import { api } from '@/services/api';

vi.mock('@/services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

const mockedGet = vi.mocked(api.get);
const mockedDelete = vi.mocked(api.delete);

describe('useLiderancas', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedGet.mockResolvedValue({
      data: { items: [{ id_lideranca: 'x' }], total: 21, total_pages: 2 },
    });
    mockedDelete.mockResolvedValue({ data: {} });
  });

  it('busca a primeira página imediatamente ao montar, sem esperar o debounce de busca', async () => {
    renderHook(() => useLiderancas());

    await waitFor(() => expect(mockedGet).toHaveBeenCalledTimes(1));
    expect(mockedGet).toHaveBeenCalledWith(
      '/api/v1/gabinete/liderancas',
      expect.objectContaining({ params: expect.objectContaining({ page: 1 }) })
    );
  });

  it('recua para a página anterior ao excluir o último item restante de uma página', async () => {
    const { result } = renderHook(() => useLiderancas());
    await waitFor(() => expect(mockedGet).toHaveBeenCalledTimes(1));

    act(() => {
      result.current.setPage(2);
    });
    await waitFor(() => expect(mockedGet).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(result.current.page).toBe(2));

    mockedGet
      .mockResolvedValueOnce({ data: { items: [], total: 20, total_pages: 1 } })
      .mockResolvedValueOnce({ data: { items: [{ id_lideranca: 'a' }], total: 20, total_pages: 1 } });

    await act(async () => {
      await result.current.deleteLideranca('ultima');
    });

    expect(result.current.page).toBe(1);
    expect(mockedDelete).toHaveBeenCalledWith('/api/v1/gabinete/liderancas/ultima');
  });
});
