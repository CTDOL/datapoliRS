import { defineConfig, devices } from '@playwright/test';

// PLAYWRIGHT_BASE_URL, quando definida, aponta para uma stack já no ar por fora
// (job e2e-parity do CI: docker-compose.prod.yml + Nginx efêmero) — nesse caso não
// há webServer próprio para subir, os testes só apontam para o proxy já rodando.
const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? 'http://127.0.0.1:3000';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  retries: process.env.CI ? 1 : 0,
  reporter: 'list',
  use: {
    // 127.0.0.1, não localhost: o cookie de sessão HttpOnly é SameSite=Lax
    // e o backend roda em 127.0.0.1:8000 — "localhost" e "127.0.0.1" são
    // sites distintos para o navegador, então o cookie do login nunca é
    // persistido/enviado se o front for acessado por um host diferente do
    // backend. Ver ADR de confinamento em 127.0.0.1 no CLAUDE.md.
    baseURL,
    trace: 'on-first-retry',
  },
  webServer: process.env.PLAYWRIGHT_BASE_URL
    ? undefined
    : {
        command: 'npm run dev',
        url: 'http://127.0.0.1:3000',
        reuseExistingServer: !process.env.CI,
        timeout: 120_000,
      },
  projects: [
    {
      name: 'setup',
      testMatch: /global\.setup\.ts/,
    },
    {
      name: 'chromium',
      testMatch: /auth\.spec\.ts/,
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'chromium-autenticado',
      testMatch: /(dashboard|modulos|settings)\.spec\.ts/,
      use: { ...devices['Desktop Chrome'], storageState: 'e2e/.auth/user.json' },
      dependencies: ['setup'],
    },
  ],
});
