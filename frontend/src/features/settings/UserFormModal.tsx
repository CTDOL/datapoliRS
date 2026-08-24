'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Loader2, UserPlus } from 'lucide-react';
import { TeamMemberCreate, TeamRole } from './useSettings';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: TeamMemberCreate) => Promise<{ ok: true } | { ok: false; status?: number }>;
  isSubmitting: boolean;
}

const EMPTY_FORM: TeamMemberCreate = { email: '', password: '', role: 'operador' };

export function UserFormModal({ isOpen, onClose, onSubmit, isSubmitting }: Props) {
  const [formData, setFormData] = useState<TeamMemberCreate>(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);

  const handleClose = () => {
    setFormData(EMPTY_FORM);
    setError(null);
    onClose();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    const result = await onSubmit(formData);
    if (result.ok) {
      handleClose();
    } else if (result.status === 409) {
      setError('Já existe um usuário cadastrado com este e-mail.');
    } else {
      setError('Não foi possível convidar o membro. Verifique os dados informados.');
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            key="backdrop"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={handleClose}
            className="fixed inset-0 bg-zinc-950/80 backdrop-blur-sm z-40"
          />
          <motion.div
            key="modal"
            initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-md bg-zinc-900 border border-zinc-700/50 rounded-3xl shadow-2xl z-50 overflow-hidden"
          >
            <div className="p-6 border-b border-zinc-800 flex justify-between items-center">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-purple-500/10 rounded-xl flex items-center justify-center border border-purple-500/20">
                  <UserPlus className="w-5 h-5 text-purple-400" />
                </div>
                <h2 className="text-xl font-bold text-white">Convidar Membro</h2>
              </div>
              <button onClick={handleClose} className="text-zinc-400 hover:text-white transition-colors">
                <X className="w-6 h-6" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-zinc-300 uppercase mb-1.5">E-mail</label>
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-white outline-none focus:ring-2 focus:ring-purple-500/50"
                  placeholder="membro@campanha.com.br"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-zinc-300 uppercase mb-1.5">Senha Inicial</label>
                <input
                  type="password"
                  required
                  minLength={8}
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-white outline-none focus:ring-2 focus:ring-purple-500/50"
                  placeholder="Mínimo 8 caracteres"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-zinc-300 uppercase mb-1.5">Papel</label>
                <select
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value as TeamRole })}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-white outline-none appearance-none focus:ring-2 focus:ring-purple-500/50"
                >
                  <option value="admin">👑 Admin</option>
                  <option value="operador">🏛️ Operador</option>
                  <option value="leitor">👁️ Leitor</option>
                </select>
              </div>

              {error && <p className="text-sm text-red-400">{error}</p>}

              <div className="pt-2 flex gap-3">
                <button type="button" onClick={handleClose} className="flex-1 px-4 py-3 rounded-xl border border-zinc-700 text-zinc-300 hover:bg-zinc-800 transition-colors">Cancelar</button>
                <button type="submit" disabled={isSubmitting} className="flex-1 bg-purple-600 hover:bg-purple-500 text-white px-4 py-3 rounded-xl font-medium shadow-lg flex justify-center disabled:opacity-70">
                  {isSubmitting ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Convidar'}
                </button>
              </div>
            </form>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
