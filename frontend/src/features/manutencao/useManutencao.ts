import { useCallback, useEffect, useState } from 'react';
import { api } from '@/services/api';

export interface SaudePleito {
  cd_eleicao: string;
  ano_eleicao: number;
  ds_eleicao: string;
  nr_turno: number;
  linhas_votacao: number;
  municipios_votacao: number;
  zonas_votacao: number;
  codigos_sem_cadastro: number;
  linhas_comparecimento: number;
}

export interface CargaEtl {
  id_carga: number;
  tipo: 'votacao' | 'comparecimento';
  ano_eleicao: number;
  cd_eleicoes: string[];
  arquivo_origem: string;
  sha256: string;
  tamanho_bytes: number;
  iniciado_em: string;
  concluido_em: string;
  status: 'sucesso' | 'falha';
  linhas_carregadas: number | null;
  erro: string | null;
  operador: string;
}

export interface JobEtl {
  id_job: number;
  tipo: 'votacao' | 'comparecimento';
  ano_eleicao: number;
  status: 'pendente' | 'executando' | 'concluido' | 'falha';
  solicitado_por: string;
  solicitado_em: string;
  iniciado_em: string | null;
  concluido_em: string | null;
  erro: string | null;
}

export const MUNICIPIOS_RS = 497;

export interface ConfiguracaoItem {
  chave: string;
  valor: string;
}
const INTERVALO_ATUALIZACAO_MS = 5000;

export function useManutencao() {
  const [saude, setSaude] = useState<SaudePleito[]>([]);
  const [cargas, setCargas] = useState<CargaEtl[]>([]);
  const [jobs, setJobs] = useState<JobEtl[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [erroEnvio, setErroEnvio] = useState<string | null>(null);
  const [cdAtivo, setCdAtivo] = useState<string | null>(null);
  const [erroAtivacao, setErroAtivacao] = useState<string | null>(null);

  const buscar = useCallback(() => {
    return Promise.all([
      api.get<SaudePleito[]>('/api/v1/admin/manutencao/saude'),
      api.get<CargaEtl[]>('/api/v1/admin/manutencao/cargas?limite=50'),
      api.get<JobEtl[]>('/api/v1/admin/manutencao/jobs?limite=20'),
      api.get<ConfiguracaoItem[]>('/api/v1/admin/configuracoes'),
    ])
      .then(([saudeRes, cargasRes, jobsRes, configRes]) => {
        setCdAtivo(configRes.data.find((c) => c.chave === 'eleitoral.tse_codigo_eleicao')?.valor ?? null);
        setSaude(saudeRes.data);
        setCargas(cargasRes.data);
        setJobs(jobsRes.data);
        setErro(null);
      })
      .catch(() => setErro('Não foi possível carregar os dados de manutenção.'))
      .finally(() => setIsLoading(false));
  }, []);

  useEffect(() => {
    buscar();
  }, [buscar]);

  // Enquanto houver job pendente ou em execução, atualiza só a fila (leve). A recarga completa
  // (saúde por pleito, que varre a votação) acontece uma vez, quando a fila esvazia.
  const atualizarJobs = useCallback(() => {
    return api.get<JobEtl[]>('/api/v1/admin/manutencao/jobs?limite=20')
      .then((res) => {
        setJobs(res.data);
        if (!res.data.some((j) => j.status === 'pendente' || j.status === 'executando')) buscar();
      })
      .catch(() => undefined);
  }, [buscar]);

  const haJobAtivo = jobs.some((j) => j.status === 'pendente' || j.status === 'executando');
  useEffect(() => {
    if (!haJobAtivo) return;
    const timer = setInterval(atualizarJobs, INTERVALO_ATUALIZACAO_MS);
    return () => clearInterval(timer);
  }, [haJobAtivo, atualizarJobs]);

  const recarregar = useCallback(() => {
    setIsLoading(true);
    buscar();
  }, [buscar]);

  const enfileirar = useCallback(
    async (tipo: 'votacao' | 'comparecimento', ano: number, confirmacao: string) => {
      setErroEnvio(null);
      try {
        await api.post('/api/v1/admin/manutencao/jobs', { tipo, ano, confirmacao });
        await buscar();
        return true;
      } catch (e: unknown) {
        const resposta = (e as { response?: { status?: number; data?: { detail?: string } } }).response;
        setErroEnvio(resposta?.data?.detail ?? 'Não foi possível enfileirar a carga.');
        return false;
      }
    },
    [buscar],
  );

  const ativarPleito = useCallback(
    async (cdEleicao: string, confirmacao: string, aceitarCodigos: boolean) => {
      setErroAtivacao(null);
      try {
        await api.post('/api/v1/admin/manutencao/ativar-pleito', {
          cd_eleicao: cdEleicao,
          confirmacao,
          aceitar_codigos_sem_cadastro: aceitarCodigos,
        });
        await buscar();
        return true;
      } catch (e: unknown) {
        const resposta = (e as { response?: { data?: { detail?: string } } }).response;
        setErroAtivacao(resposta?.data?.detail ?? 'Não foi possível ativar o pleito.');
        return false;
      }
    },
    [buscar],
  );

  return { saude, cargas, jobs, cdAtivo, isLoading, erro, erroEnvio, erroAtivacao, recarregar, enfileirar, ativarPleito };
}
