import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Necessário para o build de produção multi-stage do Dockerfile (target
  // "production") — gera .next/standalone com um server.js autocontido.
  output: "standalone",
};

export default nextConfig;
