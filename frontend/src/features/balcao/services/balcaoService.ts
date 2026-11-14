import { api } from '@/services/api';
import type {
  AnexoCriadoResposta,
  DescartarRequest,
  DescartarResponse,
  EfetivarRequest,
  EfetivarResponse,
  EntradaDetalhe,
  EntradaResumo,
  EventoTimeline,
  GrafoResposta,
  IaConfigResposta,
  PortalCriadoResposta,
  PortalEntradaResposta,
  PortalRevogadoResposta,
  ResolverRequest,
  ResolverResponse,
  StatusEntrada,
} from '../types';

export const LIMITE_ANEXO_BYTES = 10 * 1024 * 1024; // 10 MB
export const TIPOS_ANEXO_PERMITIDOS = [
  'image/jpeg',
  'image/png',
  'image/webp',
  'application/pdf',
] as const;

export const balcaoService = {
  async enviarEntradaPortal(
    token: string,
    texto: string,
    anexo?: File | null
  ): Promise<PortalEntradaResposta> {
    const formData = new FormData();
    formData.append('texto', texto);
    if (anexo) {
      formData.append('anexo', anexo);
    }
    const res = await api.post<PortalEntradaResposta>(
      `/api/v1/portal/${encodeURIComponent(token)}/entradas`,
      formData
    );
    return res.data;
  },

  async listarEntradas(status?: StatusEntrada): Promise<EntradaResumo[]> {
    const res = await api.get<EntradaResumo[]>('/api/v1/balcao/entradas', {
      params: status ? { status } : undefined,
    });
    return res.data;
  },

  async obterEntrada(idEntrada: string): Promise<EntradaDetalhe> {
    const res = await api.get<EntradaDetalhe>(`/api/v1/balcao/entradas/${idEntrada}`);
    return res.data;
  },

  async analisarEntrada(idEntrada: string): Promise<EntradaDetalhe> {
    const res = await api.post<EntradaDetalhe>(`/api/v1/balcao/entradas/${idEntrada}/analisar`);
    return res.data;
  },

  async efetivarEntrada(idEntrada: string, payload: EfetivarRequest): Promise<EfetivarResponse> {
    const res = await api.post<EfetivarResponse>(
      `/api/v1/balcao/entradas/${idEntrada}/efetivar`,
      payload
    );
    return res.data;
  },

  async descartarEntrada(idEntrada: string, payload: DescartarRequest): Promise<DescartarResponse> {
    const res = await api.post<DescartarResponse>(
      `/api/v1/balcao/entradas/${idEntrada}/descartar`,
      payload
    );
    return res.data;
  },

  async obterTimelineAtendido(idAtendido: string): Promise<EventoTimeline[]> {
    const res = await api.get<EventoTimeline[]>(
      `/api/v1/balcao/atendidos/${idAtendido}/timeline`
    );
    return res.data;
  },

  urlDownloadAnexo(idAnexo: string): string {
    return `/api/v1/balcao/anexos/${idAnexo}`;
  },

  async anexarAoAtendimento(idAtendimento: string, arquivo: File): Promise<AnexoCriadoResposta> {
    const formData = new FormData();
    formData.append('anexo', arquivo);
    const res = await api.post<AnexoCriadoResposta>(
      `/api/v1/balcao/atendimentos/${idAtendimento}/anexos`,
      formData
    );
    return res.data;
  },

  async resolverAtendimento(
    idAtendimento: string,
    payload: ResolverRequest
  ): Promise<ResolverResponse> {
    const res = await api.post<ResolverResponse>(
      `/api/v1/balcao/atendimentos/${idAtendimento}/resolver`,
      payload
    );
    return res.data;
  },

  async criarPortal(): Promise<PortalCriadoResposta> {
    const res = await api.post<PortalCriadoResposta>('/api/v1/balcao/portais');
    return res.data;
  },

  async revogarPortal(idPortal: string): Promise<PortalRevogadoResposta> {
    const res = await api.post<PortalRevogadoResposta>(
      `/api/v1/balcao/portais/${idPortal}/revogar`
    );
    return res.data;
  },

  async obterGrafo(): Promise<GrafoResposta> {
    const res = await api.get<GrafoResposta>('/api/v1/balcao/grafo');
    return res.data;
  },

  async obterIaConfig(): Promise<IaConfigResposta> {
    const res = await api.get<IaConfigResposta>('/api/v1/balcao/ia-config');
    return res.data;
  },

  async atualizarIaConfig(payload: {
    provider: string;
    model: string;
    base_url: string;
  }): Promise<IaConfigResposta> {
    const res = await api.put<IaConfigResposta>('/api/v1/balcao/ia-config', payload);
    return res.data;
  },
};

