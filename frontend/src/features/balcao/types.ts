export type StatusEntrada = 'PENDENTE' | 'EFETIVADA' | 'DESCARTADA';

export interface PortalEntradaResposta {
  mensagem: string;
}

export interface PortalCriadoResposta {
  id: string;
  token: string;
  ativo: boolean;
  criado_em: string;
}

export interface PortalRevogadoResposta {
  id: string;
  ativo: boolean;
}

export interface PortalResumo {
  id: string;
  ativo: boolean;
  criado_em: string;
}

export interface AnexoResumo {
  id: string;
  mime_type: string;
  tamanho_bytes: number;
}

export interface SugestaoResponse {
  id: string;
  entrada_similar_id?: string | null;
  atendimento_relacionado_id?: string | null;
  score_similaridade: number;
  motivo: string;
}

export interface DadosExtraidosBalcao {
  nome?: string | null;
  telefone?: string | null;
  email?: string | null;
  municipio_id?: string | null;
  municipio_nome?: string | null;
  cpf_presente?: boolean;
  ia_complementou?: boolean;
  municipios_candidatos?: string[];
  municipios_candidatos_opcoes?: Array<{ id: string; nome: string }>;
  [key: string]: unknown;
}

export interface EntradaResumo {
  id: string;
  status: StatusEntrada;
  texto_original: string;
  dados_extraidos: DadosExtraidosBalcao;
  criado_em: string;
}

export interface EntradaDetalhe extends EntradaResumo {
  sugestoes: SugestaoResponse[];
  anexos: AnexoResumo[];
}

export interface EfetivarRequest {
  atendido_id?: string | null;
  nome?: string | null;
  telefone?: string | null;
  email?: string | null;
  municipio_id?: string | null;
  resumo?: string | null;
}

export interface EfetivarResponse {
  atendimento_id: string;
  atendido_id: string;
  protocolo: string;
}

export interface DescartarRequest {
  motivo?: string | null;
}

export interface DescartarResponse {
  id: string;
  status: StatusEntrada;
}

export interface EventoTimeline {
  tipo: 'ATENDIMENTO' | 'RESOLUCAO' | string;
  id: string;
  protocolo?: string | null;
  tipo_evento?: string | null;
  resumo?: string | null;
  ocorrido_em: string;
}

export interface AnexoCriadoResposta {
  id: string;
  mime_type: string;
  tamanho_bytes: number;
}

export interface ResolverRequest {
  despacho?: string | null;
  evidencia_anexo_id?: string | null;
}

export interface ResolverResponse {
  id: string;
  atendimento_id: string;
  resolvido_em: string;
}

export interface IaConfigResposta {
  provider: string;
  model: string;
  base_url: string;
  api_key_configurada: boolean;
  provedores_suportados: string[];
}

export interface IaConfigAtualizarRequest {
  provider: string;
  model: string;
  base_url: string;
  api_key?: string;
  limpar_api_key?: boolean;
}

export interface IaConfigTestarRequest {
  provider?: string;
  model?: string;
  base_url?: string;
  api_key?: string;
}

export interface IaConfigTesteResposta {
  ok: boolean;
  provider: string;
  model: string;
  latencia_ms: number;
  detalhe: string;
  resultado: Record<string, string>;
}

export interface PedidoMapaItem {
  id: string;
  tipo: 'PENDENTE' | 'EM_ANDAMENTO' | string;
  resumo: string;
  nome_atendido?: string | null;
  municipio_id: string;
  municipio_nome: string;
  latitude: number;
  longitude: number;
  criado_em: string;
}

export interface GrafoNo {
  id: string;
  tipo: 'ATENDIDO' | 'ATENDIMENTO' | 'MUNICIPIO' | string;
  rotulo: string;
}

export interface GrafoAresta {
  origem: string;
  destino: string;
  tipo: string;
}

export interface GrafoResposta {
  nos: GrafoNo[];
  arestas: GrafoAresta[];
}

interface AxiosErrorLike {
  response?: {
    status?: number;
    data?: {
      detail?: string | Array<{ msg?: string }>;
      title?: string;
      message?: string;
    };
  };
}

export function extrairMensagemErroApi(error: unknown, fallback: string): string {
  const err = error as AxiosErrorLike | null | undefined;
  const data = err?.response?.data;
  if (typeof data?.detail === 'string' && data.detail.trim()) {
    return data.detail;
  }
  if (Array.isArray(data?.detail) && data.detail.length > 0) {
    const msgs = data.detail.map((d) => d?.msg).filter(Boolean);
    if (msgs.length > 0) return msgs.join('; ');
  }
  if (typeof data?.title === 'string' && data.title.trim()) {
    return data.title;
  }
  if (typeof data?.message === 'string' && data.message.trim()) {
    return data.message;
  }
  return fallback;
}

