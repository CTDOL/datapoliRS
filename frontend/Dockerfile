FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json ./
# npm ci falha em Linux: o lockfile não resolve a dependência opcional
# @img/sharp-wasm32 -> @emnapi/runtime para esta plataforma (gerado no macOS).
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
