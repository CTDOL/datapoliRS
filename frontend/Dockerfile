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
