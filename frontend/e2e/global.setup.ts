import { test as setup, expect } from '@playwright/test';

const authFile = 'e2e/.auth/user.json';

setup('autentica como operador e persiste o estado de sessão', async ({ page }) => {
  await page.goto('/login');
  await page.locator('input[type="email"]').fill('operador@campanha.com.br');
  await page.locator('input[type="password"]').fill('admin123');
  await page.getByRole('button', { name: 'Acessar Painel Isolado' }).click();

  await expect(page).toHaveURL('/');
  await page.context().storageState({ path: authFile });
});
