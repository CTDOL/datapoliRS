'use client';

import { useState } from 'react';
import { Download, KeyRound, Loader2, Lock, ShieldAlert } from 'lucide-react';

interface Props {
  isAdmin: boolean;
  isSubmitting: boolean;
  onChangePassword: (senhaAtual: string, novaSenha: string) => Promise<{ ok: true } | { ok: false; message: string }>;
  onExportData: () => Promise<boolean>;
}

export function SegurancaSettingsTab({ isAdmin, isSubmitting, onChangePassword, onExportData }: Props) {
  const [senhaAtual, setSenhaAtual] = useState('');
  const [novaSenha, setNovaSenha] = useState('');
  const [confirmacao, setConfirmacao] = useState('');
  const [passwordFeedback, setPasswordFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [isExporting, setIsExporting] = useState(false);
  const [exportError, setExportError] = useState(false);

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordFeedback(null);

    if (novaSenha !== confirmacao) {
      setPasswordFeedback({ type: 'error', message: 'A confirmação não corresponde à nova senha.' });
      return;
    }

    const result = await onChangePassword(senhaAtual, novaSenha);
    if (result.ok) {
      setPasswordFeedback({ type: 'success', message: 'Senha alterada com sucesso.' });
      setSenhaAtual('');
      setNovaSenha('');
      setConfirmacao('');
    } else {
      setPasswordFeedback({ type: 'error', message: result.message });
    }
  };

  const handleExport = async () => {
    setIsExporting(true);
    setExportError(false);
    const success = await onExportData();
    if (!success) setExportError(true);
    setIsExporting(false);
  };

  return (
    <div className="max-w-2xl space-y-10">
      <div>
        <div className="flex items-center gap-3 mb-5">
          <div className="w-10 h-10 bg-purple-500/10 rounded-xl flex items-center justify-center border border-purple-500/20">
            <Lock className="w-5 h-5 text-purple-400" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">Segurança da Conta</h2>
            <p className="text-sm text-zinc-400">Altere a senha da sua própria conta.</p>
          </div>
        </div>

        <form onSubmit={handlePasswordSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-zinc-300 uppercase mb-1.5">Senha Atual</label>
            <input
              type="password"
              required
              value={senhaAtual}
              onChange={(e) => setSenhaAtual(e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-white outline-none focus:ring-2 focus:ring-purple-500/50"
            />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-zinc-300 uppercase mb-1.5">Nova Senha</label>
              <input
                type="password"
                required
                minLength={8}
                value={novaSenha}
                onChange={(e) => setNovaSenha(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-white outline-none focus:ring-2 focus:ring-purple-500/50"
                placeholder="Mínimo 8 caracteres"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-zinc-300 uppercase mb-1.5">Confirmação</label>
              <input
                type="password"
                required
                minLength={8}
                value={confirmacao}
                onChange={(e) => setConfirmacao(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-white outline-none focus:ring-2 focus:ring-purple-500/50"
              />
            </div>
          </div>

          {passwordFeedback && (
            <p className={`text-sm ${passwordFeedback.type === 'success' ? 'text-emerald-400' : 'text-red-400'}`}>
              {passwordFeedback.message}
            </p>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="bg-purple-600 hover:bg-purple-500 text-white px-5 py-2.5 rounded-xl font-medium transition-all shadow-lg flex items-center gap-2 disabled:opacity-70"
          >
            {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <KeyRound className="w-4 h-4" />}
            Alterar Senha
          </button>
        </form>
      </div>

      <div className="pt-6 border-t border-zinc-800/60">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 bg-purple-500/10 rounded-xl flex items-center justify-center border border-purple-500/20">
            <ShieldAlert className="w-5 h-5 text-purple-400" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">Exportação de Dados (LGPD/Backup)</h2>
            <p className="text-sm text-zinc-400">Baixe todas as lideranças e emendas do mandato em CSV.</p>
          </div>
        </div>

        {isAdmin ? (
          <button
            onClick={handleExport}
            disabled={isExporting}
            className="px-5 py-2.5 rounded-xl border border-zinc-700 text-zinc-200 hover:bg-zinc-800 transition-colors flex items-center gap-2 disabled:opacity-70"
          >
            {isExporting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
            Exportar Dados do Gabinete
          </button>
        ) : (
          <p className="text-xs text-zinc-500">Apenas administradores podem exportar os dados do gabinete.</p>
        )}
        {exportError && <p className="text-sm text-red-400 mt-2">Não foi possível gerar a exportação.</p>}
      </div>
    </div>
  );
}
