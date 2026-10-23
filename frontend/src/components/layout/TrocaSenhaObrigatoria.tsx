'use client';

import { useState } from 'react';
import { useAuthStore } from '@/stores/useAuthStore';
import { api } from '@/services/api';

/**
 * Formulário bloqueante exibido quando a senha está pendente (ADR 037): o usuário novo
 * ou com senha redefinida pelo super-admin precisa trocá-la antes de usar o sistema.
 */
export function TrocaSenhaObrigatoria() {
  const user = useAuthStore((s) => s.user);
  const login = useAuthStore((s) => s.login);
  const [senhaAtual, setSenhaAtual] = useState('');
  const [senhaNova, setSenhaNova] = useState('');
  const [confirmacao, setConfirmacao] = useState('');
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  if (!user?.must_change_password) return null;

  const enviar = async (evento: React.FormEvent) => {
    evento.preventDefault();
    setErro(null);
    if (senhaNova.length < 8) {
      setErro('A nova senha precisa ter pelo menos 8 caracteres.');
      return;
    }
    if (senhaNova !== confirmacao) {
      setErro('A confirmação não confere com a nova senha.');
      return;
    }
    setEnviando(true);
    try {
      await api.post('/api/v1/auth/trocar-senha', { senha_atual: senhaAtual, nova_senha: senhaNova });
      login({ ...user, must_change_password: false });
    } catch {
      setErro('Não foi possível trocar a senha. Confira a senha atual.');
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div role="dialog" aria-modal="true" aria-labelledby="troca-senha-titulo"
         className="fixed inset-0 z-[1500] flex items-center justify-center bg-black/80 p-4">
      <form onSubmit={enviar} className="w-full max-w-sm rounded-2xl border border-zinc-800 bg-zinc-900 p-6 space-y-4">
        <h2 id="troca-senha-titulo" className="text-lg font-bold text-white">Troque sua senha</h2>
        <p className="text-sm text-zinc-400">Por segurança, defina uma senha pessoal antes de continuar.</p>

        <label className="block text-xs text-zinc-300">
          Senha atual
          <input type="password" value={senhaAtual} onChange={(e) => setSenhaAtual(e.target.value)} required
                 className="mt-1 w-full rounded-xl bg-zinc-950 border border-zinc-800 px-3 py-2 text-sm text-white" />
        </label>
        <label className="block text-xs text-zinc-300">
          Nova senha
          <input type="password" value={senhaNova} onChange={(e) => setSenhaNova(e.target.value)} required
                 className="mt-1 w-full rounded-xl bg-zinc-950 border border-zinc-800 px-3 py-2 text-sm text-white" />
        </label>
        <label className="block text-xs text-zinc-300">
          Confirmar nova senha
          <input type="password" value={confirmacao} onChange={(e) => setConfirmacao(e.target.value)} required
                 className="mt-1 w-full rounded-xl bg-zinc-950 border border-zinc-800 px-3 py-2 text-sm text-white" />
        </label>

        {erro && <p role="alert" className="text-sm text-red-400">{erro}</p>}

        <button type="submit" disabled={enviando}
                className="w-full rounded-xl bg-purple-600 hover:bg-purple-500 disabled:opacity-60 text-white font-medium py-2.5">
          {enviando ? 'Salvando...' : 'Salvar nova senha'}
        </button>
      </form>
    </div>
  );
}
