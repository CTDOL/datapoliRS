import { test, expect } from '@playwright/test';

test.describe('Mapa Tático (dashboard autenticado)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('acessa / com sessão autenticada e exibe o título do mapa tático', async ({ page }) => {
    await expect(page).toHaveURL('/');
    await expect(page.getByRole('heading', { name: 'Mapa Tático' })).toBeVisible();
  });

  test('carrega o container do mapa Leaflet', async ({ page }) => {
    await expect(page.locator('.leaflet-container')).toBeVisible({ timeout: 15000 });
  });

  test('controles de modo de visualização (lideranças/votação/visão cruzada) alternam a busca de candidato', async ({ page }) => {
    const buscaPlaceholder = 'Buscar candidato para ver a votação no mapa...';

    // No modo padrão (Lideranças) a busca de candidato não é exibida.
    await expect(page.getByPlaceholder(buscaPlaceholder)).not.toBeVisible();

    await page.getByRole('button', { name: 'Votação' }).click();
    await expect(page.getByPlaceholder(buscaPlaceholder)).toBeVisible();

    await page.getByRole('button', { name: 'Visão Cruzada' }).click();
    await expect(page.getByPlaceholder(buscaPlaceholder)).toBeVisible();

    await page.getByRole('button', { name: 'Lideranças' }).click();
    await expect(page.getByPlaceholder(buscaPlaceholder)).not.toBeVisible();
  });

  test('sidebar de navegação expõe todos os módulos do gabinete', async ({ page }) => {
    await expect(page.getByRole('link', { name: 'Mapa Tático' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Lideranças' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Projetos de Lei' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Emendas' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Configurações' })).toBeVisible();
  });
});
