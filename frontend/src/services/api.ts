import axios from 'axios';
import { useAuthStore } from '../stores/useAuthStore';

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
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
    if (error.response && (error.response.status === 401 || error.response.status === 403)) {
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
