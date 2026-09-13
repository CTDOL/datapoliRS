'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Loader2, KeyRound, Check } from 'lucide-react';
import { TeamMember } from './useSettings';

interface Props {
  isOpen: boolean;
  member: TeamMember | null;
  onClose: () => void;
  onSubmit: (id: string, data: { password: string }) => Promise<boolean>;
}

export function ResetPasswordModal({ isOpen, member, onClose, onSubmit }: Props) {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleClose = () => {
    setPassword('');
    setConfirmPassword('');
    setError(null);
    setSuccess(false);
    onClose();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!member) return;
    setError(null);

    if (password.length < 8) {
      setError('A nova senha deve ter no mínimo 8 caracteres.');
      return;
    }

    if (password !== confirmPassword) {
      setError('A confirmação de senha não confere.');
      return;
    }

    setIsSubmitting(true);
    const ok = await onSubmit(member.id, { password });
    setIsSubmitting(false);

    if (ok) {
      setSuccess(true);
      setTimeout(() => {
        handleClose();
      }, 1200);
    } else {
      setError('Não foi possível redefinir a senha do usuário. Tente novamente.');
    }
  };

  return (
    <AnimatePresence>
      {isOpen && member && (
        <>
          <motion.div
            key="backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={handleClose}
            className="fixed inset-0 bg-zinc-950/80 backdrop-blur-sm z-40"
          />
          <motion.div
            key="modal"
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-md bg-zinc-900 border border-zinc-700/50 rounded-3xl shadow-2xl z-50 overflow-hidden"
          >
            {/* Header */}
            <div className="p-6 border-b border-zinc-800 flex justify-between items-center">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-purple-500/10 rounded-xl flex items-center justify-center border border-purple-500/20">
                  <KeyRound className="w-5 h-5 text-purple-400" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-white">Redefinir Senha de Membro</h2>
                  <p className="text-xs text-zinc-400 truncate max-w-[220px]">{member.email}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={handleClose}
                className="text-zinc-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Body */}
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              {success ? (
                <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl flex items-center justify-center gap-2 text-emerald-400 font-medium text-sm">
                  <Check className="w-5 h-5" />
                  Senha redefinida com sucesso!
                </div>
              ) : (
                <>
                  <p className="text-xs text-zinc-400 leading-relaxed">
                    Como administrador, você pode atribuir uma nova senha para este assessor. Ele poderá acessar o sistema imediatamente com a nova credencial.
                  </p>

                  <div>
                    <label className="block text-xs font-semibold text-zinc-300 uppercase mb-1.5">
                      Nova Senha
                    </label>
                    <input
                      type="password"
                      required
                      minLength={8}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-white outline-none focus:ring-2 focus:ring-purple-500/50"
                      placeholder="Mínimo 8 caracteres"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-zinc-300 uppercase mb-1.5">
                      Confirmar Nova Senha
                    </label>
                    <input
                      type="password"
                      required
                      minLength={8}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-white outline-none focus:ring-2 focus:ring-purple-500/50"
                      placeholder="Repita a nova senha"
                    />
                  </div>

                  {error && (
                    <p className="text-xs text-red-400 bg-red-500/10 p-2.5 rounded-lg border border-red-500/20">
                      {error}
                    </p>
                  )}

                  <div className="pt-3 flex gap-3">
                    <button
                      type="button"
                      onClick={handleClose}
                      className="flex-1 px-4 py-3 rounded-xl border border-zinc-700 text-zinc-300 hover:bg-zinc-800 transition-colors text-sm font-medium"
                    >
                      Cancelar
                    </button>
                    <button
                      type="submit"
                      disabled={isSubmitting}
                      className="flex-1 bg-purple-600 hover:bg-purple-500 text-white px-4 py-3 rounded-xl font-medium shadow-lg flex items-center justify-center gap-2 text-sm disabled:opacity-70 transition-all"
                    >
                      {isSubmitting ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        'Salvar Senha'
                      )}
                    </button>
                  </div>
                </>
              )}
            </form>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
