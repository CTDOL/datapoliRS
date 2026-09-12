import { defineConfig, devices } from '@playwright/test';

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
    baseURL: 'http://127.0.0.1:3000',
    trace: 'on-first-retry',
  },
  webServer: {
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
