import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Necessário para o build de produção multi-stage do Dockerfile (target
  // "production") — gera .next/standalone com um server.js autocontido.
  output: "standalone",
  // Sem isso, o Next 16 bloqueia os chunks de dev quando acessado via
  // 127.0.0.1 (porta canônica local do ADR 015), deixando a página sem JS.
  allowedDevOrigins: ["127.0.0.1", "localhost", "127.0.0.1:3000", "localhost:3000"],
  // Proxy same-origin para a API em dev/local: o navegador trata "localhost"
  // e "127.0.0.1" como hosts distintos, então o cookie HttpOnly do login
  // emitido por um deles nunca é enviado de volta se a página foi acessada
  // pelo outro (login "funciona" no POST mas o usuário não sai da tela de
  // login). Passando pelo próprio servidor Next.js, a requisição do
  // navegador é sempre same-origin com a página — o host usado na barra de
  // endereço deixa de importar. Só se aplica quando NEXT_PUBLIC_API_URL
  // (usado como baseURL absoluta em src/services/api.ts) não está setado.
  async rewrites() {
    const apiInternalUrl = process.env.API_INTERNAL_URL || "http://127.0.0.1:8000";
    return [
      { source: "/api/:path*", destination: `${apiInternalUrl}/api/:path*` },
    ];
  },
};

export default nextConfig;
