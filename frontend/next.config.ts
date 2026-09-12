import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Necessário para o build de produção multi-stage do Dockerfile (target
  // "production") — gera .next/standalone com um server.js autocontido.
  output: "standalone",
  // Sem isso, o Next 16 bloqueia os chunks de dev quando acessado via
  // 127.0.0.1 (porta canônica local do ADR 015), deixando a página sem JS.
  allowedDevOrigins: ["127.0.0.1", "localhost", "127.0.0.1:3000", "localhost:3000"],
};

export default nextConfig;
