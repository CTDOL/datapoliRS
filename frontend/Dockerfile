# syntax=docker/dockerfile:1

# ---- deps: instala dependências uma única vez, cacheável entre os dois alvos ----
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
# O lockfile foi regenerado em ambiente Linux (validado no CI) — npm ci é
# determinístico e mais rápido que npm install para instalação limpa.
RUN npm ci

# ---- dev: alvo padrão (última stage) — usado pelo docker-compose local ----
FROM deps AS dev
WORKDIR /app
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]

# ---- builder: compila o build de produção (não usado localmente) ----
FROM deps AS builder
WORKDIR /app
# Selo visual de ambiente (ADR universal governanca/047): NEXT_PUBLIC_* é
# inlinado no bundle do cliente durante "next build" — precisa existir ANTES
# do build, não em runtime. Vazio por padrão (produção real não mostra selo);
# o job e2e-parity do ci.yml passa --build-arg NEXT_PUBLIC_ENV_LABEL=HOMOLOGACAO.
ARG NEXT_PUBLIC_ENV_LABEL=""
ENV NEXT_PUBLIC_ENV_LABEL=${NEXT_PUBLIC_ENV_LABEL}
COPY . .
RUN npx next typegen && npm run build

# ---- production: imagem final publicada no registro — apenas o output standalone ----
FROM node:22-alpine AS production
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup -S nodejs && adduser -S nextjs -G nodejs
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
USER nextjs
EXPOSE 3000
ENV PORT=3000
CMD ["node", "server.js"]
