import axios from 'axios';
import { useAuthStore } from '../stores/useAuthStore';

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  withCredentials: true, // Necessário para enviar/receber cookies HttpOnly
});

// Interceptor de Requisição (pode ser usado para injetar headers genéricos como CSRF se necessário)
api.interceptors.request.use(
  (config) => {
    // Extrai o token do cookie cliente para enviar ao FastAPI (que exige Header Bearer)
    if (typeof document !== 'undefined') {
      const token = document.cookie.split('; ').find(row => row.startsWith('token='))?.split('=')[1];
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

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
