"use client";

import { useEffect, useState } from "react";

const LABELS: Record<string, { text: string; className: string }> = {
  DESENVOLVIMENTO: {
    text: "AMBIENTE DE DESENVOLVIMENTO — Sala Vermelha (dados não-produtivos)",
    className: "bg-red-600 text-on-accent",
  },
  HOMOLOGACAO: {
    text: "AMBIENTE DE HOMOLOGAÇÃO — Sandbox de Paridade (dados de teste)",
    className: "bg-yellow-500 text-black font-bold",
  },
};

// Arquivo gerado por scripts/ambiente_status.sh (só dev e hml, fora do Git).
const STATUS_URL = "/ambiente-status.json";
const INTERVALO_MS = 30000;

type AmbienteStatus = { geradoEm: string; containers: { nome: string; status: string }[] };

// NEXT_PUBLIC_ENV_LABEL é assado na imagem em tempo de build (Next.js standalone
// inlina NEXT_PUBLIC_* no bundle do cliente) — ver frontend/Dockerfile. Ausente/vazio
// em produção real, então o selo simplesmente não renderiza (ADR universal governanca/047 v2.0.0).
export function EnvironmentBadge() {
  const label = LABELS[process.env.NEXT_PUBLIC_ENV_LABEL ?? ""];
  const [containers, setContainers] = useState<string[] | null>(null);

  useEffect(() => {
    if (!label) return;
    let cancelado = false;

    const carregar = async () => {
      try {
        const resposta = await fetch(STATUS_URL, { cache: "no-store" });
        if (!resposta.ok) return;
        const dados: AmbienteStatus = await resposta.json();
        if (!cancelado) setContainers(dados.containers.map((c) => c.nome));
      } catch {
        // Sem o arquivo de status, a barra mostra só o ambiente e o banco.
      }
    };

    carregar();
    const id = setInterval(carregar, INTERVALO_MS);
    return () => {
      cancelado = true;
      clearInterval(id);
    };
  }, [label]);

  if (!label) return null;

  // NEXT_PUBLIC_DB_LABEL vem do compose (nome do banco que a API usa). Sem ele, só o ambiente aparece.
  const banco = process.env.NEXT_PUBLIC_DB_LABEL;

  return (
    <div
      role="status"
      className={`w-full py-1 text-center text-xs font-semibold tracking-wide shadow-md ${label.className}`}
    >
      <div>{banco ? `${label.text} · banco: ${banco}` : label.text}</div>
      {containers && (
        <div className="text-[10px] font-normal opacity-90">
          Containers ativos ({containers.length}): {containers.join(", ")}
        </div>
      )}
    </div>
  );
}
