import axios from 'axios';
import { useAuthStore } from '../stores/useAuthStore';

export const api = axios.create({
  // Vazio (relativo) por padrão: a requisição vai para o próprio host que
  // serviu a página (same-origin) e o rewrite em next.config.ts encaminha
  // para a API de verdade. Isso evita que o cookie de sessão HttpOnly se
  // perca por mismatch "localhost" vs "127.0.0.1" (ver comentário lá).
  // Só defina NEXT_PUBLIC_API_URL quando o front e a API realmente vivem em
  // hosts/domínios diferentes e cookies cross-site não se aplicam (ex.:
  // produção com subdomínios sob o mesmo domínio — ADR 018).
  baseURL: process.env.NEXT_PUBLIC_API_URL || '',
  // O cookie de sessão é HttpOnly: o navegador o anexa sozinho em toda
  // requisição para o backend, o JS nunca lê nem manipula seu valor.
  withCredentials: true,
});

// Interceptor de Resposta (Fail Fast)
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    const url: string = error.config?.url || '';
    const isTentativaDeLogin = url.includes('/api/v1/auth/login');

    // A própria tentativa de login rejeitada não deve disparar o
    // redirecionamento de sessão expirada: isso recarregava a página antes
    // do formulário conseguir exibir "Credenciais inválidas...".
    if (!isTentativaDeLogin && error.response && (error.response.status === 401 || error.response.status === 403)) {
      // Força o logout no frontend e limpa a store
      useAuthStore.getState().logout();

      // Redirecionamento impiedoso para a tela de login
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);
