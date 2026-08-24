'use client';

import { useState } from 'react';
import { Loader2, ShieldAlert, UserPlus, Users } from 'lucide-react';
import { TeamMember, TeamMemberCreate, TeamRole } from './useSettings';
import { UserFormModal } from './UserFormModal';

interface Props {
  team: TeamMember[];
  isLoading: boolean;
  isSubmitting: boolean;
  isAdmin: boolean;
  currentUserEmail: string | null;
  onInvite: (data: TeamMemberCreate) => Promise<{ ok: true } | { ok: false; status?: number }>;
  onUpdateMember: (id: string, data: { role?: TeamRole; is_active?: boolean }) => Promise<boolean>;
}

const ROLE_LABELS: Record<TeamRole, string> = {
  admin: '👑 Admin',
  operador: '🏛️ Operador',
  leitor: '👁️ Leitor',
};

export function EquipeSettingsTab({ team, isLoading, isSubmitting, isAdmin, currentUserEmail, onInvite, onUpdateMember }: Props) {
  const [isModalOpen, setIsModalOpen] = useState(false);

  if (!isAdmin) {
    return (
      <div className="max-w-4xl flex flex-col items-center justify-center gap-3 py-16 text-center">
        <ShieldAlert className="w-8 h-8 text-zinc-600" />
        <p className="text-zinc-400">Apenas administradores podem gerenciar a equipe e os acessos do gabinete.</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl space-y-5">
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-purple-500/10 rounded-xl flex items-center justify-center border border-purple-500/20">
            <Users className="w-5 h-5 text-purple-400" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">Equipe & Gestão de Acessos</h2>
            <p className="text-sm text-zinc-400">Usuários com acesso a este gabinete.</p>
          </div>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="bg-purple-600 hover:bg-purple-500 text-white px-4 py-2.5 rounded-xl font-medium transition-all shadow-lg flex items-center gap-2"
        >
          <UserPlus className="w-4 h-4" />
          Convidar Membro
        </button>
      </div>

      <div className="rounded-2xl border border-zinc-800 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-zinc-900/60 text-zinc-400 uppercase text-xs">
            <tr>
              <th className="text-left px-4 py-3 font-semibold">E-mail</th>
              <th className="text-left px-4 py-3 font-semibold">Papel</th>
              <th className="text-left px-4 py-3 font-semibold">Criado em</th>
              <th className="text-left px-4 py-3 font-semibold">Status</th>
              <th className="text-right px-4 py-3 font-semibold">Ações</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={5} className="text-center py-10 text-zinc-500">
                  <Loader2 className="w-5 h-5 animate-spin mx-auto" />
                </td>
              </tr>
            ) : team.length === 0 ? (
              <tr>
                <td colSpan={5} className="text-center py-10 text-zinc-500">Nenhum usuário cadastrado.</td>
              </tr>
            ) : (
              team.map((member) => {
                const isSelf = member.email === currentUserEmail;
                return (
                  <tr key={member.id} className="border-t border-zinc-800/60">
                    <td className="px-4 py-3 text-white">{member.email}{isSelf && <span className="text-zinc-500 text-xs ml-2">(você)</span>}</td>
                    <td className="px-4 py-3">
                      <select
                        value={member.role}
                        onChange={(e) => onUpdateMember(member.id, { role: e.target.value as TeamRole })}
                        className="bg-zinc-950 border border-zinc-800 rounded-lg px-2 py-1.5 text-white outline-none focus:ring-2 focus:ring-purple-500/50 text-xs"
                      >
                        <option value="admin">{ROLE_LABELS.admin}</option>
                        <option value="operador">{ROLE_LABELS.operador}</option>
                        <option value="leitor">{ROLE_LABELS.leitor}</option>
                      </select>
                    </td>
                    <td className="px-4 py-3 text-zinc-400">{new Date(member.created_at).toLocaleDateString('pt-BR')}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${member.is_active ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'}`}>
                        {member.is_active ? '🟢 Ativo' : '🔴 Inativo'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => onUpdateMember(member.id, { is_active: !member.is_active })}
                        disabled={isSelf}
                        title={isSelf ? 'Você não pode desativar a própria conta' : undefined}
                        className="text-xs px-3 py-1.5 rounded-lg border border-zinc-700 text-zinc-300 hover:bg-zinc-800 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                      >
                        {member.is_active ? 'Desativar' : 'Ativar'}
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      <UserFormModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={onInvite}
        isSubmitting={isSubmitting}
      />
    </div>
  );
}
