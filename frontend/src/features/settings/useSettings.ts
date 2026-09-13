import { useState, useCallback, useEffect } from 'react';
import { api } from '@/services/api';

export interface TenantProfile {
  id_tenant: string;
  nm_mandato: string;
  ds_cargo_mandato: string;
  cd_cargo: number | null;
  ds_cargo: string | null;
  nr_partido: number | null;
  sg_partido: string | null;
  cd_ibge_base: string | null;
  nm_municipio_base: string | null;
  is_ativo: boolean;
  created_at: string;
}

export interface TenantProfileUpdate {
  nm_mandato?: string;
  cd_cargo?: number | null;
  nr_partido?: number | null;
  cd_ibge_base?: string | null;
}

export interface CargoOption {
  cd_cargo: number;
  ds_cargo: string;
}

export interface PartidoOption {
  nr_partido: number;
  sg_partido: string;
  nm_partido: string;
}

export interface MunicipioOption {
  cd_ibge_7: string;
  nm_municipio: string;
}

export interface FormOptions {
  cargos: CargoOption[];
  partidos: PartidoOption[];
  municipios: MunicipioOption[];
}

export type TeamRole = 'admin' | 'operador' | 'leitor';

export interface TeamMember {
  id: string;
  email: string;
  role: TeamRole;
  is_active: boolean;
  created_at: string;
}

export interface TeamMemberCreate {
  email: string;
  password: string;
  role: TeamRole;
}

export interface TeamMemberUpdatePayload {
  role?: TeamRole;
  is_active?: boolean;
  password?: string;
}

export function useSettings(isAdmin: boolean) {
  const [profile, setProfile] = useState<TenantProfile | null>(null);
  const [options, setOptions] = useState<FormOptions | null>(null);
  const [team, setTeam] = useState<TeamMember[]>([]);
  const [isLoadingProfile, setIsLoadingProfile] = useState(true);
  const [isLoadingTeam, setIsLoadingTeam] = useState(isAdmin);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchProfile = useCallback(async () => {
    setIsLoadingProfile(true);
    try {
      const [profileRes, optionsRes] = await Promise.all([
        api.get('/api/v1/gabinete/perfil'),
        api.get('/api/v1/gabinete/perfil/opcoes'),
      ]);
      setProfile(profileRes.data);
      setOptions(optionsRes.data);
    } catch (error) {
      console.error('Erro ao buscar perfil do gabinete', error);
    } finally {
      setIsLoadingProfile(false);
    }
  }, []);

  const fetchTeam = useCallback(async () => {
    setIsLoadingTeam(true);
    try {
      const response = await api.get('/api/v1/gabinete/usuarios');
      setTeam(response.data);
    } catch (error) {
      console.error('Erro ao buscar equipe do gabinete', error);
    } finally {
      setIsLoadingTeam(false);
    }
  }, []);

  useEffect(() => {
    setTimeout(() => {
      fetchProfile();
      if (isAdmin) fetchTeam();
    }, 0);
  }, [fetchProfile, fetchTeam, isAdmin]);

  const updateProfile = useCallback(async (data: TenantProfileUpdate): Promise<boolean> => {
    setIsSubmitting(true);
    try {
      const response = await api.put('/api/v1/gabinete/perfil', data);
      setProfile(response.data);
      return true;
    } catch (error) {
      console.error('Erro ao atualizar perfil do gabinete', error);
      return false;
    } finally {
      setIsSubmitting(false);
    }
  }, []);

  const inviteMember = useCallback(async (data: TeamMemberCreate): Promise<{ ok: true } | { ok: false; status?: number }> => {
    setIsSubmitting(true);
    try {
      await api.post('/api/v1/gabinete/usuarios', data);
      await fetchTeam();
      return { ok: true };
    } catch (error: unknown) {
      console.error('Erro ao convidar membro para o gabinete', error);
      const status = (error as { response?: { status?: number } })?.response?.status;
      return { ok: false, status };
    } finally {
      setIsSubmitting(false);
    }
  }, [fetchTeam]);

  const updateMember = useCallback(async (id: string, data: TeamMemberUpdatePayload): Promise<boolean> => {
    try {
      await api.patch(`/api/v1/gabinete/usuarios/${id}`, data);
      await fetchTeam();
      return true;
    } catch (error) {
      console.error('Erro ao atualizar membro do gabinete', error);
      return false;
    }
  }, [fetchTeam]);

  const changePassword = useCallback(async (senhaAtual: string, novaSenha: string): Promise<{ ok: true } | { ok: false; message: string }> => {
    setIsSubmitting(true);
    try {
      await api.post('/api/v1/auth/trocar-senha', { senha_atual: senhaAtual, nova_senha: novaSenha });
      return { ok: true };
    } catch (error: unknown) {
      const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      return { ok: false, message: detail || 'Não foi possível alterar a senha.' };
    } finally {
      setIsSubmitting(false);
    }
  }, []);

  const exportGabineteData = useCallback(async (): Promise<boolean> => {
    try {
      const response = await api.get('/api/v1/gabinete/exportar-dados', { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'text/csv' }));
      const link = document.createElement('a');
      link.href = url;
      link.download = 'gabinete_export.csv';
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      return true;
    } catch (error) {
      console.error('Erro ao exportar dados do gabinete', error);
      return false;
    }
  }, []);

  return {
    profile,
    options,
    team,
    isLoadingProfile,
    isLoadingTeam,
    isSubmitting,
    updateProfile,
    inviteMember,
    updateMember,
    changePassword,
    exportGabineteData,
  };
}
