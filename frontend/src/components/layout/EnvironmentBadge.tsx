const LABELS: Record<string, { text: string; className: string }> = {
  DESENVOLVIMENTO: {
    text: "AMBIENTE DE DESENVOLVIMENTO — dados fictícios, não é produção",
    className: "bg-amber-500 text-amber-950",
  },
  HOMOLOGACAO: {
    text: "AMBIENTE DE HOMOLOGAÇÃO — dados de teste, não é produção",
    className: "bg-blue-600 text-blue-50",
  },
};

// NEXT_PUBLIC_ENV_LABEL é assado na imagem em tempo de build (Next.js standalone
// inlina NEXT_PUBLIC_* no bundle do cliente) — ver frontend/Dockerfile e o
// build-arg equivalente no job e2e-parity do ci.yml. Ausente/vazio em produção
// real, então o selo simplesmente não renderiza (ADR universal governanca/047).
export function EnvironmentBadge() {
  const label = LABELS[process.env.NEXT_PUBLIC_ENV_LABEL ?? ""];
  if (!label) return null;

  return (
    <div
      role="status"
      className={`w-full py-1 text-center text-xs font-semibold tracking-wide ${label.className}`}
    >
      {label.text}
    </div>
  );
}
