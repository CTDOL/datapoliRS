import { test, expect } from '@playwright/test';

test('a tela de login carrega e exibe o formulário', async ({ page }) => {
  await page.goto('/login');
  await expect(page.getByRole('heading', { name: 'DATAPOLIRS' })).toBeVisible();
  await expect(page.locator('input[type="email"]')).toBeVisible();
  await expect(page.locator('input[type="password"]')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Acessar Painel Isolado' })).toBeVisible();
});

test('rotas protegidas redirecionam para /login sem sessão', async ({ page }) => {
  for (const rota of ['/', '/liderancas', '/emendas', '/projetos-lei']) {
    await page.goto(rota);
    await expect(page).toHaveURL(/\/login$/);
  }
});
