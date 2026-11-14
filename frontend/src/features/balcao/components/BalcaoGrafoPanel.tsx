'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Network,
  RefreshCw,
  AlertTriangle,
  Focus,
  X,
  ZoomIn,
  ZoomOut,
  Maximize2,
} from 'lucide-react';
import { balcaoService } from '../services/balcaoService';
import { extrairMensagemErroApi, type GrafoNo, type GrafoResposta } from '../types';

const ESTILOS_NO: Record<string, { fill: string; stroke: string; badge: string; label: string }> = {
  ATENDIDO: {
    fill: '#0284c7',
    stroke: '#38bdf8',
    badge: 'border-sky-500/40 bg-sky-500/10 text-sky-300',
    label: 'Atendido',
  },
  ATENDIMENTO: {
    fill: '#9333ea',
    stroke: '#c084fc',
    badge: 'border-purple-500/40 bg-purple-500/10 text-purple-300',
    label: 'Atendimento',
  },
  LIDERANCA: {
    fill: '#f59e0b',
    stroke: '#fbbf24',
    badge: 'border-amber-500/40 bg-amber-500/10 text-amber-300',
    label: 'Liderança',
  },
  MUNICIPIO: {
    fill: '#10b981',
    stroke: '#34d399',
    badge: 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300',
    label: 'Município',
  },
  CATEGORIA: {
    fill: '#ec4899',
    stroke: '#f472b6',
    badge: 'border-pink-500/40 bg-pink-500/10 text-pink-300',
    label: 'Categoria',
  },
};

const LARGURA = 820;
const ALTURA = 480;

interface SimNode {
  id: string;
  x: number;
  y: number;
  vx: number;
  vy: number;
}

export function BalcaoGrafoPanel() {
  const [grafo, setGrafo] = useState<GrafoResposta | null>(null);
  const [noSelecionado, setNoSelecionado] = useState<GrafoNo | null>(null);
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [modoLocal, setModoLocal] = useState(true);
  const [incluirResolvidos, setIncluirResolvidos] = useState(false);
  const [busca, setBusca] = useState('');
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [posicoes, setPosicoes] = useState<Record<string, { x: number; y: number }>>({});

  const simRef = useRef<Map<string, SimNode>>(new Map());
  const dragNodeRef = useRef<string | null>(null);
  const dragPanRef = useRef<{ startX: number; startY: number; origX: number; origY: number } | null>(
    null
  );
  const svgRef = useRef<SVGSVGElement | null>(null);
  const animarRef = useRef<() => void>(() => {});

  const carregar = useCallback(async (resolvidos: boolean) => {
    setCarregando(true);
    setErro(null);
    try {
      const dados = await balcaoService.obterGrafo({ incluir_resolvidos: resolvidos });
      setGrafo(dados);
    } catch (err) {
      setErro(extrairMensagemErroApi(err, 'Não foi possível carregar o grafo de correlações.'));
    } finally {
      setCarregando(false);
    }
  }, []);

  useEffect(() => {
    let cancelado = false;
    balcaoService
      .obterGrafo({ incluir_resolvidos: incluirResolvidos })
      .then((dados) => {
        if (!cancelado) {
          setGrafo(dados);
          setErro(null);
        }
      })
      .catch((err) => {
        if (!cancelado) {
          setErro(extrairMensagemErroApi(err, 'Não foi possível carregar o grafo de correlações.'));
        }
      })
      .finally(() => {
        if (!cancelado) setCarregando(false);
      });
    return () => {
      cancelado = true;
    };
  }, [incluirResolvidos]);

  const termo = busca.trim().toLowerCase();

  const { nosVisiveis, arestasVisiveis, grauPorNo } = useMemo(() => {
    if (!grafo) {
      return { nosVisiveis: [], arestasVisiveis: [], grauPorNo: new Map<string, number>() };
    }

    let nosFiltrados = grafo.nos;
    if (noSelecionado && modoLocal) {
      const idsVizinhos = new Set<string>([noSelecionado.id]);
      for (const a of grafo.arestas) {
        if (a.origem === noSelecionado.id) idsVizinhos.add(a.destino);
        if (a.destino === noSelecionado.id) idsVizinhos.add(a.origem);
      }
      nosFiltrados = grafo.nos.filter((n) => idsVizinhos.has(n.id));
    } else if (termo) {
      const casados = new Set(
        grafo.nos
          .filter(
            (n) =>
              n.rotulo.toLowerCase().includes(termo) ||
              (n.subtitulo ?? '').toLowerCase().includes(termo)
          )
          .map((n) => n.id)
      );
      nosFiltrados = grafo.nos.filter((n) => casados.has(n.id));
    }

    const idsVisiveis = new Set(nosFiltrados.map((n) => n.id));
    const arestasFiltradas = grafo.arestas.filter(
      (a) => idsVisiveis.has(a.origem) && idsVisiveis.has(a.destino)
    );

    const graus = new Map<string, number>();
    for (const a of arestasFiltradas) {
      graus.set(a.origem, (graus.get(a.origem) ?? 0) + 1);
      graus.set(a.destino, (graus.get(a.destino) ?? 0) + 1);
    }

    return { nosVisiveis: nosFiltrados, arestasVisiveis: arestasFiltradas, grauPorNo: graus };
  }, [grafo, noSelecionado, modoLocal, termo]);

  const focoAtivoId = hoveredId ?? noSelecionado?.id ?? null;

  const vizinhosFoco = useMemo(() => {
    const conjunto = new Set<string>();
    if (!focoAtivoId) return conjunto;
    conjunto.add(focoAtivoId);
    for (const a of arestasVisiveis) {
      if (a.origem === focoAtivoId) conjunto.add(a.destino);
      if (a.destino === focoAtivoId) conjunto.add(a.origem);
    }
    return conjunto;
  }, [focoAtivoId, arestasVisiveis]);

  // Simulação force-directed estilo Obsidian (repulsão + mola + gravidade central)
  useEffect(() => {
    if (nosVisiveis.length === 0) return;

    const cx = LARGURA / 2;
    const cy = ALTURA / 2;
    const mapa = new Map<string, SimNode>();

    nosVisiveis.forEach((no, idx) => {
      const anterior = simRef.current.get(no.id);
      if (anterior) {
        mapa.set(no.id, { ...anterior });
      } else {
        const ang = (2 * Math.PI * idx) / Math.max(nosVisiveis.length, 1);
        const raio = Math.min(180, 45 + nosVisiveis.length * 5);
        mapa.set(no.id, {
          id: no.id,
          x: cx + raio * Math.cos(ang),
          y: cy + raio * Math.sin(ang),
          vx: 0,
          vy: 0,
        });
      }
    });
    simRef.current = mapa;

    let rafId = 0;
    let ativo = true;
    let iteracoes = 0;

    const publicarPosicoes = () => {
      const snap: Record<string, { x: number; y: number }> = {};
      mapa.forEach((n, id) => {
        snap[id] = { x: n.x, y: n.y };
      });
      setPosicoes(snap);
    };

    // Garante posição inicial imediata na primeira renderização
    publicarPosicoes();

    const passo = () => {
      if (!ativo) return;
      const lista = Array.from(mapa.values());
      const repulsao = 3200;
      const compIdeal = 120;
      const kMola = 0.035;
      const gravidade = 0.014;
      const amortecimento = 0.8;

      for (let i = 0; i < lista.length; i++) {
        const a = lista[i];
        if (dragNodeRef.current === a.id) continue;

        // Gravidade suave para o centro
        a.vx += (cx - a.x) * gravidade;
        a.vy += (cy - a.y) * gravidade;

        for (let j = i + 1; j < lista.length; j++) {
          const b = lista[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const dist2 = Math.max(dx * dx + dy * dy, 25);
          const dist = Math.sqrt(dist2);
          const forca = repulsao / dist2;
          const fx = (dx / dist) * forca;
          const fy = (dy / dist) * forca;

          a.vx += fx;
          a.vy += fy;
          if (dragNodeRef.current !== b.id) {
            b.vx -= fx;
            b.vy -= fy;
          }
        }
      }

      for (const aresta of arestasVisiveis) {
        const o = mapa.get(aresta.origem);
        const d = mapa.get(aresta.destino);
        if (!o || !d) continue;
        const dx = d.x - o.x;
        const dy = d.y - o.y;
        const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 1);
        const deslocamento = dist - compIdeal;
        const fx = (dx / dist) * deslocamento * kMola;
        const fy = (dy / dist) * deslocamento * kMola;

        if (dragNodeRef.current !== o.id) {
          o.vx += fx;
          o.vy += fy;
        }
        if (dragNodeRef.current !== d.id) {
          d.vx -= fx;
          d.vy -= fy;
        }
      }

      let energia = 0;
      for (const n of lista) {
        if (dragNodeRef.current === n.id) {
          n.vx = 0;
          n.vy = 0;
          continue;
        }
        n.vx *= amortecimento;
        n.vy *= amortecimento;
        n.x += Math.max(-18, Math.min(18, n.vx));
        n.y += Math.max(-18, Math.min(18, n.vy));
        energia += Math.abs(n.vx) + Math.abs(n.vy);
      }

      iteracoes += 1;
      publicarPosicoes();

      if ((energia > 0.35 && iteracoes < 260) || dragNodeRef.current !== null) {
        rafId = requestAnimationFrame(passo);
      }
    };

    animarRef.current = () => {
      iteracoes = 0;
      cancelAnimationFrame(rafId);
      rafId = requestAnimationFrame(passo);
    };

    rafId = requestAnimationFrame(passo);
    return () => {
      ativo = false;
      cancelAnimationFrame(rafId);
    };
  }, [nosVisiveis, arestasVisiveis]);

  const converterPontoSvg = (clientX: number, clientY: number) => {
    const svg = svgRef.current;
    if (!svg) return { x: LARGURA / 2, y: ALTURA / 2 };
    const rect = svg.getBoundingClientRect();
    const sx = ((clientX - rect.left) / Math.max(rect.width, 1)) * LARGURA;
    const sy = ((clientY - rect.top) / Math.max(rect.height, 1)) * ALTURA;
    return {
      x: (sx - LARGURA / 2 - pan.x) / zoom + LARGURA / 2,
      y: (sy - ALTURA / 2 - pan.y) / zoom + ALTURA / 2,
    };
  };

  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (dragNodeRef.current) {
      const pt = converterPontoSvg(e.clientX, e.clientY);
      const no = simRef.current.get(dragNodeRef.current);
      if (no) {
        no.x = pt.x;
        no.y = pt.y;
        animarRef.current();
      }
    } else if (dragPanRef.current) {
      const dx = e.clientX - dragPanRef.current.startX;
      const dy = e.clientY - dragPanRef.current.startY;
      setPan({ x: dragPanRef.current.origX + dx, y: dragPanRef.current.origY + dy });
    }
  };

  const handleMouseUp = () => {
    dragNodeRef.current = null;
    dragPanRef.current = null;
  };

  const handleWheel = (e: React.WheelEvent<SVGSVGElement>) => {
    e.preventDefault();
    const fator = e.deltaY < 0 ? 1.1 : 0.9;
    setZoom((z) => Math.max(0.4, Math.min(2.8, Number((z * fator).toFixed(2)))));
  };

  const resetarCamera = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  const nosPorId = useMemo(() => {
    const mapa = new Map<string, GrafoNo>();
    for (const n of grafo?.nos ?? []) mapa.set(n.id, n);
    return mapa;
  }, [grafo]);

  const conexoesDoNo =
    grafo && noSelecionado
      ? grafo.arestas.filter(
          (a) => a.origem === noSelecionado.id || a.destino === noSelecionado.id
        )
      : [];

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-sm text-zinc-300">
          <Network className="h-4 w-4 text-purple-400" />
          <span>
            {grafo
              ? `${nosVisiveis.length} de ${grafo.nos.length} nós · ${arestasVisiveis.length} conexões`
              : 'Grafo de correlações do gabinete'}
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <input
            type="search"
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
            placeholder="Filtrar nó, intenção ou cidade..."
            aria-label="Filtrar grafo"
            className="w-52 rounded-lg border border-zinc-700 bg-zinc-950 px-2.5 py-1.5 text-xs text-white placeholder-zinc-500 focus:border-purple-500 focus:outline-none"
          />

          <label className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-800 bg-zinc-900 px-2.5 py-1.5 text-xs text-zinc-300 cursor-pointer">
            <input
              type="checkbox"
              checked={incluirResolvidos}
              onChange={(e) => setIncluirResolvidos(e.target.checked)}
              className="rounded border-zinc-600"
            />
            <span>Incluir resolvidos</span>
          </label>

          {noSelecionado && (
            <>
              <button
                type="button"
                onClick={() => setModoLocal((v) => !v)}
                className={`inline-flex items-center gap-1 rounded-lg border px-2.5 py-1.5 text-xs font-medium ${
                  modoLocal
                    ? 'border-purple-500/50 bg-purple-600/20 text-purple-200'
                    : 'border-zinc-700 bg-zinc-800 text-zinc-300'
                }`}
              >
                <Focus className="h-3.5 w-3.5" />
                <span>{modoLocal ? 'Grafo Local (1 salto)' : 'Grafo Completo'}</span>
              </button>
              <button
                type="button"
                onClick={() => setNoSelecionado(null)}
                className="inline-flex items-center gap-1 rounded-lg border border-zinc-700 bg-zinc-800 px-2.5 py-1.5 text-xs text-zinc-300 hover:bg-zinc-700"
              >
                <X className="h-3.5 w-3.5" />
                <span>Limpar foco</span>
              </button>
            </>
          )}

          <button
            type="button"
            onClick={() => carregar(incluirResolvidos)}
            disabled={carregando}
            className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-1.5 text-xs font-medium text-zinc-200 hover:bg-zinc-700"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${carregando ? 'animate-spin' : ''}`} />
            <span>Atualizar</span>
          </button>
        </div>
      </div>

      {erro && (
        <div
          role="alert"
          className="flex items-center gap-2 rounded-xl border border-rose-300 bg-rose-50 p-3 text-sm text-rose-900"
        >
          <AlertTriangle className="h-4 w-4 text-rose-400" />
          <span>{erro}</span>
        </div>
      )}

      {!carregando && grafo && grafo.nos.length === 0 && (
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-8 text-center text-sm text-zinc-400">
          Nenhuma correlação ativa registrada ainda. Efetive entradas do portal para gerar o grafo.
        </div>
      )}

      {grafo && grafo.nos.length > 0 && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <div className="lg:col-span-2 rounded-2xl border border-zinc-800 bg-zinc-950 p-3 space-y-2.5">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex flex-wrap items-center gap-1.5 text-[11px]">
                {Object.entries(ESTILOS_NO).map(([tipo, cfg]) => (
                  <span key={tipo} className={`rounded-full border px-2 py-0.5 ${cfg.badge}`}>
                    {cfg.label}
                  </span>
                ))}
              </div>
              <div className="flex items-center gap-1 text-zinc-400">
                <button
                  type="button"
                  onClick={() => setZoom((z) => Math.max(0.4, Number((z - 0.2).toFixed(2))))}
                  aria-label="Diminuir zoom"
                  className="rounded-md border border-zinc-800 bg-zinc-900 p-1 hover:text-white"
                >
                  <ZoomOut className="h-3.5 w-3.5" />
                </button>
                <span className="w-10 text-center text-[11px]">{Math.round(zoom * 100)}%</span>
                <button
                  type="button"
                  onClick={() => setZoom((z) => Math.min(2.8, Number((z + 0.2).toFixed(2))))}
                  aria-label="Aumentar zoom"
                  className="rounded-md border border-zinc-800 bg-zinc-900 p-1 hover:text-white"
                >
                  <ZoomIn className="h-3.5 w-3.5" />
                </button>
                <button
                  type="button"
                  onClick={resetarCamera}
                  aria-label="Centralizar grafo"
                  className="rounded-md border border-zinc-800 bg-zinc-900 p-1 hover:text-white"
                >
                  <Maximize2 className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>

            <svg
              ref={svgRef}
              viewBox={`0 0 ${LARGURA} ${ALTURA}`}
              onWheel={handleWheel}
              onMouseDown={(e) => {
                if (e.target === svgRef.current) {
                  dragPanRef.current = {
                    startX: e.clientX,
                    startY: e.clientY,
                    origX: pan.x,
                    origY: pan.y,
                  };
                }
              }}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onMouseLeave={handleMouseUp}
              className="w-full h-[420px] rounded-xl bg-[radial-gradient(circle_at_center,_rgba(147,51,234,0.09),_#09090b_75%)] cursor-grab active:cursor-grabbing select-none"
              role="img"
              aria-label="Grafo interativo de correlações estilo Obsidian"
            >
              <g
                transform={`translate(${LARGURA / 2 + pan.x}, ${ALTURA / 2 + pan.y}) scale(${zoom}) translate(${-LARGURA / 2}, ${-ALTURA / 2})`}
              >
                {arestasVisiveis.map((a, idx) => {
                  const p1 = posicoes[a.origem];
                  const p2 = posicoes[a.destino];
                  if (!p1 || !p2) return null;
                  const destacada =
                    !focoAtivoId || a.origem === focoAtivoId || a.destino === focoAtivoId;
                  return (
                    <line
                      key={`${a.origem}-${a.destino}-${idx}`}
                      x1={p1.x}
                      y1={p1.y}
                      x2={p2.x}
                      y2={p2.y}
                      stroke={destacada ? '#a855f7' : '#3f3f46'}
                      strokeOpacity={focoAtivoId ? (destacada ? 0.78 : 0.12) : 0.35}
                      strokeWidth={destacada && focoAtivoId ? 1.8 : 1}
                    />
                  );
                })}

                {nosVisiveis.map((no) => {
                  const pos = posicoes[no.id];
                  if (!pos) return null;
                  const estilo = ESTILOS_NO[no.tipo] ?? {
                    fill: '#71717a',
                    stroke: '#a1a1aa',
                    badge: '',
                    label: no.tipo,
                  };
                  const grau = grauPorNo.get(no.id) ?? 1;
                  const raio = Math.min(18, 7 + Math.sqrt(grau) * 2.2);
                  const selecionado = noSelecionado?.id === no.id;
                  const esmaecido = focoAtivoId !== null && !vizinhosFoco.has(no.id);
                  const mostrarLabel =
                    zoom >= 0.75 || selecionado || hoveredId === no.id || vizinhosFoco.has(no.id);

                  return (
                    <g
                      key={no.id}
                      transform={`translate(${pos.x}, ${pos.y})`}
                      onMouseEnter={() => setHoveredId(no.id)}
                      onMouseLeave={() => setHoveredId(null)}
                      onMouseDown={(e) => {
                        e.stopPropagation();
                        dragNodeRef.current = no.id;
                        animarRef.current();
                      }}
                      onClick={(e) => {
                        e.stopPropagation();
                        setNoSelecionado(no);
                      }}
                      className="cursor-pointer transition-opacity duration-150"
                      opacity={esmaecido ? 0.18 : 1}
                    >
                      <circle
                        r={selecionado ? raio + 3 : raio}
                        fill={estilo.fill}
                        stroke={selecionado || hoveredId === no.id ? '#ffffff' : estilo.stroke}
                        strokeWidth={selecionado ? 2.5 : 1.4}
                      />
                      {mostrarLabel && (
                        <text
                          y={raio + 13}
                          textAnchor="middle"
                          style={{ paintOrder: 'stroke' }}
                          stroke="#09090b"
                          strokeWidth={3}
                          className="fill-zinc-200 text-[10px] font-medium pointer-events-none"
                        >
                          {no.rotulo}
                        </text>
                      )}
                    </g>
                  );
                })}
              </g>
            </svg>
            <p className="text-[11px] text-zinc-500">
              Arraste nós para reorganizar · Scroll para zoom · Arraste o fundo para mover · Clique em um nó para isolar o contexto (1 salto).
            </p>
          </div>

          <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-4">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
              Conexões do Nó
            </h3>
            {!noSelecionado ? (
              <p className="mt-2 text-xs text-zinc-500">
                Passe o mouse para destacar relações ou clique em um nó para isolar o contexto local (1 salto).
              </p>
            ) : (
              <div className="mt-3 space-y-2">
                <p className="text-sm font-semibold text-white">{noSelecionado.rotulo}</p>
                <p className="text-xs text-zinc-400">Tipo: {noSelecionado.tipo}</p>
                {noSelecionado.subtitulo && (
                  <p className="rounded-lg border border-purple-500/30 bg-purple-500/10 px-2.5 py-1 text-xs text-purple-200">
                    {noSelecionado.subtitulo}
                  </p>
                )}
                <ul className="mt-2 max-h-[300px] overflow-y-auto space-y-1.5 pr-1">
                  {conexoesDoNo.map((aresta, idx) => {
                    const outroId =
                      aresta.origem === noSelecionado.id ? aresta.destino : aresta.origem;
                    const outroNo = nosPorId.get(outroId);
                    return (
                      <li
                        key={`${aresta.origem}-${aresta.destino}-${idx}`}
                        className="rounded-lg border border-zinc-800 bg-zinc-950/70 px-2.5 py-1.5 text-xs text-zinc-300"
                      >
                        <span className="font-mono text-purple-300">{aresta.tipo}</span>{' '}
                        {outroNo ? (
                          <button
                            type="button"
                            onClick={() => setNoSelecionado(outroNo)}
                            className="font-medium text-white underline-offset-2 hover:underline"
                          >
                            {outroNo.rotulo}
                          </button>
                        ) : (
                          <span>
                            {aresta.origem} → {aresta.destino}
                          </span>
                        )}
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
