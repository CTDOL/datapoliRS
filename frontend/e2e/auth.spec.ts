import { test, expect } from '@playwright/test';

test('a tela de login carrega e exibe o formulário', async ({ page }) => {
  await page.goto('/login');
  await expect(page.getByRole('heading', { name: 'DATAPOLIRS' })).toBeVisible();
  await expect(page.locator('input[type="email"]')).toBeVisible();
  await expect(page.locator('input[type="password"]')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Acessar Painel Isolado' })).toBeVisible();
});

test('rotas protegidas redirecionam para /login sem sessão', async ({ page }) => {
  for (const rota of ['/', '/liderancas', '/emendas', '/projetos-lei', '/settings']) {
    await page.goto(rota);
    await expect(page).toHaveURL(/\/login$/);
  }
});

test('login com credenciais inválidas exibe feedback de erro', async ({ page }) => {
  await page.goto('/login');
  await page.locator('input[type="email"]').fill('invasor@invalido.com.br');
  await page.locator('input[type="password"]').fill('senha-incorreta');
  await page.getByRole('button', { name: 'Acessar Painel Isolado' }).click();

  await expect(
    page.getByText('Credenciais inválidas ou acesso negado. Verifique os dados.')
  ).toBeVisible();
  await expect(page).toHaveURL(/\/login$/);
});

test('login com sucesso seta o cookie HttpOnly e redireciona para /', async ({ page, context }) => {
  await page.goto('/login');
  await page.locator('input[type="email"]').fill('operador@campanha.com.br');
  await page.locator('input[type="password"]').fill('admin123');
  await page.getByRole('button', { name: 'Acessar Painel Isolado' }).click();

  await expect(page).toHaveURL('/');

  const cookies = await context.cookies();
  const sessionCookie = cookies.find((c) => c.name === 'token');
  expect(sessionCookie).toBeDefined();
  expect(sessionCookie?.httpOnly).toBe(true);
  expect(sessionCookie?.sameSite).toBe('Lax');
});
