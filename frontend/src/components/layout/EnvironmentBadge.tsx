const LABELS: Record<string, { text: string; className: string }> = {
  DESENVOLVIMENTO: {
    text: "AMBIENTE DE DESENVOLVIMENTO — Sala Vermelha (dados não-produtivos)",
    className: "bg-red-600 text-white",
  },
  HOMOLOGACAO: {
    text: "AMBIENTE DE HOMOLOGAÇÃO — Sandbox de Paridade (dados de teste)",
    className: "bg-yellow-500 text-black font-bold",
  },
};

// NEXT_PUBLIC_ENV_LABEL é assado na imagem em tempo de build (Next.js standalone
// inlina NEXT_PUBLIC_* no bundle do cliente) — ver frontend/Dockerfile e o
// build-arg equivalente no job e2e-parity do ci.yml. Ausente/vazio em produção
// real, então o selo simplesmente não renderiza (ADR universal governanca/047 v2.0.0).
export function EnvironmentBadge() {
  const label = LABELS[process.env.NEXT_PUBLIC_ENV_LABEL ?? ""];
  if (!label) return null;

  return (
    <div
      role="status"
      className={`w-full py-1 text-center text-xs font-semibold tracking-wide shadow-md ${label.className}`}
    >
      {label.text}
    </div>
  );
}
