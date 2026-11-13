import { ShieldCheck } from 'lucide-react';
import { PortalPublicoForm } from '@/features/balcao/components/PortalPublicoForm';

export default async function PortalPublicoPage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = await params;

  return (
    <main className="flex min-h-screen w-full items-center justify-center bg-zinc-950 px-4 py-10">
      <section className="w-full max-w-xl rounded-2xl border border-zinc-800 bg-zinc-900/80 p-6 shadow-2xl sm:p-8">
        <div className="mb-6 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-purple-500/30 bg-purple-500/10">
            <ShieldCheck className="h-5 w-5 text-purple-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Balcão de Atendimento</h1>
            <p className="text-xs text-zinc-400">Canal direto para envio de demandas ao gabinete</p>
          </div>
        </div>

        <PortalPublicoForm token={token} />
      </section>
    </main>
  );
}

