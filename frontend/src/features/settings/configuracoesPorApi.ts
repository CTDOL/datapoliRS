/** Agrupamento das configurações globais por API/módulo (a tela do super-admin mostra uma seção por grupo). */
export interface GrupoApi {
  id: string;
  titulo: string;
  descricao: string;
  chaves: string[];
}

export const GRUPOS_API: GrupoApi[] = [
  {
    id: 'pleito',
    titulo: 'Pleito e TSE',
    descricao: 'Qual eleição o sistema usa por padrão nas buscas.',
    chaves: ['eleitoral.election_year', 'eleitoral.tse_codigo_eleicao', 'eleitoral.default_cargo_code'],
  },
  {
    id: 'votacao',
    titulo: 'Votação e candidatos',
    descricao: 'Resultados de votação e busca de candidatos.',
    chaves: ['rate_limit.voting.times', 'rate_limit.voting.seconds', 'cache_ttl.candidate_votes'],
  },
  {
    id: 'eleicoes',
    titulo: 'Eleições e cargos',
    descricao: 'Listas de eleições e de cargos.',
    chaves: ['cache_ttl.eleicoes', 'cache_ttl.cargos'],
  },
  {
    id: 'geo',
    titulo: 'Mapa e geografia',
    descricao: 'Mapa dos municípios do Rio Grande do Sul.',
    chaves: ['rate_limit.geo.times', 'rate_limit.geo.seconds', 'cache_ttl.geojson_municipios'],
  },
  {
    id: 'gabinete',
    titulo: 'Gabinete',
    descricao: 'Limites de uso das telas de cada gabinete.',
    chaves: [
      'rate_limit.cabinet.times', 'rate_limit.cabinet.seconds',
      'rate_limit.amendments.times', 'rate_limit.amendments.seconds',
      'rate_limit.legislative.times', 'rate_limit.legislative.seconds',
      'rate_limit.tasks.times', 'rate_limit.tasks.seconds',
      'rate_limit.tenant.times', 'rate_limit.tenant.seconds',
    ],
  },
  {
    id: 'autenticacao',
    titulo: 'Autenticação',
    descricao: 'Proteção contra tentativas repetidas de login e troca de senha.',
    chaves: ['rate_limit.login.times', 'rate_limit.login.seconds', 'rate_limit.trocar_senha.times', 'rate_limit.trocar_senha.seconds'],
  },
  {
    id: 'sistema',
    titulo: 'Sistema',
    descricao: 'Somente leitura. Mudar aqui não altera o ambiente real.',
    chaves: ['ambiente.tipo'],
  },
];

/** Texto de tela para cada chave: rótulo em português comum e, se preciso, uma ajuda que muda com o valor. */
export interface Rotulo {
  texto: string;
  ajuda?: (valor: string) => string;
}

const emHoras = (valor: string) => {
  const segundos = Number(valor);
  if (!Number.isFinite(segundos) || segundos <= 0) return 'Valor inválido';
  if (segundos % 86400 === 0) return `Equivale a ${segundos / 86400} dia(s)`;
  if (segundos % 3600 === 0) return `Equivale a ${segundos / 3600} hora(s)`;
  return `Equivale a ${segundos} segundo(s)`;
};

const limite = (chave: string) => (valor: string) => `Máximo de ${valor} pedidos a cada janela de tempo (${chave})`;

export const ROTULOS: Record<string, Rotulo> = {
  'eleitoral.default_cargo_code': { texto: 'Cargo usado quando a busca não escolhe um', ajuda: (v) => `Código ${v} (7 = Deputado Estadual)` },
  'eleitoral.election_year': { texto: 'Ano da eleição usado quando a busca não escolhe um' },
  'eleitoral.tse_codigo_eleicao': { texto: 'Código da eleição no TSE (DivulgaCandContas)' },
  'cache_ttl.candidate_votes': { texto: 'Guardar votos de cada candidato por', ajuda: emHoras },
  'cache_ttl.eleicoes': { texto: 'Guardar a lista de eleições por', ajuda: emHoras },
  'cache_ttl.cargos': { texto: 'Guardar a lista de cargos por', ajuda: emHoras },
  'cache_ttl.geojson_municipios': { texto: 'Guardar o mapa dos municípios por', ajuda: emHoras },
  'rate_limit.voting.times': { texto: 'Pedidos de votação e candidatos permitidos', ajuda: limite('votacao') },
  'rate_limit.voting.seconds': { texto: 'Janela de tempo da votação e candidatos (segundos)' },
  'rate_limit.geo.times': { texto: 'Pedidos do mapa permitidos', ajuda: limite('mapa') },
  'rate_limit.geo.seconds': { texto: 'Janela de tempo do mapa (segundos)' },
  'rate_limit.cabinet.times': { texto: 'Pedidos de lideranças permitidos', ajuda: limite('lideranças') },
  'rate_limit.cabinet.seconds': { texto: 'Janela de tempo de lideranças (segundos)' },
  'rate_limit.amendments.times': { texto: 'Pedidos de emendas permitidos', ajuda: limite('emendas') },
  'rate_limit.amendments.seconds': { texto: 'Janela de tempo de emendas (segundos)' },
  'rate_limit.legislative.times': { texto: 'Pedidos de projetos de lei permitidos', ajuda: limite('projetos de lei') },
  'rate_limit.legislative.seconds': { texto: 'Janela de tempo de projetos de lei (segundos)' },
  'rate_limit.tasks.times': { texto: 'Pedidos de tarefas permitidos', ajuda: limite('tarefas') },
  'rate_limit.tasks.seconds': { texto: 'Janela de tempo de tarefas (segundos)' },
  'rate_limit.tenant.times': { texto: 'Pedidos de configurações do gabinete permitidos', ajuda: limite('configurações') },
  'rate_limit.tenant.seconds': { texto: 'Janela de tempo das configurações do gabinete (segundos)' },
  'rate_limit.login.times': { texto: 'Tentativas de login permitidas', ajuda: (v) => `Máximo de ${v} tentativas por janela de tempo` },
  'rate_limit.login.seconds': { texto: 'Janela de tempo do login (segundos)' },
  'rate_limit.trocar_senha.times': { texto: 'Trocas de senha permitidas', ajuda: (v) => `Máximo de ${v} trocas por janela de tempo` },
  'rate_limit.trocar_senha.seconds': { texto: 'Janela de tempo da troca de senha (segundos)' },
  'ambiente.tipo': { texto: 'Tipo de ambiente' },
};

/** Chaves que aparecem na tela, mas não podem ser editadas por ela. */
export const CHAVES_SOMENTE_LEITURA = ['ambiente.tipo'];
